from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv as _dotenv_load

from src.app.shared.database import get_engine, get_session_factory
from src.app.shared.logging import setup_logging

logger = logging.getLogger(__name__)

_initialized = False

# 실행 환경 → .env 파일 매핑
_ENV_FILES = {
    "local": ".env.local",
    "development": ".env",
    "production": ".env.production",
}


def load_dotenv(env_type: str | None = None) -> None:
    """환경 타입에 맞는 `.env` 파일을 로드한다.

    지정 파일이 없으면 기본 `.env`로 폴백하며, 어느 것도 없으면 조용히 통과한다
    (실제 환경변수만으로 동작 가능해야 하므로 실패시키지 않는다).
    """
    env_type = env_type or os.getenv("ENV", "development")
    env_file = _ENV_FILES.get(env_type, ".env")

    for candidate in (env_file, ".env"):
        path = Path(candidate)
        if path.exists():
            _dotenv_load(dotenv_path=path, override=False)
            logger.debug("Loaded env file: %s", candidate)
            return


def initialize() -> None:
    """워커 프로세스당 1회 실행되는 공용 런타임 초기화.

    로깅을 설정하고 DB 엔진/세션 팩토리를 미리 생성해 첫 요청 지연을 줄인다.
    """
    global _initialized
    if _initialized:
        return

    setup_logging()
    get_engine()
    get_session_factory()

    _initialized = True
    logger.info("Shared runtime initialized")
