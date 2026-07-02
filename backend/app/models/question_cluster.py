import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin, utcnow
from app.models.document_chunk import EMBEDDING_DIM

if TYPE_CHECKING:
    from app.models.unit import Unit


class QuestionCluster(UUIDMixin, TimestampMixin, Base):
    """A semantic cluster of guest questions for one unit.

    Produced by the FAQ recompute script: guest questions are embedded and
    grouped by cosine similarity. Each cluster holds a representative question,
    a coarser ``category_label`` (used by the admin analytics drill-down), the
    question count and share, and — for the top clusters — a generated FAQ
    answer surfaced in the guest chat.
    """

    __tablename__ = "question_cluster"

    unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("unit.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Mean of the member-question embeddings — the cluster centroid.
    centroid: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    representative_question: Mapped[str] = mapped_column(Text, nullable=False)
    # Coarser semantic grouping label (the representative question of the category).
    category_label: Mapped[str] = mapped_column(Text, nullable=False)
    question_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    share: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    # 1..N for the top FAQ clusters (null otherwise); answer generated for these.
    faq_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    faq_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    faq_answer_language: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    unit: Mapped["Unit"] = relationship("Unit")
