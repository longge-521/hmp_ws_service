import json
import logging
from fastapi import Request, Response
from fastapi.routing import APIRoute
from app.application.audit_log.audit_log_app_service import AuditLogAppService

logger = logging.getLogger("hmp_ws_service")

class AuditLogRoute(APIRoute):
    """
    自定义 APIRoute，用于拦截标记了 summary（审计动作名）和 description（资源类型）的 HTTP 路由，
    并自动且异步记录审计日志。
    """
    def get_route_handler(self):
        original_route_handler = super().get_route_handler()
        
        async def custom_route_handler(request: Request) -> Response:
            action = self.summary
            resource_type = self.description
            
            # 仅拦截我们需要审计的动作范围，其他路由直接放行
            auditable_actions = {"SEND_MESSAGE", "READ_MESSAGE", "READ_ALL_MESSAGES", "DELETE_FILE"}
            if not action or action not in auditable_actions:
                return await original_route_handler(request)
            
            operator = None
            resource_id = None
            
            # 1. 尝试从 URL 路径参数自动提取资源 ID
            if "message_id" in request.path_params:
                resource_id = str(request.path_params["message_id"])
            elif "file_id" in request.path_params:
                resource_id = str(request.path_params["file_id"])
                
            # 2. 尝试从 Query 提取 operator 
            if action == "READ_ALL_MESSAGES":
                operator = request.query_params.get("receiver")
                
            # 3. 发送站内信时，安全备份 Request Body 提取发送者作为操作者
            if action == "SEND_MESSAGE" and request.method == "POST":
                try:
                    body_bytes = await request.body()
                    async def receive():
                        return {"type": "http.request", "body": body_bytes, "more_body": False}
                    request._receive = receive
                    
                    req_json = json.loads(body_bytes.decode("utf-8"))
                    operator = req_json.get("sender")
                except Exception as e:
                    logger.warning(f"AuditLogRoute failed to parse request body: {e}")
                    
            # 4. 执行业务逻辑
            try:
                response = await original_route_handler(request)
                
                status = "success"
                details = None
                if response.status_code >= 400:
                    status = "failed"
                    details = f"HTTP status code: {response.status_code}"
                    
                # 5. 对于 SEND_MESSAGE 成功逻辑，安全拉取 response 里的 ID
                if status == "success" and action == "SEND_MESSAGE":
                    try:
                        response_body = b""
                        if hasattr(response, "body_iterator"):
                            async for chunk in response.body_iterator:
                                response_body += chunk
                            
                            # 必须重构 Response 以防原响应流被耗尽失效
                            response = Response(
                                content=response_body,
                                status_code=response.status_code,
                                headers=dict(response.headers),
                                media_type=response.media_type
                            )
                        else:
                            # 静态 Response 或 JSONResponse 直接读取 body
                            response_body = response.body
                        
                        res_json = json.loads(response_body.decode("utf-8"))
                        if res_json.get("status") == "success" or "id" in res_json:
                            resource_id = str(res_json.get("id"))
                    except Exception as e:
                        logger.warning(f"AuditLogRoute failed to parse response body: {e}")
                        
                # 异步入库审计日志
                audit_service = AuditLogAppService()
                await audit_service.record_log(
                    request=request,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    status=status,
                    details=details,
                    operator=operator or "system"
                )
                
                return response
                
            except Exception as e:
                # 拦截业务抛出的未知运行时异常并记为失败
                logger.error(f"AuditLogRoute captured endpoint execution error: {e}")
                
                # 提取 HTTPException detail
                err_details = str(e)
                if hasattr(e, "detail"):
                    err_details = getattr(e, "detail")
                    
                audit_service = AuditLogAppService()
                await audit_service.record_log(
                    request=request,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    status="failed",
                    details=err_details,
                    operator=operator or "system"
                )
                raise e
                
        return custom_route_handler
