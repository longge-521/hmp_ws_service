import os
import logging
from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader, APIKeyQuery

logger = logging.getLogger("hmp_ws_service")

# 从环境变量中获取安全令牌，默认可为空以维持开发兼容性
API_TOKEN = os.getenv("API_TOKEN", "")

# 声明凭证获取策略
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)
api_key_query = APIKeyQuery(name="token", auto_error=False)

def verify_token(
    request: Request, 
    authorization: str = Security(api_key_header), 
    token: str = Security(api_key_query)
) -> bool:
    """
    HTTP 路由依赖注入验证方法。
    若环境变量未配置 API_TOKEN，则不进行拦截（以兼容开发与本地调试环境）。
    如果配置了，客户端必须提供匹配的 Bearer Token 或 Query Token 参数。
    """
    if not API_TOKEN:
        return True
        
    extracted_token = None
    if authorization:
        if authorization.lower().startswith("bearer "):
            extracted_token = authorization[7:]
        else:
            extracted_token = authorization
            
    if not extracted_token and token:
        extracted_token = token
        
    if not extracted_token or extracted_token != API_TOKEN:
        logger.warning("Unauthenticated HTTP access request rejected.")
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Invalid or missing API_TOKEN"
        )
    return True

def verify_ws_token(query_params) -> bool:
    """
    WebSocket 连接校验辅助方法。
    """
    if not API_TOKEN:
        return True
    
    token = query_params.get("token")
    return token == API_TOKEN
