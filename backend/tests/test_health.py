from app.main import create_app
from fastapi.testclient import TestClient


def test_live(client):
    r = client.get("/api/v1/health/live")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == "OK" and body["data"] == {"status": "alive"}


def test_ready_up(client):
    r = client.get("/api/v1/health/ready")
    assert r.status_code == 200
    assert r.json()["data"] == {"status": "ready", "database": "up"}


def test_ready_down(db_down):
    with TestClient(create_app(), raise_server_exceptions=False) as c:
        r = c.get("/api/v1/health/ready")
    assert r.status_code == 503
    body = r.json()
    assert body["code"] == "DEPENDENCY_UNAVAILABLE"
    assert body["data"] == {"status": "not_ready", "database": "down"}
    assert "127.0.0.1" not in r.text and "Traceback" not in r.text


def test_app_starts_and_live_ok_when_db_down(db_down):
    with TestClient(create_app()) as c:
        assert c.get("/api/v1/health/live").status_code == 200
