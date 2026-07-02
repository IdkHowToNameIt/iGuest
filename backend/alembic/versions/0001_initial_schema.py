"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 768


def upgrade() -> None:
    # pgvector extension (also created by Docker init.sql, idempotent)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "structure",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("country_language", sa.Text, nullable=False),
        sa.Column("owner_contact", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "unit",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "structure_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("structure.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("owner_contact", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "document",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "scope_type",
            sa.Enum("structure", "unit", name="document_scope_type"),
            nullable=False,
        ),
        sa.Column(
            "structure_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("structure.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "unit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("unit.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("original_filename", sa.Text, nullable=False),
        sa.Column("file_type", sa.Text, nullable=False),
        sa.Column("extracted_text", sa.Text, nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "processed", "error", name="document_status"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "document_chunk",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("document.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "structure_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("structure.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "unit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("unit.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    # HNSW index with cosine distance — optimal for normalised text embeddings
    op.execute(
        "CREATE INDEX idx_chunk_embedding ON document_chunk "
        "USING hnsw (embedding vector_cosine_ops)"
    )
    # Composite index to accelerate the dual-scope retrieval query
    # (unit_id = X) OR (structure_id = Y AND unit_id IS NULL)
    op.create_index(
        "idx_chunk_scope",
        "document_chunk",
        ["structure_id", "unit_id"],
    )

    op.create_table(
        "guest_link",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "unit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("unit.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("token", sa.Text, nullable=False, unique=True),
        sa.Column(
            "status",
            sa.Enum("active", "revoked", name="guest_link_status"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("idx_guest_link_token", "guest_link", ["token"], unique=True)

    op.create_table(
        "conversation",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "guest_link_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("guest_link.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "unit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("unit.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("delete_after", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "message",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversation.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "role",
            sa.Enum("guest", "assistant", name="message_role"),
            nullable=False,
        ),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("detected_language", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("message")
    op.drop_table("conversation")
    op.drop_index("idx_guest_link_token", table_name="guest_link")
    op.drop_table("guest_link")
    op.drop_index("idx_chunk_scope", table_name="document_chunk")
    op.drop_index("idx_chunk_embedding", table_name="document_chunk")
    op.drop_table("document_chunk")
    op.drop_table("document")
    op.drop_table("unit")
    op.drop_table("structure")
    op.execute("DROP TYPE IF EXISTS message_role")
    op.execute("DROP TYPE IF EXISTS guest_link_status")
    op.execute("DROP TYPE IF EXISTS document_status")
    op.execute("DROP TYPE IF EXISTS document_scope_type")
