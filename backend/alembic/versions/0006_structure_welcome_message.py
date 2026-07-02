"""Add structure.welcome_message (custom chatbot greeting per structure)

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-01

Lets an admin override the default catalog greeting shown to guests at the
start of the chat, on a per-structure basis. Null keeps the built-in
per-language greeting (see app.services.opening.build_opening).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("structure", sa.Column("welcome_message", sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column("structure", "welcome_message")
