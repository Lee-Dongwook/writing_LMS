"""init user and document tables

Revision ID: 0001_init
Revises:
Create Date: 2026-07-05

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_init"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # user 테이블(테이블명 "user"는 예약어 → SQLAlchemy가 자동 따옴표 처리)
    op.create_table(
        "user",
        sa.Column("uuid", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("uuid"),
    )
    op.create_index("ix_user_email", "user", ["email"], unique=True)

    # document 테이블(user FK, JSONB 동적 폼/파이프라인)
    op.create_table(
        "document",
        sa.Column("uuid", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("inputs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("pipeline", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("user_uuid", postgresql.UUID(as_uuid=False), nullable=False),
        sa.ForeignKeyConstraint(["user_uuid"], ["user.uuid"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("uuid"),
        sa.UniqueConstraint("slug", name="uq_document_slug"),
    )
    op.create_index("ix_document_user_uuid", "document", ["user_uuid"])


def downgrade() -> None:
    op.drop_index("ix_document_user_uuid", table_name="document")
    op.drop_table("document")
    op.drop_index("ix_user_email", table_name="user")
    op.drop_table("user")
