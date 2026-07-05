import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Document(Base, RegistryMixin):
    __tablename__ = "document"
    __registry_type__= UnifiedResourceType.DOCUMENT

    uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )

    title: Mapped[str] = mapped_column(
        String,
    )

    slug: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=True,
    )

    description: Mapped[str] = mapped_column(
        String,
        default="",
        nullable=True,
    )

    inputs: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        default=list,
    )

    user_uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("user.uuid"),
        index=True,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="doc_templates",
    )
