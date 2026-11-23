from fastapi import FastAPI

from app.main import create_app
from fastapi.testclient import TestClient


def make_client():
    app = create_app()

    @app.get("/boom")
    def boom():
        raise RuntimeError("secret-detail-xyz")

    @app.get("/needs-int")
    def needs_int(n: int):
        return {}

    return TestClient(app, raise_server_exceptions=False)


def check(r, status, code):
    assert r.status_code == status
    b = r.json()
    assert set(b) == {"code", "message", "data", "request_id"}
    assert b["code"] == code
    assert b["request_id"] == r.headers["X-Request-ID"]
    assert "Traceback" not in r.text and "secret-detail-xyz" not in r.text


def test_404(client):
    check(client.get("/api/v1/nope"), 404, "NOT_FOUND")


def test_422():
    check(make_client().get("/needs-int?n=abc"), 422, "VALIDATION_ERROR")


def test_500():
    check(make_client().get("/boom"), 500, "INTERNAL_ERROR")
