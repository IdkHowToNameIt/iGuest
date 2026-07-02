"""
GDPR conversation retention.

Conversations are stored with a `delete_after` timestamp set at creation. A
cleanup job removes everything past that timestamp. The two date helpers are
pure functions so the retention policy can be unit-tested without a DB.
"""

from datetime import datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Conversation
from app.models.base import utcnow


def compute_delete_after(
    created_at: datetime | None = None,
    retention_days: int | None = None,
) -> datetime:
    """Return the timestamp at which a conversation created now should be deleted."""
    created_at = created_at or utcnow()
    days = retention_days if retention_days is not None else settings.conversation_retention_days
    return created_at + timedelta(days=days)


def is_conversation_expired(delete_after: datetime | None, now: datetime | None = None) -> bool:
    """True if a conversation with this `delete_after` is past retention."""
    if delete_after is None:
        return False
    now = now or utcnow()
    return now >= delete_after


def purge_expired_conversations(db: Session, now: datetime | None = None) -> int:
    """Delete all conversations whose `delete_after` has passed.

    Messages cascade-delete via the FK relationship. Returns the number of
    conversations removed.
    """
    now = now or utcnow()
    stmt = delete(Conversation).where(
        Conversation.delete_after.is_not(None),
        Conversation.delete_after <= now,
    )
    result = db.execute(stmt)
    db.commit()
    return result.rowcount or 0
