import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.guest_link import GuestLink
    from app.models.structure import Structure


class Unit(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "unit"

    structure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("structure.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    # Overrides structure.owner_contact when set
    owner_contact: Mapped[str | None] = mapped_column(Text, nullable=True)

    structure: Mapped["Structure"] = relationship("Structure", back_populates="units")
    # delete-cascade: removing a unit removes its documents, links and (via links)
    # conversations. Relies on the ON DELETE CASCADE FKs (passive_deletes).
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="unit", cascade="all, delete-orphan", passive_deletes=True
    )
    guest_links: Mapped[list["GuestLink"]] = relationship(
        "GuestLink", back_populates="unit", cascade="all, delete-orphan", passive_deletes=True
    )
