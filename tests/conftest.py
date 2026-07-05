"""공용 테스트 픽스처.

DB/LLM 없이 도는 것을 원칙으로 한다. 인증은 `verify_token` 의존성을 오버라이드해
가짜 사용자를 주입하고, 에이전트/분석은 테스트별로 monkeypatch한다. TestClient를
context manager로 쓰면 lifespan(memory 체크포인터 분기)까지 함께 검증된다.
"""

from __future__ import annotations

import os

# 테스트는 항상 인메모리 체크포인터로 동작한다(외부 Postgres 불필요).
# .env/셸에 AGENT_CHECKPOINTER=postgres가 있어도 여기서 강제로 덮는다.
os.environ["AGENT_CHECKPOINTER"] = "memory"
os.environ.setdefault("ENV", "development")

from collections.abc import Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from src.app.auth.dependencies import verify_token  # noqa: E402
from src.app.shared.database import get_async_db  # noqa: E402
from src.app.user.schema import UserRead  # noqa: E402


def _no_db() -> None:
    # DB 세션 의존성 무력화 — 테스트 경로는 실제 DB에 접속하지 않는다.
    return None


def _fake_user(uuid: str = "user-test-1", *, is_admin: bool = False) -> UserRead:
    return UserRead(
        uuid=uuid,
        email="tester@test.local",
        name="테스터",
        is_active=True,
        is_admin=is_admin,
    )


@pytest.fixture
def app_client() -> Iterator[TestClient]:
    """인증 오버라이드 없는 클라이언트(401 검증용)."""
    main.app.dependency_overrides[get_async_db] = _no_db
    try:
        with TestClient(main.app) as client:
            yield client
    finally:
        main.app.dependency_overrides.clear()


@pytest.fixture
def authed() -> Iterator[tuple[TestClient, dict[str, str]]]:
    """인증된 클라이언트 + 사용자 uuid를 바꿀 수 있는 state.

    `state["uuid"]`를 요청 사이에 바꾸면 다른 사용자로 위장할 수 있다(스레드 격리 검증).
    """
    state = {"uuid": "user-test-1"}

    def _override() -> UserRead:
        return _fake_user(state["uuid"])

    main.app.dependency_overrides[verify_token] = _override
    main.app.dependency_overrides[get_async_db] = _no_db
    try:
        with TestClient(main.app) as client:
            yield client, state
    finally:
        main.app.dependency_overrides.clear()
