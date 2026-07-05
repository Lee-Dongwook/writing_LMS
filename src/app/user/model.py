from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.shared.database import Base

if TYPE_CHECKING:
    from src.app.doc.model import Document


def _utcnow() -> datetime:
    return datetime.now(UTC)


class User(Base):
    """서비스 사용자.

    로컬 JWT 인증용 계정. `email`로 로그인하며 비밀번호는 bcrypt 해시로 저장한다.
    테이블명 `user`는 Postgres 예약어라 SQLAlchemy가 자동으로 따옴표 처리한다.
    """

    __tablename__ = "user"

    uuid: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)

    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
    )

    documents: Mapped[list[Document]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
