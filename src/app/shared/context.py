from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.requests import Request

_current_request: ContextVar[Request | None] = ContextVar(
    "current_request",
    default=None,
)


def set_current_request(request: Request | None) -> None:
    """현재 요청을 컨텍스트에 저장한다(미들웨어에서 호출)."""
    _current_request.set(request)


def get_current_request() -> Request | None:
    """현재 요청을 반환한다. 요청 컨텍스트 밖이면 None."""
    return _current_request.get()
