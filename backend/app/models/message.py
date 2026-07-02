import uuid
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.document_chunk import EMBEDDING_DIM

if TYPE_CHECKING:
    from app.models.conversation import Conversation


class Message(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "message"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversation.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(
        Enum("guest", "assistant", name="message_role"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # BCP 47 tag detected from the guest message; null for assistant messages
    detected_language: Mapped[str | None] = mapped_column(Text, nullable=True)
    # FAQ analytics (guest messages only): cached embedding to avoid re-embedding
    # across recompute runs, and the cluster the question was assigned to.
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    faq_cluster_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("question_cluster.id", ondelete="SET NULL"), nullable=True
    )

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
