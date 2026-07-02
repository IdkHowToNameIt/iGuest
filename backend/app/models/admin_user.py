from sqlalchemy import Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class AdminUser(UUIDMixin, TimestampMixin, Base):
    """An additional administrator login, alongside the legacy .env account.

    The original single admin (ADMIN_USERNAME/ADMIN_PASSWORD in .env, see
    app/services/auth.py) keeps working unchanged as a fallback that can
    never be locked out. An already-authenticated admin can create further
    named accounts here, managed the same way host accounts are: a bcrypt
    password hash, and a temporary password on creation/reset that must be
    rotated on first use.
    """

    __tablename__ = "admin_user"

    username: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
