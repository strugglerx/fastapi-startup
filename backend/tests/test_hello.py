def test_hello_world(client):
    r = client.get("/api/v1/hello")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["message"] == "Hello, base scaffold!"


def test_ping(client):
    r = client.get("/api/v1/ping")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["status"] == "ok"


def test_docs(client):
    r = client.get("/docs")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_openapi(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    data = r.json()
    assert "openapi" in data
    assert "/api/v1/hello" in data["paths"]
    assert "/api/v1/ping" in data["paths"]
