"""
Guest chat orchestration.

Ties together link resolution → conversation persistence → RAG answer.

Conversation model: one conversation per GuestLink (the link represents a
booking / stay). It is created lazily on the first message and reused for
subsequent ones. `delete_after` is set at creation for GDPR retention.

No personal data about the guest is ever requested or stored — only the
message text and the assistant reply, tied to the anonymous link token.
"""

import uuid
from dataclasses import dataclass
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Conversation, GuestLink, Message
from app.services.links import resolve_link
from app.services.rag import RagResult, answer_question
from app.services.retention import compute_delete_after


@dataclass
class ChatReply:
    conversation_id: uuid.UUID
    answer: str
    detected_language: str | None


def get_or_create_conversation(db: Session, link: GuestLink) -> Conversation:
    """Return the link's conversation, creating it on first use."""
    stmt = select(Conversation).where(Conversation.guest_link_id == link.id)
    conversation = db.execute(stmt).scalars().first()
    if conversation is not None:
        return conversation

    conversation = Conversation(
        guest_link_id=link.id,
        unit_id=link.unit_id,
        delete_after=compute_delete_after(),
    )
    db.add(conversation)
    db.flush()  # assign id without ending the transaction
    return conversation


def handle_guest_message(
    db: Session,
    token: str,
    message: str,
    *,
    answer_fn: Callable[..., RagResult] = answer_question,
) -> ChatReply:
    """Process one guest message end to end.

    1. Resolve and validate the link (raises LinkError if unusable).
    2. Get or create the conversation for this link.
    3. Persist the guest message.
    4. Generate the answer via the RAG engine.
    5. Persist the assistant reply (with detected language).

    Args:
        answer_fn: injectable RAG entry point (defaults to the real engine).

    Returns:
        ChatReply with the answer, detected language and conversation id.
    """
    link = resolve_link(db, token)
    conversation = get_or_create_conversation(db, link)

    # Persist the guest message and commit it *before* calling the model: a
    # generation failure downstream (e.g. a Gemini rate limit) must not lose
    # the fact the guest asked something, since that's the raw material for
    # FAQ clustering and analytics. A flush-only row is rolled back with the
    # rest of the transaction if answer_fn raises, silently dropping it.
    guest_msg = Message(
        conversation_id=conversation.id,
        role="guest",
        content=message,
    )
    db.add(guest_msg)
    db.commit()

    # Generate the answer (dual-scope RAG over the unit + its structure). If
    # this raises, the guest message above is already safely committed.
    result: RagResult = answer_fn(db, link.unit_id, message)

    # Record the detected language on the guest message too (for admin review)
    guest_msg.detected_language = result.detected_language

    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=result.answer,
        detected_language=result.detected_language,
    )
    db.add(assistant_msg)
    db.commit()

    return ChatReply(
        conversation_id=conversation.id,
        answer=result.answer,
        detected_language=result.detected_language,
    )
