from __future__ import annotations

import logging

from src.app.shared.config import get_settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_NOISY_LOGGERS = ("httpx", "httpcore", "urllib3", "asyncio")


def setup_logging(level: str | None = None) -> None:
    """루트 로거를 표준 포맷으로 설정한다.

    `force=True`로 기존 핸들러를 교체해 중복 로그를 방지한다.
    """
    resolved = (level or get_settings().log_level).upper()
    logging.basicConfig(level=resolved, format=_LOG_FORMAT, force=True)

    for noisy in _NOISY_LOGGERS:
        logging.getLogger(noisy).setLevel(logging.WARNING)
