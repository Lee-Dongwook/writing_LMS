import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
import yaml
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from scalar_fastapi import get_scalar_api_reference

from src.app import models  # noqa: F401  # 모델 매퍼 레지스트리 등록
from src.app.auth.router import router as auth_router
from src.app.doc.api import router as doc_router
from src.app.llm.router import router as llm_router
from src.app.shared import init as shared_init
from src.app.shared.config import get_settings
from src.app.shared.database import checkpointer_pool
from src.app.shared.exceptions import global_exception_handler
from src.app.shared.logging import setup_logging
from src.app.shared.middleware import setup_middleware
from src.app.writing.agent import build_writing_agent, set_active_agent
from src.app.writing.router import router as writing_router

env_type = os.getenv("ENV", "development")
shared_init.load_dotenv(env_type)

setup_logging()

os.environ["TOKENIZERS_PARALLELISM"] = "false"

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """앱 수명 주기: AGENT_CHECKPOINTER=postgres면 풀 기반 체크포인터를 배선한다.

    Postgres면 lifespan 동안 커넥션 풀을 유지하며 그걸로 컴파일한 대화 에이전트를
    런타임에 주입(재시작해도 스레드 유지). memory면 기존 인메모리로 동작한다.
    """
    settings = get_settings()
    if settings.agent_checkpointer == "postgres":
        logger.info("Postgres 체크포인터로 대화 에이전트 배선")
        async with checkpointer_pool() as saver:
            set_active_agent(build_writing_agent(checkpointer=saver))
            try:
                yield
            finally:
                set_active_agent(None)
    else:
        yield


app = FastAPI(
    title="Writing LMS API",
    description="Writing LMS API",
    version="0.1.0",
    lifespan=lifespan,
    swagger_ui_init_oauth={
        "appName": "Writing LMS",
        "usePkceWithAuthorizationCodeGrant": True,
        "scopes": "openid email profile",
    },
)

setup_middleware(app)

app.include_router(auth_router)
app.include_router(writing_router)
app.include_router(llm_router)
app.include_router(doc_router)


@app.get("/health", tags=["health"], summary="라이브니스 체크")
async def health() -> dict[str, str]:
    """앱 생존 확인(무의존성). 인프라/프론트의 헬스체크용."""
    settings = get_settings()
    return {"status": "ok", "app": settings.app_name, "env": settings.env}


@app.get("/openapi.yaml", include_in_schema=False)
def get_openapi_yaml() -> Response:
    openapi_schema = app.openapi()
    openapi_yaml = yaml.dump(openapi_schema, sort_keys=False, allow_unicode=True)
    return Response(content=openapi_yaml, media_type="text/yaml")

app.add_exception_handler(Exception, global_exception_handler)

@app.get("/scalar", include_in_schema=False)
async def scalar_html() -> HTMLResponse:
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )

if __name__ == "__main__":
    if env_type == "local":
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    else:
        uvicorn.run("main:app", host="0.0.0.0", port=8000, proxy_headers=True, forwarded_allow_ips="*")
