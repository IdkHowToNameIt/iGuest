"""
Guest-facing API (no authentication — access is via the capability token).

  GET  /api/guest/{token}/opening  → bilingual opening message + privacy notice
  GET  /api/guest/{token}/history   → the conversation so far (temporary history)
  GET  /api/guest/{token}/faqs      → suggested FAQ menu (once enough have built up)
  POST /api/guest/{token}/chat      → ask a question, get an answer

Link errors are mapped to HTTP status codes with a machine-readable `code`
so the frontend (Phase 6) can show the right screen.
"""

from typing import NoReturn

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Conversation, Message, Structure, Unit
from app.schemas.guest import (
    ChatRequest,
    ChatResponse,
    FaqEntry,
    FaqMenuResponse,
    HistoryMessage,
    HistoryResponse,
    OpeningResponse,
)
from app.services.chat import handle_guest_message
from app.services.faq import list_unit_faqs
from app.services.links import LinkError, resolve_link
from app.services.opening import build_opening
from app.services.rag.prompt import resolve_owner_contact

router = APIRouter(prefix="/api/guest", tags=["guest"])

# Map link error types to HTTP status codes (by error code string)
_ERROR_STATUS = {
    "not_found": 404,
    "revoked": 403,
    "expired": 410,
    "not_yet_valid": 403,
}


def _raise_link_error(exc: LinkError) -> NoReturn:
    status = _ERROR_STATUS.get(exc.code, 400)
    raise HTTPException(status_code=status, detail={"code": exc.code, "message": str(exc)})


def _is_provider_busy(exc: Exception) -> bool:
    """True if *exc* is a transient Gemini error (quota or overload).

    Covers rate limiting (429) and the 503/504 the API returns when a model is
    overloaded; both mean "try again in a moment" rather than a server bug.
    Checked structurally (no hard SDK import) so both the embedding and the
    generation call sites are covered.
    """
    message = str(exc)
    return getattr(exc, "code", None) in {429, 503, 504} or any(
        marker in message
        for marker in ("RESOURCE_EXHAUSTED", "UNAVAILABLE", "DEADLINE_EXCEEDED")
    )


@router.get("/{token}/opening", response_model=OpeningResponse)
def get_opening(token: str, db: Session = Depends(get_db)):
    try:
        link = resolve_link(db, token)
    except LinkError as exc:
        _raise_link_error(exc)

    unit: Unit = db.get(Unit, link.unit_id)
    structure: Structure = db.get(Structure, unit.structure_id)
    owner_contact = resolve_owner_contact(unit.owner_contact, structure.owner_contact)

    opening = build_opening(
        structure.country_language,
        owner_contact,
        settings.conversation_retention_days,
        structure.welcome_message,
    )
    return OpeningResponse(**opening.__dict__)


@router.get("/{token}/history", response_model=HistoryResponse)
def get_history(token: str, db: Session = Depends(get_db)):
    """The conversation so far for this link.

    Lets a returning guest see their previous messages. The history is temporary:
    it is erased when the link is revoked and auto-deleted at end of stay.
    """
    try:
        link = resolve_link(db, token)
    except LinkError as exc:
        _raise_link_error(exc)

    conversation = (
        db.execute(select(Conversation).where(Conversation.guest_link_id == link.id))
        .scalars()
        .first()
    )
    if conversation is None:
        return HistoryResponse(messages=[])

    messages = (
        db.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at)
        )
        .scalars()
        .all()
    )
    return HistoryResponse(
        messages=[HistoryMessage(role=m.role, content=m.content) for m in messages]
    )


@router.get("/{token}/faqs", response_model=FaqMenuResponse)
def get_faqs(token: str, db: Session = Depends(get_db)):
    """Suggested questions for this unit, hidden until enough have accumulated."""
    try:
        link = resolve_link(db, token)
    except LinkError as exc:
        _raise_link_error(exc)

    entries = list_unit_faqs(db, link.unit_id)
    if len(entries) < settings.faq_min_to_show:
        return FaqMenuResponse(enabled=False, entries=[])
    return FaqMenuResponse(
        enabled=True,
        entries=[
            FaqEntry(question=e.question, answer=e.answer, answer_language=e.answer_language)
            for e in entries
        ],
    )


@router.post("/{token}/chat", response_model=ChatResponse)
def post_chat(token: str, body: ChatRequest, db: Session = Depends(get_db)):
    try:
        reply = handle_guest_message(db, token, body.message)
    except LinkError as exc:
        _raise_link_error(exc)
    except Exception as exc:
        if _is_provider_busy(exc):
            # Free-tier quota hit: ask the guest to retry shortly instead of a 500.
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "busy",
                    "message": "The assistant is momentarily busy. Please try again in a few moments.",
                },
            )
        raise

    return ChatResponse(
        conversation_id=reply.conversation_id,
        answer=reply.answer,
        detected_language=reply.detected_language,
    )
