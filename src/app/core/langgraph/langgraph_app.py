from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


_shared_initialized = False

def _initialize_shared_once() -> None:
    """Initialize shared runtime state once for LangGraph API workers."""
    global _shared_initialized
    if _shared_initialized:
        return

    shared_init.initialize()
    _shared_initialized = True


env_type = os.getenv("ENV", "development")
shared_init.load_dotenv(env_type)

app = FastAPI()

class RequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        set_current_request(request)
        return await call_next(request)


app.add_middleware(RequestMiddleware)
