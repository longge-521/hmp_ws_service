import pytest
from unittest.mock import MagicMock, patch, ANY
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.testclient import TestClient
from app.infrastructure.audit_route import AuditLogRoute

def test_audit_route_success_and_failure():
    app_test = FastAPI()
    router = APIRouter(route_class=AuditLogRoute)
    
    @router.post("/test-send", summary="SEND_MESSAGE", description="site_message")
    async def mock_send(payload: dict):
        return {"status": "success", "id": 999}
        
    @router.post("/test-fail", summary="READ_MESSAGE", description="site_message")
    async def mock_fail():
        raise HTTPException(status_code=400, detail="Mock bad request")
        
    app_test.include_router(router)
    
    # Mock record_log 避免数据库依赖
    with patch("app.application.audit_log.audit_log_app_service.AuditLogAppService.record_log") as mock_record:
        client = TestClient(app_test)
        
        # 1. 测试成功调用时的拦截与 ID 提取
        response_ok = client.post("/test-send", json={"sender": "user_123", "content": "hello"})
        assert response_ok.status_code == 200
        assert response_ok.json()["id"] == 999
        
        mock_record.assert_any_call(
            request=ANY,
            action="SEND_MESSAGE",
            resource_type="site_message",
            resource_id="999",
            status="success",
            details=None,
            operator="user_123"
        )
        
        # 2. 测试抛出 HTTPException 时的失败日志拦截
        response_err = client.post("/test-fail")
        assert response_err.status_code == 400
        
        mock_record.assert_any_call(
            request=ANY,
            action="READ_MESSAGE",
            resource_type="site_message",
            resource_id=None,
            status="failed",
            details="Mock bad request",
            operator="system"
        )
