from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from src.app.shared.config import get_settings
from src.app.shared.context import set_current_request

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from fastapi import FastAPI
    from starlette.requests import Request
    from starlette.responses import Response


class RequestContextMiddleware(BaseHTTPMiddleware):
    """요청 객체를 contextvar에 저장해 하위 로직에서 접근 가능하게 한다."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        set_current_request(request)
        try:
            return await call_next(request)
        finally:
            set_current_request(None)


def setup_middleware(app: FastAPI) -> None:
    """앱에 공용 미들웨어(요청 컨텍스트, CORS)를 등록한다."""
    settings = get_settings()

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
