import os

import uvicorn
import yaml
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from scalar_fastapi import get_scalar_api_reference

from src.app import models  # noqa: F401  # 모델 매퍼 레지스트리 등록
from src.app.auth.router import router as auth_router
from src.app.shared import init as shared_init
from src.app.shared.exceptions import global_exception_handler
from src.app.shared.logging import setup_logging
from src.app.shared.middleware import setup_middleware
from src.app.writing.router import router as writing_router

env_type = os.getenv("ENV", "development")
shared_init.load_dotenv(env_type)

setup_logging()

os.environ["TOKENIZERS_PARALLELISM"] = "false"


app = FastAPI(
    title="Writing LMS API",
    description="Writing LMS API",
    version="0.1.0",
    swagger_ui_init_oauth={
        "appName": "Writing LMS",
        "usePkceWithAuthorizationCodeGrant": True,
        "scopes": "openid email profile",
    },
)

setup_middleware(app)

app.include_router(auth_router)
app.include_router(writing_router)


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
