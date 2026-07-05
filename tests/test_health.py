"""헬스체크 엔드포인트."""

from __future__ import annotations


def test_health_ok(app_client):
    resp = app_client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "env" in body
