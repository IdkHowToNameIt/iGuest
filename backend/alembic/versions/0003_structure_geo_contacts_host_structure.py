"""Structure geo + admin contacts; hosts and change requests scoped to structure

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-30

Changes:
  - structure gains location fields (region/province/city) and admin-only
    contact fields (contact_name/contact_phone/contact_email),
  - host moves from being scoped to a unit to being scoped to a structure
    (a host manages a whole property, seeing all its units' documents),
  - document_change_request follows: unit_id -> structure_id.

The host / document_change_request tables are empty at this revision (they were
introduced in 0002 with no production data), so the FK column swap is done with a
plain drop/add rather than a data migration.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── structure: location + admin-only contact details ──────────────────────
    for col in ("region", "province", "city", "contact_name", "contact_phone", "contact_email"):
        op.add_column("structure", sa.Column(col, sa.Text, nullable=True))

    # ── host: unit -> structure ───────────────────────────────────────────────
    op.drop_column("host", "unit_id")  # drops the dependent FK constraint too
    op.add_column(
        "host",
        sa.Column(
            "structure_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("structure.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    op.create_index("idx_host_structure", "host", ["structure_id"])

    # ── document_change_request: unit -> structure ────────────────────────────
    op.drop_column("document_change_request", "unit_id")
    op.add_column(
        "document_change_request",
        sa.Column(
            "structure_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("structure.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_change_request_structure", "document_change_request", ["structure_id"]
    )


def downgrade() -> None:
    op.drop_index("idx_change_request_structure", table_name="document_change_request")
    op.drop_column("document_change_request", "structure_id")
    op.add_column(
        "document_change_request",
        sa.Column(
            "unit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("unit.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )

    op.drop_index("idx_host_structure", table_name="host")
    op.drop_column("host", "structure_id")
    op.add_column(
        "host",
        sa.Column(
            "unit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("unit.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )

    for col in ("contact_email", "contact_phone", "contact_name", "city", "province", "region"):
        op.drop_column("structure", col)
