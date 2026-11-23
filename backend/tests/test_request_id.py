import json


def test_request_id_consistent_and_client_header_ignored(client, stdout_logs):
    r = client.get("/api/v1/health/live", headers={"X-Request-ID": "client-forged"})
    rid = r.headers["X-Request-ID"]
    assert rid != "client-forged"
    assert r.json()["request_id"] == rid
    lines = [json.loads(x) for x in stdout_logs.readouterr().out.splitlines() if x.strip()]
    rec = [x for x in lines if x.get("request_id") == rid]
    assert len(rec) == 1
    for k in ("timestamp", "level", "service", "method", "path", "status_code", "duration_ms"):
        assert k in rec[0]
    assert rec[0]["path"] == "/api/v1/health/live" and rec[0]["status_code"] == 200


def test_ids_differ_per_request(client):
    a = client.get("/api/v1/health/live").headers["X-Request-ID"]
    b = client.get("/api/v1/health/live").headers["X-Request-ID"]
    assert a != b
