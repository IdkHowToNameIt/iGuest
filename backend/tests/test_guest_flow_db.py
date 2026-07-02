"""
Opt-in DB integration tests for the full guest flow.

These run only when RUN_DB_TESTS=1 and the configured PostgreSQL is reachable
with migrations applied (`alembic upgrade head`). They exercise real persistence:
link creation/resolution, chat conversation + message storage, and retention purge.

Run with:
    RUN_DB_TESTS=1 python -m pytest tests/test_guest_flow_db.py -v

Created rows are namespaced with "[TEST]" and removed in teardown (FK cascade).
The RAG engine is mocked so no Gemini API key is needed.
"""

import os
import sys
from datetime import timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

if os.getenv("RUN_DB_TESTS") != "1":
    pytest.skip("DB integration tests disabled (set RUN_DB_TESTS=1)", allow_module_level=True)

from sqlalchemy import delete, select

from app.database import SessionLocal, engine
from app.models import Conversation, GuestLink, Message, Structure, Unit
from app.models.base import utcnow
from app.services.chat import handle_guest_message
from app.services.links import (
    LinkExpiredError,
    LinkRevokedError,
    create_guest_link,
    resolve_link,
    revoke_link,
)
from app.services.rag import RagResult
from app.services.retention import purge_expired_conversations

# Skip the whole module if the DB isn't reachable
try:
    with engine.connect():
        pass
except Exception as exc:  # pragma: no cover
    pytest.skip(f"DB not reachable: {exc}", allow_module_level=True)


def fake_answer(db, unit_id, message):
    return RagResult(answer="Risposta di test.", detected_language="it", chunk_ids=[])


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        # Clean up everything created by the test (cascades to children)
        session.rollback()
        session.execute(delete(Structure).where(Structure.name.like("[TEST]%")))
        session.commit()
        session.close()


@pytest.fixture()
def unit(db):
    structure = Structure(
        name="[TEST] Property", country_language="it", owner_contact="host@test.com"
    )
    db.add(structure)
    db.flush()
    u = Unit(structure_id=structure.id, name="[TEST] Room", owner_contact=None)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def test_create_and_resolve_link(db, unit):
    link = create_guest_link(db, unit.id)
    assert len(link.token) >= 40
    assert link.status == "active"

    resolved = resolve_link(db, link.token)
    assert resolved.id == link.id
    assert resolved.unit_id == unit.id


def test_chat_persists_conversation_and_messages(db, unit):
    link = create_guest_link(db, unit.id)

    reply = handle_guest_message(db, link.token, "A che ora è il check-in?", answer_fn=fake_answer)
    assert reply.answer == "Risposta di test."
    assert reply.detected_language == "it"

    # Conversation created with a retention deadline
    conv = db.get(Conversation, reply.conversation_id)
    assert conv is not None
    assert conv.delete_after is not None
    assert conv.delete_after > utcnow()

    # Guest + assistant messages stored
    msgs = db.execute(
        select(Message).where(Message.conversation_id == conv.id).order_by(Message.created_at)
    ).scalars().all()
    assert [m.role for m in msgs] == ["guest", "assistant"]
    assert msgs[1].detected_language == "it"

    # Second message reuses the same conversation
    reply2 = handle_guest_message(db, link.token, "E il check-out?", answer_fn=fake_answer)
    assert reply2.conversation_id == reply.conversation_id
    count = db.execute(
        select(Message).where(Message.conversation_id == conv.id)
    ).scalars().all()
    assert len(count) == 4


def test_revoked_link_cannot_chat(db, unit):
    link = create_guest_link(db, unit.id)
    revoke_link(db, link)
    with pytest.raises(LinkRevokedError):
        resolve_link(db, link.token)


def test_expired_link_cannot_chat(db, unit):
    past = utcnow() - timedelta(days=1)
    link = create_guest_link(db, unit.id, valid_until=past)
    with pytest.raises(LinkExpiredError):
        resolve_link(db, link.token)


def test_retention_purge_deletes_expired(db, unit):
    link = create_guest_link(db, unit.id)

    expired = Conversation(
        guest_link_id=link.id, unit_id=unit.id, delete_after=utcnow() - timedelta(days=1)
    )
    surviving = Conversation(
        guest_link_id=link.id, unit_id=unit.id, delete_after=utcnow() + timedelta(days=10)
    )
    db.add_all([expired, surviving])
    db.commit()
    expired_id, surviving_id = expired.id, surviving.id

    purge_expired_conversations(db)

    assert db.get(Conversation, expired_id) is None
    assert db.get(Conversation, surviving_id) is not None
