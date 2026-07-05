"""writing 라우터: 인증 보호 + 스레드 사용자 귀속."""

from __future__ import annotations

import pytest

import src.app.writing.router as writing_router

# (method, path, kwargs) — 토큰 없이 호출하면 전부 401 이어야 한다.
_PROTECTED = [
    ("post", "/writing/analyze", {"json": {"passage": "테스트 지문"}}),
    ("post", "/writing/chat", {"json": {"message": "안녕"}}),
    ("post", "/writing/chat/stream", {"json": {"message": "안녕"}}),
    ("post", "/writing/chat/resume", {"json": {"thread_uuid": "t", "decision": "승인"}}),
    ("post", "/writing/chat/resume/stream", {"json": {"thread_uuid": "t", "decision": "승인"}}),
]


@pytest.mark.parametrize(("method", "path", "kwargs"), _PROTECTED)
def test_protected_endpoints_require_auth(app_client, method, path, kwargs):
    resp = getattr(app_client, method)(path, **kwargs)
    assert resp.status_code == 401


def test_chat_thread_is_namespaced_per_user(authed, monkeypatch):
    """같은 client_thread라도 사용자별로 다른 내부 스레드에 매핑된다."""
    client, state = authed

    async def _fake_send(thread_id, message, graph=None):
        # 내부 thread_id를 그대로 reply로 돌려줘 네임스페이스를 관찰
        return {
            "thread_id": thread_id,
            "status": "completed",
            "reply": thread_id,
            "analysis": None,
        }

    monkeypatch.setattr(writing_router, "send_message", _fake_send)

    state["uuid"] = "user-aaa"
    resp_a = client.post("/writing/chat", json={"message": "hi", "thread_uuid": "abc"}).json()
    state["uuid"] = "user-bbb"
    resp_b = client.post("/writing/chat", json={"message": "hi", "thread_uuid": "abc"}).json()

    # 외부로 노출되는 thread_uuid는 client 값 그대로(uuid 미노출)
    assert resp_a["thread_uuid"] == "abc"
    assert resp_b["thread_uuid"] == "abc"
    # 내부 스레드는 사용자별로 격리
    assert resp_a["reply"] == "user-aaa:abc"
    assert resp_b["reply"] == "user-bbb:abc"
    assert resp_a["reply"] != resp_b["reply"]


def test_chat_generates_thread_when_absent(authed, monkeypatch):
    """thread_uuid 미제공 시 신규 스레드가 생성되어 응답에 실린다."""
    client, state = authed
    state["uuid"] = "user-ccc"

    async def _fake_send(thread_id, message, graph=None):
        return {"thread_id": thread_id, "status": "completed", "reply": "ok", "analysis": None}

    monkeypatch.setattr(writing_router, "send_message", _fake_send)

    body = client.post("/writing/chat", json={"message": "hi"}).json()
    assert body["thread_uuid"]  # 신규 uuid 발급
    assert body["status"] == "completed"
