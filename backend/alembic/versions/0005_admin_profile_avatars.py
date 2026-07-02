"""Add admin_profile table and host.avatar_path (profile pictures)

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-01

The admin account has no DB row today (credentials come from .env); this adds
a single-row `admin_profile` table so it can have a display name and avatar
like a real account. `host.avatar_path` gives each host the same. Both store
a relative path served by the backend's /uploads static mount, not the image
itself.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_profile",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("display_name", sa.Text, nullable=True),
        sa.Column("avatar_path", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.add_column("host", sa.Column("avatar_path", sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column("host", "avatar_path")
    op.drop_table("admin_profile")
