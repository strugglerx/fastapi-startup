"""错误处理 / 状态码 / 响应包装的测试"""


def test_404_returns_real_status(client):
    """不存在的路由应返回真实 404，并带统一 code/msg 结构"""
    r = client.get("/api/v1/does-not-exist")
    assert r.status_code == 404
    body = r.json()
    assert body["code"] == 404
    assert "接口不存在" in body["msg"]


def test_405_method_not_allowed(client):
    """GET 路由用 POST 调用 → 405"""
    r = client.post("/api/v1/ping")
    assert r.status_code == 405
    body = r.json()
    assert body["code"] == 405


def test_response_wrapper_does_not_double_wrap(client):
    """已经是 {code, data} 结构的响应不应被重复包装"""
    r = client.get("/api/v1/ping")
    body = r.json()
    # 顶层 code/data 各一份，没有嵌套
    assert "code" in body
    assert "data" in body
    assert "code" not in body["data"]


def test_health_endpoint_is_public(client):
    """健康检查不需要鉴权（负载均衡器探活）"""
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["status"] == "ok"
