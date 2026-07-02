import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.host import Host
    from app.models.structure import Structure


class DocumentChangeRequest(UUIDMixin, TimestampMixin, Base):
    """A host's request to change the documentation of their structure.

    Optionally references a specific ``document``. The host/document references
    use ON DELETE SET NULL so the request survives (for the admin's audit) even
    if the host account or the referenced document is later removed; the
    structure reference cascades (the request is meaningless without it).
    """

    __tablename__ = "document_change_request"

    structure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("structure.id", ondelete="CASCADE"), nullable=False, index=True
    )
    host_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("host.id", ondelete="SET NULL"), nullable=True, index=True
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document.id", ondelete="SET NULL"), nullable=True
    )
    # For "other" requests (not tied to a document): the host-written problem title.
    # Null when the request references a specific document. The request "type" is
    # derived: document_id set -> "document", else -> "other".
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("open", "resolved", name="change_request_status"), nullable=False, default="open"
    )
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    structure: Mapped["Structure"] = relationship("Structure")
    host: Mapped["Host | None"] = relationship("Host")
    document: Mapped["Document | None"] = relationship("Document")
