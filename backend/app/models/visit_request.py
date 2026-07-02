import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class VisitRequest(UUIDMixin, TimestampMixin, Base):
    """A "book a visit" request submitted from the public landing page.

    Unlike a ``DocumentChangeRequest`` this is *not* tied to an existing
    structure/host: it is a lead from someone who is not yet a customer, so it
    carries only the free-text contact details typed into the landing form. The
    admin reviews these in a dedicated inbox and marks them contacted/archived.
    """

    __tablename__ = "visit_request"

    # What/where — the property the prospect wants a visit for.
    structure_name: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str | None] = mapped_column(Text, nullable=True)
    # "bnb_hotel" | "private_host" | "property_manager" (free text; UI-constrained).
    business_type: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Who — the contact who will be called back.
    contact_name: Mapped[str] = mapped_column(Text, nullable=False)
    contact_email: Mapped[str] = mapped_column(Text, nullable=False)
    preferred_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Admin workflow.
    status: Mapped[str] = mapped_column(
        Enum("new", "contacted", "archived", name="visit_request_status"),
        nullable=False,
        default="new",
    )
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    handled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
