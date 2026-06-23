from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.infrastructure import auth

def test_verify_token_no_token_env(monkeypatch):
    # 测试未配置 API_TOKEN 环境变量的情况（允许无条件通过）
    monkeypatch.setattr(auth, "API_TOKEN", "")
    
    app = FastAPI()
    
    from fastapi import Depends
    @app.get("/test")
    def test_route(valid: bool = Depends(auth.verify_token)):
        return {"status": "ok"}
        
    client = TestClient(app)
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_verify_token_with_token_env(monkeypatch):
    # 测试配置了 API_TOKEN 环境变量的情况
    monkeypatch.setattr(auth, "API_TOKEN", "secure-secret-token")
    
    app = FastAPI()
    
    from fastapi import Depends
    @app.get("/test")
    def test_route(valid: bool = Depends(auth.verify_token)):
        return {"status": "ok"}
        
    client = TestClient(app)
    
    # 1. 不传 Token -> 401
    response = client.get("/test")
    assert response.status_code == 401
    
    # 2. 传错误的 Token -> 401
    response = client.get("/test", headers={"Authorization": "wrong-token"})
    assert response.status_code == 401
    
    # 3. 传正确的 Header Bearer Token -> 200
    response = client.get("/test", headers={"Authorization": "Bearer secure-secret-token"})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    
    # 4. 传正确的 Query Token -> 200
    response = client.get("/test?token=secure-secret-token")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_verify_ws_token(monkeypatch):
    monkeypatch.setattr(auth, "API_TOKEN", "ws-secret-token")
    
    # 正确
    assert auth.verify_ws_token({"token": "ws-secret-token"}) is True
    # 错误
    assert auth.verify_ws_token({"token": "wrong-token"}) is False
    # 缺失
    assert auth.verify_ws_token({}) is False
    
    # 无 API_TOKEN 限制
    monkeypatch.setattr(auth, "API_TOKEN", "")
    assert auth.verify_ws_token({"token": "whatever"}) is True
    assert auth.verify_ws_token({}) is True
