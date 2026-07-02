from datetime import datetime

from sqlalchemy import DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin, utcnow


class AdminProfile(UUIDMixin, TimestampMixin, Base):
    """Profile for the single administrator account (display name + avatar).

    The admin has no DB-backed identity (credentials are compared against
    .env, see app/services/auth.py) — this table holds the one supplementary
    row that gives that account a display name and picture. Enforced as a
    singleton at the service layer (get-or-create on first read), not via a
    DB constraint, since a single-row table with no natural key would need an
    artificial one just to express "at most one row".
    """

    __tablename__ = "admin_profile"

    display_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
