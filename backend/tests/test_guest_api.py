"""
HTTP-layer tests for the guest API (no DB, no network).

get_db is overridden with a configurable fake session so we can verify routing,
link-error → HTTP status mapping, request validation, and the opening payload
without a live database.
"""

import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import routers
from app.database import get_db
from app.main import app
from app.services.chat import ChatReply


class FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class FakeDB:
    """Configurable fake Session: returns a link from execute() and
    unit/structure from get()."""

    def __init__(self, link=None, unit=None, structure=None):
        self._link = link
        self._unit = unit
        self._structure = structure

    def execute(self, *a, **k):
        return FakeResult(self._link)

    def get(self, model, pk):
        if model.__name__ == "Unit":
            return self._unit
        if model.__name__ == "Structure":
            return self._structure
        return None


def make_fakes(status="active", valid_from=None, valid_until=None):
    structure = SimpleNamespace(
        id=uuid.uuid4(), country_language="it", owner_contact="host@struct.com",
        welcome_message=None,
    )
    unit = SimpleNamespace(id=uuid.uuid4(), structure_id=structure.id, owner_contact=None)
    link = SimpleNamespace(
        id=uuid.uuid4(), unit_id=unit.id, token="tok", status=status,
        valid_from=valid_from, valid_until=valid_until,
    )
    return link, unit, structure


def override_db(db):
    def _gen():
        yield db
    app.dependency_overrides[get_db] = _gen


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


# ── error mapping ────────────────────────────────────────────────────────────

def test_unknown_token_opening_404():
    override_db(FakeDB(link=None))
    r = client.get("/api/guest/xxx/opening")
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "not_found"


def test_unknown_token_chat_404():
    override_db(FakeDB(link=None))
    r = client.post("/api/guest/xxx/chat", json={"message": "ciao"})
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "not_found"


def test_revoked_link_opening_403():
    link, unit, structure = make_fakes(status="revoked")
    override_db(FakeDB(link, unit, structure))
    r = client.get("/api/guest/tok/opening")
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "revoked"


def test_expired_link_opening_410():
    from app.models.base import utcnow
    from datetime import timedelta
    link, unit, structure = make_fakes(valid_until=utcnow() - timedelta(days=1))
    override_db(FakeDB(link, unit, structure))
    r = client.get("/api/guest/tok/opening")
    assert r.status_code == 410
    assert r.json()["detail"]["code"] == "expired"


def test_empty_message_validation_422():
    override_db(FakeDB(link=None))
    r = client.post("/api/guest/tok/chat", json={"message": ""})
    assert r.status_code == 422


# ── happy paths ──────────────────────────────────────────────────────────────

def test_opening_returns_bilingual_payload():
    link, unit, structure = make_fakes()
    override_db(FakeDB(link, unit, structure))
    r = client.get("/api/guest/tok/opening")
    assert r.status_code == 200
    body = r.json()
    assert body["primary_language"] == "it"
    assert body["primary_message"]      # greeting in Italian
    assert body["english_message"]      # English version present
    assert body["language_note"]
    assert "host@struct.com" in body["privacy_notice"]


def test_chat_happy_path(monkeypatch):
    link, unit, structure = make_fakes()
    override_db(FakeDB(link, unit, structure))

    conv_id = uuid.uuid4()
    monkeypatch.setattr(
        routers.guest, "handle_guest_message",
        lambda db, token, message: ChatReply(
            conversation_id=conv_id, answer="Risposta.", detected_language="it"
        ),
    )

    r = client.post("/api/guest/tok/chat", json={"message": "Domanda?"})
    assert r.status_code == 200
    body = r.json()
    assert body["answer"] == "Risposta."
    assert body["detected_language"] == "it"
    assert body["conversation_id"] == str(conv_id)


def test_chat_rate_limited_returns_503_busy(monkeypatch):
    link, unit, structure = make_fakes()
    override_db(FakeDB(link, unit, structure))

    class FakeRateLimit(Exception):
        code = 429  # mirrors google.genai ClientError on quota exhaustion

    def boom(db, token, message):
        raise FakeRateLimit("429 RESOURCE_EXHAUSTED")

    monkeypatch.setattr(routers.guest, "handle_guest_message", boom)

    r = client.post("/api/guest/tok/chat", json={"message": "Domanda?"})
    assert r.status_code == 503
    assert r.json()["detail"]["code"] == "busy"
