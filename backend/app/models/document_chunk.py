import uuid
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.document import Document

# Must match the output dimension of the Gemini embedding model used in Phases 2-3.
# text-embedding-004 default output is 768 dimensions.
EMBEDDING_DIM = 768


class DocumentChunk(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "document_chunk"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Denormalised for efficient retrieval: always set regardless of scope
    structure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("structure.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Null for structure-scoped chunks; set for unit-scoped chunks
    unit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("unit.id", ondelete="CASCADE"), nullable=True, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
