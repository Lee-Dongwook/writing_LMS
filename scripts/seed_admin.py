"""어드민(교사) 계정을 .env의 ADMIN_* 값으로 부트스트랩한다(멱등).

실행: `make seed-admin` (또는 `.env` 소스 후 `python -m scripts.seed_admin`).
ADMIN_EMAIL / ADMIN_PASSWORD 가 없으면 안내 후 종료한다.
"""

from __future__ import annotations

import asyncio
import logging

from src.app.auth.service import ensure_admin_user
from src.app.shared.config import get_settings
from src.app.shared.database import async_context_session

logger = logging.getLogger(__name__)


async def _main() -> None:
    settings = get_settings()
    if not settings.admin_email or not settings.admin_password_hash:
        msg = (
            "ADMIN_EMAIL / ADMIN_PASSWORD_HASH 를 .env에 설정하세요 "
            "(해시 생성: `make hash-password`)."
        )
        raise SystemExit(msg)

    async with async_context_session() as db:
        user = await ensure_admin_user(
            db,
            email=settings.admin_email,
            password_hash=settings.admin_password_hash,
            name=settings.admin_name,
        )
        # 세션 종료(커밋) 전에 필요한 값을 확정
        summary = (user.email, user.uuid, user.is_admin)

    logger.info("어드민 계정 준비 완료: email=%s uuid=%s is_admin=%s", *summary)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(_main())
