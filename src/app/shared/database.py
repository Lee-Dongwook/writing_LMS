from __future__ import annotations

from contextlib import asynccontextmanager
from functools import lru_cache
from typing import TYPE_CHECKING

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
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
    """LangGraph 파이프라인용 Postgres 체크포인터 컨텍스트.

    최초 사용 전 테이블 준비는 `AsyncPostgresSaver.setup()`으로 수행한다
    (마이그레이션 레이어가 준비되면 그쪽으로 이관 예정).
    """
    settings = get_settings()
    async with AsyncPostgresSaver.from_conn_string(settings.checkpoint_dsn) as checkpointer:
        yield checkpointer
