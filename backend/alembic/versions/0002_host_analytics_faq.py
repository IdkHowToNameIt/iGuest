"""Host portal, question analytics and per-unit FAQ

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-29

Adds:
  - host accounts (scoped to a unit) and document change requests,
  - question clusters (semantic grouping of guest questions, FAQ source),
  - message.embedding / message.faq_cluster_id columns for the FAQ pipeline.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 768


def upgrade() -> None:
    op.create_table(
        "host",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "unit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("unit.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("email", sa.Text, nullable=False, unique=True),
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
    op.create_index("idx_host_email", "host", ["email"], unique=True)

    op.create_table(
        "question_cluster",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "unit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("unit.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("centroid", Vector(EMBEDDING_DIM), nullable=False),
        sa.Column("representative_question", sa.Text, nullable=False),
        sa.Column("category_label", sa.Text, nullable=False),
        sa.Column("question_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("share", sa.Float, nullable=False, server_default="0"),
        sa.Column("faq_rank", sa.Integer, nullable=True),
        sa.Column("faq_answer", sa.Text, nullable=True),
        sa.Column("faq_answer_language", sa.Text, nullable=True),
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

    op.create_table(
        "document_change_request",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "unit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("unit.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "host_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("host.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("document.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column(
            "status",
            sa.Enum("open", "resolved", name="change_request_status"),
            nullable=False,
            server_default="open",
        ),
        sa.Column("admin_note", sa.Text, nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # FAQ pipeline columns on message
    op.add_column("message", sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True))
    op.add_column(
        "message",
        sa.Column(
            "faq_cluster_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("question_cluster.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("message", "faq_cluster_id")
    op.drop_column("message", "embedding")
    op.drop_table("document_change_request")
    op.drop_table("question_cluster")
    op.drop_index("idx_host_email", table_name="host")
    op.drop_table("host")
    op.execute("DROP TYPE IF EXISTS change_request_status")
