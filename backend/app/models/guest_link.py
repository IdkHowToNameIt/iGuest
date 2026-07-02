import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.unit import Unit


class GuestLink(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "guest_link"

    unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("unit.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Long random token — the capability URL identifier; never expose sequential IDs
    token: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(
        Enum("active", "revoked", name="guest_link_status"), nullable=False, default="active"
    )
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    unit: Mapped["Unit"] = relationship("Unit", back_populates="guest_links")
    # delete-cascade: revoking is the soft path; deleting a link (or its unit)
    # removes its conversations and messages too (GDPR erasure of a booking).
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="guest_link",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
