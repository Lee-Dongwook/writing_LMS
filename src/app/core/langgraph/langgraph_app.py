from __future__ import annotations

import os
from typing import TYPE_CHECKING

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

from src.app.shared import init as shared_init
from src.app.shared.context import set_current_request

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request
    from starlette.responses import Response


_shared_initialized = False


def _initialize_shared_once() -> None:
    """LangGraph API 워커에서 공용 런타임 상태를 1회 초기화한다."""
    global _shared_initialized
    if _shared_initialized:
        return

    shared_init.initialize()
    _shared_initialized = True


env_type = os.getenv("ENV", "development")
shared_init.load_dotenv(env_type)
_initialize_shared_once()

app = FastAPI()


class RequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        set_current_request(request)
        return await call_next(request)


app.add_middleware(RequestMiddleware)
