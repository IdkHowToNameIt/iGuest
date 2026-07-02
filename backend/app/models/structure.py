from typing import TYPE_CHECKING

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.unit import Unit


class Structure(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "structure"

    name: Mapped[str] = mapped_column(Text, nullable=False)
    # BCP 47 language tag for the country/property locale, e.g. "it", "en", "fr"
    country_language: Mapped[str] = mapped_column(Text, nullable=False)
    owner_contact: Mapped[str] = mapped_column(Text, nullable=False)

    # Optional custom greeting shown to guests at the start of the chat, replacing
    # the default catalog greeting for this structure. Null falls back to the
    # built-in per-language greeting (see app.services.opening).
    welcome_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Location (Italian admin geography) — used by the admin management view for
    # filtering and search. Free of any external service: validated client-side
    # against the static /api/geo dataset.
    region: Mapped[str | None] = mapped_column(Text, nullable=True)
    province: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Admin-only contact details for reaching the property's host/manager. Never
    # exposed to guests or on the host portal.
    contact_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_email: Mapped[str | None] = mapped_column(Text, nullable=True)

    # delete-cascade: removing a structure removes its units (and, via the units'
    # own cascades + the ON DELETE CASCADE FKs, their documents/links/conversations).
    units: Mapped[list["Unit"]] = relationship(
        "Unit", back_populates="structure", cascade="all, delete-orphan", passive_deletes=True
    )
