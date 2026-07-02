"""Add admin_user table (additional admin logins alongside the .env account)

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-02

Lets the admin panel create further named admin accounts (bcrypt password
hash, temporary password on creation/reset) on top of the original single
.env admin, which keeps working unchanged as a fallback login.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_user",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.Text, nullable=False, unique=True),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("must_change_password", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("idx_admin_user_username", "admin_user", ["username"], unique=True)


def downgrade() -> None:
    op.drop_index("idx_admin_user_username", table_name="admin_user")
    op.drop_table("admin_user")
