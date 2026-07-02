"""Add visit_request table (public "book a visit" leads from the landing page)

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-02

Prospects who are not yet customers submit a visit request from the public
landing page (no authentication). The admin reviews these leads in a dedicated
inbox, separate from the host-submitted document change requests.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "visit_request",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("structure_name", sa.Text, nullable=False),
        sa.Column("city", sa.Text, nullable=True),
        sa.Column("business_type", sa.Text, nullable=True),
        sa.Column("contact_name", sa.Text, nullable=False),
        sa.Column("contact_email", sa.Text, nullable=False),
        sa.Column("preferred_date", sa.Date, nullable=True),
        sa.Column(
            "status",
            sa.Enum("new", "contacted", "archived", name="visit_request_status"),
            nullable=False,
            server_default="new",
        ),
        sa.Column("admin_note", sa.Text, nullable=True),
        sa.Column("handled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("idx_visit_request_status", "visit_request", ["status"])


def downgrade() -> None:
    op.drop_index("idx_visit_request_status", table_name="visit_request")
    op.drop_table("visit_request")
    sa.Enum(name="visit_request_status").drop(op.get_bind(), checkfirst=True)
