from __future__ import annotations

from contextlib import asynccontextmanager
from functools import lru_cache
from typing import TYPE_CHECKING

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.app.shared.config import get_settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


class Base(DeclarativeBase):
    """모든 SQLAlchemy 모델의 선언적 베이스."""


@lru_cache
def get_engine() -> AsyncEngine:
    """프로세스당 하나의 비동기 엔진(지연 생성)."""
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.db_echo,
        pool_pre_ping=True,
    )


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """엔진에 바인딩된 세션 팩토리(지연 생성)."""
    return async_sessionmaker(
        bind=get_engine(),
        expire_on_commit=False,
        autoflush=False,
    )


async def get_async_db() -> AsyncGenerator[AsyncSession]:
    """FastAPI 의존성: 요청 스코프 비동기 DB 세션.

    정상 종료 시 커밋, 예외 발생 시 롤백한다.
    """
    async with get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def async_context_session() -> AsyncGenerator[AsyncSession]:
    """요청 컨텍스트 밖(파이프라인 핸들러 등)에서 쓰는 세션 컨텍스트."""
    async with get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_checkpoint() -> AsyncGenerator[AsyncPostgresSaver]:
    """단발성(스크립트/일회성)용 Postgres 체크포인터 컨텍스트.

    단일 커넥션 기반. 테이블 준비는 `AsyncPostgresSaver.setup()`으로 수행한다.
    앱 런타임의 장수(long-lived) 체크포인터는 `checkpointer_pool()`을 사용한다.
    """
    settings = get_settings()
    async with AsyncPostgresSaver.from_conn_string(settings.checkpoint_dsn) as checkpointer:
        yield checkpointer


@asynccontextmanager
async def checkpointer_pool() -> AsyncGenerator[AsyncPostgresSaver]:
    """앱 수명 동안 유지되는 커넥션 풀 기반 Postgres 체크포인터.

    FastAPI lifespan에서 열고 종료 시 닫는다. 진입 시 체크포인터 스키마를
    `setup()`으로 보장한다(idempotent). 동시 요청은 풀(max_size)로 처리한다.
    """
    settings = get_settings()
    # langgraph AsyncPostgresSaver 요구사항: autocommit + prepared statement 비활성.
    conn_kwargs = {"autocommit": True, "prepare_threshold": 0}
    pool = AsyncConnectionPool(
        conninfo=settings.checkpoint_dsn,
        max_size=20,
        open=False,
        kwargs=conn_kwargs,
    )
    async with pool:
        checkpointer = AsyncPostgresSaver(pool)
        await checkpointer.setup()
        yield checkpointer
