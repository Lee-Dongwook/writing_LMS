from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.app.shared.database import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Document(Base):
    """수능 비문학 학습 문서 템플릿.

    `inputs`는 동적 폼 요소 정의(JSONB), `pipeline`은 LangGraph 실행 스키마(JSONB)를
    담는다. 문서는 사용자별로 소유된다(`user_uuid`).

    TODO: User 모델/인증 레이어가 준비되면 `user_uuid`에 FK와 relationship을 복원하고,
    공용 RegistryMixin(UnifiedResourceType)을 다시 붙인다.
    """

    __tablename__ = "document"

    uuid: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
    )

    title: Mapped[str] = mapped_column(String)
    slug: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    description: Mapped[str | None] = mapped_column(String, default="", nullable=True)

    inputs: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    pipeline: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        default=None,
        nullable=True,
    )

    user_uuid: Mapped[str] = mapped_column(UUID(as_uuid=False), index=True)
