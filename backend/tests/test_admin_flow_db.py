"""
Opt-in DB integration test for the full admin flow.

Runs only when RUN_DB_TESTS=1 and PostgreSQL is reachable with migrations applied.
Embeddings are monkeypatched so no Gemini API key is needed.

    RUN_DB_TESTS=1 python -m pytest tests/test_admin_flow_db.py -v

Flow: login → create structure → create unit → upload document (ingested) →
list documents → generate link → create a conversation → list conversations →
get conversation detail → delete conversation (GDPR). Created rows are removed
in teardown via FK cascade.
"""

import os
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

if os.getenv("RUN_DB_TESTS") != "1":
    pytest.skip("DB integration tests disabled (set RUN_DB_TESTS=1)", allow_module_level=True)

from sqlalchemy import delete, select

from app.config import settings
from app.database import SessionLocal, engine
from app.main import app
from app.models import Conversation, Document, GuestLink, Structure, Unit
from app.services.chat import handle_guest_message
from app.services.rag import RagResult

try:
    with engine.connect():
        pass
except Exception as exc:  # pragma: no cover
    pytest.skip(f"DB not reachable: {exc}", allow_module_level=True)


client = TestClient(app)


@pytest.fixture(autouse=True)
def _patch_embeddings(monkeypatch):
    # Ingestion runs offline: fake 768-dim vectors instead of calling Gemini
    monkeypatch.setattr(
        "app.services.ingestion.pipeline.embed_documents",
        lambda chunks: [[0.0] * 768 for _ in chunks],
    )
    yield


@pytest.fixture(autouse=True)
def _cleanup():
    yield
    with SessionLocal() as s:
        s.execute(delete(Structure).where(Structure.name.like("[ADMINTEST]%")))
        s.commit()


def _auth():
    r = client.post(
        "/api/admin/login",
        json={"username": settings.admin_username, "password": settings.admin_password},
    )
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_full_admin_flow():
    h = _auth()

    # 1. create structure
    r = client.post(
        "/api/admin/structures",
        headers=h,
        json={"name": "[ADMINTEST] Villa", "country_language": "it", "owner_contact": "host@test.com"},
    )
    assert r.status_code == 201
    structure_id = r.json()["id"]

    # 2. create unit
    r = client.post(
        f"/api/admin/structures/{structure_id}/units",
        headers=h,
        json={"name": "[ADMINTEST] Room A"},
    )
    assert r.status_code == 201
    unit_id = r.json()["id"]

    # 3. upload a document (unit scope) → ingested
    r = client.post(
        "/api/admin/documents",
        headers=h,
        data={"scope_type": "unit", "target_id": unit_id},
        files={"file": ("manual.txt", b"Check-in is at 3 PM. The WiFi password is guest123.", "text/plain")},
    )
    assert r.status_code == 201
    doc = r.json()
    assert doc["status"] == "processed"
    assert doc["scope_type"] == "unit"

    # 4. list documents filtered by unit
    r = client.get(f"/api/admin/documents?unit_id={unit_id}", headers=h)
    assert r.status_code == 200
    assert any(d["id"] == doc["id"] for d in r.json())

    # 5. generate a link
    r = client.post(f"/api/admin/units/{unit_id}/links", headers=h, json={})
    assert r.status_code == 201
    link_token = r.json()["token"]
    assert r.json()["status"] == "active"

    # 6. create a conversation via the chat service (RAG mocked)
    with SessionLocal() as s:
        handle_guest_message(
            s, link_token, "A che ora è il check-in?",
            answer_fn=lambda db, uid, msg: RagResult("Alle 15:00.", "it", []),
        )

    # 7. list conversations for the unit
    r = client.get(f"/api/admin/units/{unit_id}/conversations", headers=h)
    assert r.status_code == 200
    convs = r.json()
    assert len(convs) == 1
    conversation_id = convs[0]["id"]

    # 8. conversation detail with messages
    r = client.get(f"/api/admin/conversations/{conversation_id}", headers=h)
    assert r.status_code == 200
    msgs = r.json()["messages"]
    assert [m["role"] for m in msgs] == ["guest", "assistant"]

    # 9. GDPR deletion
    r = client.delete(f"/api/admin/conversations/{conversation_id}", headers=h)
    assert r.status_code == 204
    r = client.get(f"/api/admin/conversations/{conversation_id}", headers=h)
    assert r.status_code == 404

    # 10. revoke the link
    link_id = client.get(f"/api/admin/units/{unit_id}/links", headers=h).json()[0]["id"]
    r = client.post(f"/api/admin/links/{link_id}/revoke", headers=h)
    assert r.status_code == 200
    assert r.json()["status"] == "revoked"


def test_delete_structure_cascades_all_children():
    """GDPR/data-management: deleting a structure removes its units, documents,
    links, conversations and messages (relies on ON DELETE CASCADE + ORM
    passive_deletes — regression guard for the NOT NULL disassociation bug)."""
    h = _auth()

    structure_id = client.post(
        "/api/admin/structures",
        headers=h,
        json={"name": "[ADMINTEST] Cascade", "country_language": "it", "owner_contact": "h@test.com"},
    ).json()["id"]
    unit_id = client.post(
        f"/api/admin/structures/{structure_id}/units",
        headers=h,
        json={"name": "[ADMINTEST] Unit"},
    ).json()["id"]
    client.post(
        "/api/admin/documents",
        headers=h,
        data={"scope_type": "unit", "target_id": unit_id},
        files={"file": ("m.txt", b"WiFi password is demo999.", "text/plain")},
    )
    link_token = client.post(f"/api/admin/units/{unit_id}/links", headers=h, json={}).json()["token"]
    with SessionLocal() as s:
        handle_guest_message(
            s, link_token, "wifi?",
            answer_fn=lambda db, uid, msg: RagResult("demo999", "en", []),
        )

    # delete the whole structure
    r = client.delete(f"/api/admin/structures/{structure_id}", headers=h)
    assert r.status_code == 204

    # API: structure and unit are gone
    assert client.get(f"/api/admin/structures/{structure_id}", headers=h).status_code == 404
    assert client.get(f"/api/admin/units/{unit_id}", headers=h).status_code == 404

    # DB: no orphaned children remain
    with SessionLocal() as s:
        assert s.execute(select(Unit).where(Unit.structure_id == structure_id)).first() is None
        assert s.execute(select(Document).where(Document.structure_id == structure_id)).first() is None
        assert s.execute(select(GuestLink).where(GuestLink.unit_id == unit_id)).first() is None
        assert s.execute(select(Conversation).where(Conversation.unit_id == unit_id)).first() is None
