"""add is_admin to user

Revision ID: 0002_user_is_admin
Revises: 0001_init
Create Date: 2026-07-05

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_user_is_admin"
down_revision: str | None = "0001_init"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 기존 행은 server_default=false로 채운다(신규 삽입은 ORM 기본값 사용).
    op.add_column(
        "user",
        sa.Column(
            "is_admin",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("user", "is_admin")
