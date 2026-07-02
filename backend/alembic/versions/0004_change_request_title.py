"""Add optional title to document_change_request (for "other" requests)

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-01

An "other" change request is not tied to a specific document; the host writes a
short problem title instead. Stored in a nullable ``title`` column (null for
document-scoped requests).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "document_change_request", sa.Column("title", sa.Text, nullable=True)
    )


def downgrade() -> None:
    op.drop_column("document_change_request", "title")
