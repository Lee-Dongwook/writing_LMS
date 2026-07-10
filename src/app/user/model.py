from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, false, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.shared.database import Base

if TYPE_CHECKING:
    from src.app.doc.model import Document

# 사용자 역할. 학생은 학습 산출물 소비자, 교사는 관리/첨삭 주체.
# 관리자(교사)는 role="teacher" + is_admin=True 조합으로 표현한다.
ROLE_STUDENT = "student"
ROLE_TEACHER = "teacher"


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
    # 관리자(교사) 여부. seed-admin으로 부트스트랩되며, 향후 관리자 게이트에 사용.
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    # 역할: student(기본) | teacher. 학생/교사 구분 및 학생 목록 필터에 사용.
    role: Mapped[str] = mapped_column(
        String,
        default=ROLE_STUDENT,
        server_default=text(f"'{ROLE_STUDENT}'"),
        index=True,
    )

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
