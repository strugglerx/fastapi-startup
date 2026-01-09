"""
Hello World 接口测试
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_hello_world():
    """测试 Hello World 接口"""
    response = client.get("/api/v1/hello")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "data" in data
    assert data["data"]["message"] == "Hello, base scaffold!"


def test_ping():
    """测试 Ping 健康检查接口"""
    response = client.get("/api/v1/ping")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["status"] == "ok"


def test_docs_endpoint():
    """测试文档接口可访问"""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_openapi_json():
    """测试 OpenAPI JSON 接口"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "paths" in data
    assert "/api/v1/hello" in data["paths"]
    assert "/api/v1/ping" in data["paths"]
