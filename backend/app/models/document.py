import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.document_chunk import DocumentChunk
    from app.models.unit import Unit


class Document(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "document"

    scope_type: Mapped[str] = mapped_column(
        Enum("structure", "unit", name="document_scope_type"), nullable=False
    )
    # Always set — even for unit-scoped docs this records the parent structure
    structure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("structure.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Null for structure-scoped documents
    unit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("unit.id", ondelete="CASCADE"), nullable=True, index=True
    )
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    file_type: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("pending", "processed", "error", name="document_status"),
        nullable=False,
        default="pending",
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    unit: Mapped["Unit | None"] = relationship("Unit", back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan", passive_deletes=True
    )
