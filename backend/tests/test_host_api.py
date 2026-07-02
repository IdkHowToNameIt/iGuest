"""
HTTP-layer tests for the host API (no DB, no network).

Covers login failure, route protection (no token / admin token rejected), and a
couple of read paths using dependency overrides for the authenticated host and a
fake DB session.
"""

import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import get_db
from app.deps import require_host
from app.main import app
from app.models import Structure, Unit
from app.services.auth import create_access_token


class FakeResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return self

    def all(self):
        return self._items

    def first(self):
        return self._items[0] if self._items else None


class FakeDB:
    """Fake session: ``execute`` yields fixed items, ``get`` maps by model class."""

    def __init__(self, items=None, by_model=None):
        self._items = items or []
        self._by_model = by_model or {}

    def execute(self, *a, **k):
        return FakeResult(self._items)

    def get(self, model, pk):
        return self._by_model.get(model)

    def commit(self):
        pass

    def refresh(self, obj):
        pass


def override_db(db):
    def _gen():
        yield db
    app.dependency_overrides[get_db] = _gen


@pytest.fixture(autouse=True)
def _clear():
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


# ── login ──────────────────────────────────────────────────────────────────────

def test_host_login_invalid_credentials_401():
    override_db(FakeDB(items=[]))  # no matching host → HostAuthError → 401
    r = client.post("/api/host/login", json={"email": "h@x.com", "password": "nope"})
    assert r.status_code == 401


# ── protection ───────────────────────────────────────────────────────────────────

def test_host_me_without_token_401():
    r = client.get("/api/host/me")
    assert r.status_code == 401


def test_host_me_with_admin_token_403():
    # An admin token has role="admin"; require_host must reject it.
    r = client.get(
        "/api/host/me", headers={"Authorization": f"Bearer {create_access_token()}"}
    )
    assert r.status_code == 403


# ── read paths with an authenticated host ──────────────────────────────────────────

def _fake_host(structure_id):
    return SimpleNamespace(
        id=uuid.uuid4(),
        email="host@example.com",
        must_change_password=True,
        structure_id=structure_id,
        is_active=True,
        avatar_path=None,
    )


def test_host_me_returns_profile():
    structure_id = uuid.uuid4()
    host = _fake_host(structure_id)
    unit = Unit(id=uuid.uuid4(), structure_id=structure_id, name="Apt 1")
    structure = Structure(
        id=structure_id, name="Casa Blu", country_language="it", owner_contact="x"
    )

    app.dependency_overrides[require_host] = lambda: host
    # /me loads the structure via get() and the units via execute().
    override_db(FakeDB(items=[unit], by_model={Structure: structure}))

    r = client.get("/api/host/me")
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "host@example.com"
    assert body["structure_name"] == "Casa Blu"
    assert [u["name"] for u in body["units"]] == ["Apt 1"]
    assert body["must_change_password"] is True


def test_host_me_avatar_without_token_401():
    r = client.post("/api/host/me/avatar", files={"file": ("a.png", b"x", "image/png")})
    assert r.status_code == 401


def test_host_me_avatar_upload_rejects_bad_content_type(tmp_path, monkeypatch):
    from app.services import avatars

    monkeypatch.setattr(avatars, "AVATAR_DIR", tmp_path)

    structure_id = uuid.uuid4()
    host = _fake_host(structure_id)
    unit = Unit(id=uuid.uuid4(), structure_id=structure_id, name="Apt 1")
    structure = Structure(
        id=structure_id, name="Casa Blu", country_language="it", owner_contact="x"
    )
    app.dependency_overrides[require_host] = lambda: host
    override_db(FakeDB(items=[unit], by_model={Structure: structure}))

    r = client.post(
        "/api/host/me/avatar", files={"file": ("a.txt", b"hello", "text/plain")}
    )
    assert r.status_code == 422


def test_host_me_avatar_upload_saves_file(tmp_path, monkeypatch):
    from app.services import avatars

    monkeypatch.setattr(avatars, "AVATAR_DIR", tmp_path)

    structure_id = uuid.uuid4()
    host = _fake_host(structure_id)
    unit = Unit(id=uuid.uuid4(), structure_id=structure_id, name="Apt 1")
    structure = Structure(
        id=structure_id, name="Casa Blu", country_language="it", owner_contact="x"
    )
    app.dependency_overrides[require_host] = lambda: host
    override_db(FakeDB(items=[unit], by_model={Structure: structure}))

    r = client.post(
        "/api/host/me/avatar", files={"file": ("a.png", b"\x89PNG", "image/png")}
    )
    assert r.status_code == 200
    assert r.json()["avatar_url"].startswith("/uploads/avatars/")
    assert host.avatar_path is not None
    assert len(list(tmp_path.iterdir())) == 1


def test_host_faqs_empty():
    host = _fake_host(uuid.uuid4())
    app.dependency_overrides[require_host] = lambda: host
    override_db(FakeDB(items=[]))

    r = client.get("/api/host/faqs")
    assert r.status_code == 200
    assert r.json() == []


# ── change-request schema: document XOR title ──────────────────────────────────

def test_change_request_requires_document_or_title():
    from pydantic import ValidationError

    from app.schemas.host import ChangeRequestCreate

    # A document-scoped request is valid and carries no title.
    did = uuid.uuid4()
    doc_req = ChangeRequestCreate(body="update wifi", document_id=did, title="ignored")
    assert doc_req.document_id == did
    assert doc_req.title is None  # title dropped for document-scoped requests

    # An "other" request is valid when it provides a title.
    other = ChangeRequestCreate(body="heating broken", title="Broken heating")
    assert other.document_id is None
    assert other.title == "Broken heating"

    # Neither a document nor a title → rejected.
    with pytest.raises(ValidationError):
        ChangeRequestCreate(body="nothing")
