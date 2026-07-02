import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.structure import Structure


class Host(UUIDMixin, TimestampMixin, Base):
    """A property host account, scoped to a single structure.

    Hosts are created by the administrator (no public registration). They manage
    a whole property: they can view all of the structure's documentation
    (read-only, across its units) and submit change requests. Credentials are an
    email + a bcrypt password hash; the first password is a temporary one issued
    by the admin, hence ``must_change_password`` defaults to True.
    """

    __tablename__ = "host"

    structure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("structure.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    avatar_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    structure: Mapped["Structure"] = relationship("Structure")
