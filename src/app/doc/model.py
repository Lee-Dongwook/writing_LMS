from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.shared.database import Base

if TYPE_CHECKING:
    from src.app.user.model import User


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Document(Base):
    """수능 비문학 학습 문서 템플릿.

    `inputs`는 동적 폼 요소 정의(JSONB), `pipeline`은 LangGraph 실행 스키마(JSONB)를
    담는다. 문서는 사용자별로 소유된다(`user_uuid` → user.uuid).

    TODO: 공용 RegistryMixin(UnifiedResourceType)은 레지스트리 레이어 준비 시 부착.
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

    user_uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("user.uuid", ondelete="CASCADE"),
        index=True,
    )
    user: Mapped[User] = relationship(back_populates="documents")
