"""LangGraph 체크포인터 테이블을 생성/마이그레이션한다.

`AsyncPostgresSaver.setup()`은 자체 스키마(checkpoints/checkpoint_blobs/
checkpoint_writes/checkpoint_migrations)를 idempotent하게 생성한다. Alembic이 관리하는
앱 테이블(user/document)과 분리되어 있으므로 별도로 한 번 실행하면 된다.

실행: `make checkpoint-setup` (또는 `.env` 소스 후 `python -m scripts.setup_checkpointer`).
"""

from __future__ import annotations

import asyncio
import logging

from src.app.shared.database import get_checkpoint

logger = logging.getLogger(__name__)


async def _main() -> None:
    async with get_checkpoint() as checkpointer:
        await checkpointer.setup()
    logger.info("체크포인터 테이블 준비 완료")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_main())
