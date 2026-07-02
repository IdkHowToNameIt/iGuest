import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.guest_link import GuestLink
    from app.models.message import Message


class Conversation(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "conversation"

    guest_link_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("guest_link.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("unit.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # GDPR retention: auto-delete after this timestamp (set at conversation creation)
    delete_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    guest_link: Mapped["GuestLink"] = relationship("GuestLink", back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan", passive_deletes=True
    )
