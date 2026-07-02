"""
HTTP-layer tests for the admin API (no DB, no network).

Covers login, route protection (401 without/with bad token), and a few
read paths using a fake DB session. The full create→upload→link→conversation
flow against a real DB is in test_admin_flow_db.py (opt-in).
"""

import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.database import get_db
from app.main import app
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

    def scalar_one(self):
        return len(self._items)


class FakeDB:
    def __init__(self, items=None, get_value=None):
        self._items = items or []
        self._get_value = get_value

    def execute(self, *a, **k):
        return FakeResult(self._items)

    def get(self, model, pk):
        return self._get_value

    def add(self, obj):
        pass

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


def auth_header():
    return {"Authorization": f"Bearer {create_access_token()}"}


# ── login ──────────────────────────────────────────────────────────────────────

def test_login_success():
    r = client.post(
        "/api/admin/login",
        json={"username": settings.admin_username, "password": settings.admin_password},
    )
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]


def test_login_wrong_password():
    r = client.post(
        "/api/admin/login",
        json={"username": settings.admin_username, "password": "wrong"},
    )
    assert r.status_code == 401


# ── protection ───────────────────────────────────────────────────────────────────

def test_protected_route_without_token_401():
    r = client.get("/api/admin/structures")
    assert r.status_code == 401


def test_protected_route_with_bad_token_401():
    r = client.get("/api/admin/structures", headers={"Authorization": "Bearer garbage"})
    assert r.status_code == 401


def test_documents_protected():
    r = client.get("/api/admin/documents")
    assert r.status_code == 401


def test_conversations_protected():
    r = client.get(f"/api/admin/conversations/{uuid.uuid4()}")
    assert r.status_code == 401


def test_hosts_protected():
    r = client.get(f"/api/admin/structures/{uuid.uuid4()}/hosts")
    assert r.status_code == 401


def test_change_requests_protected():
    r = client.get("/api/admin/change-requests")
    assert r.status_code == 401


def test_analytics_protected():
    r = client.get(f"/api/admin/units/{uuid.uuid4()}/analytics")
    assert r.status_code == 401


def test_document_content_protected():
    r = client.get(f"/api/admin/documents/{uuid.uuid4()}/content")
    assert r.status_code == 401


def test_structure_search_filters_passthrough():
    # With a token + fake DB the filters must not error (real filtering is
    # exercised by the DB-backed flow tests).
    override_db(FakeDB(items=[]))
    r = client.get(
        "/api/admin/structures",
        params={"q": "roma", "region": "Lazio", "province": "Roma", "city": "Roma"},
        headers=auth_header(),
    )
    assert r.status_code == 200
    assert r.json() == []


def test_admin_endpoint_rejects_host_token():
    # A host token (role="host") must not pass the admin guard.
    from app.services.host_auth import create_host_token

    host = uuid.uuid4()
    token = create_host_token(type("H", (), {"id": host, "structure_id": uuid.uuid4()})())
    r = client.get("/api/admin/structures", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


# ── read paths with token + fake DB ───────────────────────────────────────────────

def test_list_structures_empty():
    override_db(FakeDB(items=[]))
    r = client.get("/api/admin/structures", headers=auth_header())
    assert r.status_code == 200
    assert r.json() == []


def test_get_structure_not_found():
    override_db(FakeDB(get_value=None))
    r = client.get(f"/api/admin/structures/{uuid.uuid4()}", headers=auth_header())
    assert r.status_code == 404


def test_upload_invalid_scope_422():
    override_db(FakeDB())
    r = client.post(
        "/api/admin/documents",
        headers=auth_header(),
        data={"scope_type": "bogus", "target_id": str(uuid.uuid4())},
        files={"file": ("test.txt", b"hello", "text/plain")},
    )
    assert r.status_code == 422


# ── admin profile / avatar / stats ────────────────────────────────────────────────

def test_stats_protected():
    r = client.get("/api/admin/stats")
    assert r.status_code == 401


def test_profile_protected():
    r = client.get("/api/admin/profile")
    assert r.status_code == 401


def test_get_stats_counts():
    override_db(FakeDB(items=[]))
    r = client.get("/api/admin/stats", headers=auth_header())
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {
        "structures",
        "units",
        "active_links",
        "open_change_requests",
        "new_visit_requests",
    }


def test_global_analytics_empty():
    override_db(FakeDB(items=[]))  # no question clusters yet
    r = client.get("/api/admin/analytics", headers=auth_header())
    assert r.status_code == 200
    body = r.json()
    assert body == {"total": 0, "categories": []}


def test_global_analytics_requires_auth():
    r = client.get("/api/admin/analytics")
    assert r.status_code == 401


def test_get_profile_creates_singleton_when_none_exists():
    override_db(FakeDB(items=[]))  # .scalars().first() -> None -> created
    r = client.get("/api/admin/profile", headers=auth_header())
    assert r.status_code == 200
    body = r.json()
    assert body["display_name"] is None
    assert body["avatar_url"] is None


def test_avatar_upload_rejects_bad_content_type(tmp_path, monkeypatch):
    from app.services import avatars

    monkeypatch.setattr(avatars, "AVATAR_DIR", tmp_path)
    override_db(FakeDB(items=[]))
    r = client.post(
        "/api/admin/profile/avatar",
        headers=auth_header(),
        files={"file": ("a.gif", b"hello", "image/gif")},
    )
    assert r.status_code == 422


def test_avatar_upload_rejects_oversized_file(tmp_path, monkeypatch):
    from app.services import avatars

    monkeypatch.setattr(avatars, "AVATAR_DIR", tmp_path)
    monkeypatch.setattr(avatars, "MAX_UPLOAD_BYTES", 4)
    override_db(FakeDB(items=[]))
    r = client.post(
        "/api/admin/profile/avatar",
        headers=auth_header(),
        files={"file": ("a.png", b"toolongforfour", "image/png")},
    )
    assert r.status_code == 422


def test_avatar_upload_saves_file(tmp_path, monkeypatch):
    from app.services import avatars

    monkeypatch.setattr(avatars, "AVATAR_DIR", tmp_path)
    override_db(FakeDB(items=[]))
    r = client.post(
        "/api/admin/profile/avatar",
        headers=auth_header(),
        files={"file": ("a.png", b"\x89PNG", "image/png")},
    )
    assert r.status_code == 200
    assert r.json()["avatar_url"].startswith("/uploads/avatars/")
    assert len(list(tmp_path.iterdir())) == 1


# ── admin accounts (additional logins, alongside the legacy .env admin) ────────────

def test_admin_accounts_protected():
    assert client.get("/api/admin/admins").status_code == 401
    assert client.post("/api/admin/admins", json={"username": "x"}).status_code == 401
    assert client.patch(f"/api/admin/admins/{uuid.uuid4()}", json={}).status_code == 401
    assert client.delete(f"/api/admin/admins/{uuid.uuid4()}").status_code == 401


def test_create_admin_reserved_username_conflict():
    # Rejected before any DB lookup: this name is the built-in .env account's.
    r = client.post(
        "/api/admin/admins",
        json={"username": settings.admin_username},
        headers=auth_header(),
    )
    assert r.status_code == 409


def test_create_admin_duplicate_username_conflict():
    override_db(FakeDB(items=[object()]))  # any truthy row = "username taken"
    r = client.post(
        "/api/admin/admins",
        json={"username": "someone"},
        headers=auth_header(),
    )
    assert r.status_code == 409


def test_delete_own_admin_account_rejected():
    admin_id = uuid.uuid4()
    fake_admin = type("AU", (), {"id": admin_id})()
    override_db(FakeDB(get_value=fake_admin))
    token = create_access_token(sub=str(admin_id))
    r = client.delete(
        f"/api/admin/admins/{admin_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 400


def test_disable_own_admin_account_rejected():
    admin_id = uuid.uuid4()
    fake_admin = type("AU", (), {"id": admin_id, "is_active": True})()
    override_db(FakeDB(get_value=fake_admin))
    token = create_access_token(sub=str(admin_id))
    r = client.patch(
        f"/api/admin/admins/{admin_id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 400


def test_change_password_protected():
    r = client.post(
        "/api/admin/change-password",
        json={"current_password": "x", "new_password": "newpassword123"},
    )
    assert r.status_code == 401


def test_change_password_rejected_for_legacy_admin():
    # The .env admin's token subject is its username, not a UUID — this must
    # be rejected cleanly rather than crash trying to parse a UUID.
    r = client.post(
        "/api/admin/change-password",
        json={"current_password": "x", "new_password": "newpassword123"},
        headers=auth_header(),
    )
    assert r.status_code == 400


def test_change_password_admin_not_found():
    override_db(FakeDB(get_value=None))
    token = create_access_token(sub=str(uuid.uuid4()))
    r = client.post(
        "/api/admin/change-password",
        json={"current_password": "x", "new_password": "newpassword123"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404
