"""user role column

Revision ID: 0003_user_role
Revises: 0002_user_is_admin
Create Date: 2026-07-10 04:45:01.058617+00:00

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0003_user_role"
down_revision: str | None = "0002_user_is_admin"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # role 컬럼 추가(기본 student). 기존 행은 server_default로 student가 채워진다.
    op.add_column(
        "user",
        sa.Column("role", sa.String(), server_default=sa.text("'student'"), nullable=False),
    )
    op.create_index(op.f("ix_user_role"), "user", ["role"], unique=False)
    # 백필: 기존 관리자(교사)로 부트스트랩된 계정은 teacher로 승격.
    op.execute("UPDATE \"user\" SET role = 'teacher' WHERE is_admin = true")


def downgrade() -> None:
    op.drop_index(op.f("ix_user_role"), table_name="user")
    op.drop_column("user", "role")
