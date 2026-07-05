"""Alembic 마이그레이션 환경.

DB URL은 앱 설정(`get_settings().database_url`)에서 가져온다(.env를 소스한 상태로
`make migrate-*`가 실행). 모델 메타데이터는 `src.app.models`를 import해 매퍼를 모두
등록한 뒤 `Base.metadata`를 대상으로 삼는다. LangGraph 체크포인터가 자체 관리하는
테이블은 autogenerate 대상에서 제외한다(별도 `setup()`으로 생성).
"""

from __future__ import annotations

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

import src.app.models  # noqa: F401 - 매퍼 레지스트리 등록(관계 문자열 참조 해소)
from alembic import context
from src.app.shared.config import get_settings
from src.app.shared.database import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 설정에서 DB URL 주입(alembic.ini의 sqlalchemy.url은 비워 둠)
config.set_main_option("sqlalchemy.url", get_settings().database_url)

target_metadata = Base.metadata

# LangGraph AsyncPostgresSaver가 관리하는 테이블 — autogenerate가 삭제하지 않도록 무시
_CHECKPOINT_TABLES = frozenset(
    {
        "checkpoints",
        "checkpoint_blobs",
        "checkpoint_writes",
        "checkpoint_migrations",
    },
)


def include_object(
    obj: object,  # noqa: ARG001
    name: str | None,
    type_: str,
    reflected: bool,  # noqa: ARG001, FBT001
    compare_to: object,  # noqa: ARG001
) -> bool:
    """체크포인터 테이블은 마이그레이션 비교에서 제외한다."""
    return not (type_ == "table" and name in _CHECKPOINT_TABLES)


def run_migrations_offline() -> None:
    """오프라인(--sql) 모드: DB 연결 없이 마이그레이션 SQL을 생성한다."""
    context.configure(
        url=get_settings().database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """온라인 모드: 동기 psycopg3 엔진으로 DB에 연결해 마이그레이션을 적용한다."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
