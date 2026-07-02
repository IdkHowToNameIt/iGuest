"""
HTTP-layer tests for the public API (no DB, no network).

Covers the landing-page "book a visit" submission: validation and the happy
path, using a dependency-overridden fake DB session.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import get_db
from app.main import app


class FakeDB:
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


VALID = {
    "structure_name": "Casa Marina",
    "city": "Firenze",
    "business_type": "bnb_hotel",
    "contact_name": "Marco Rossi",
    "contact_email": "marco@example.com",
    "preferred_date": "2026-08-01",
}


def test_submit_visit_request_ok():
    override_db(FakeDB())
    r = client.post("/api/public/visit-requests", json=VALID)
    assert r.status_code == 201
    assert r.json() == {"ok": True}


def test_submit_visit_request_minimal_ok():
    override_db(FakeDB())
    r = client.post(
        "/api/public/visit-requests",
        json={
            "structure_name": "Loft",
            "contact_name": "Ann",
            "contact_email": "ann@example.com",
        },
    )
    assert r.status_code == 201


def test_submit_visit_request_missing_fields_422():
    override_db(FakeDB())
    r = client.post("/api/public/visit-requests", json={"city": "Roma"})
    assert r.status_code == 422


def test_submit_visit_request_bad_email_422():
    override_db(FakeDB())
    r = client.post(
        "/api/public/visit-requests",
        json={**VALID, "contact_email": "not-an-email"},
    )
    assert r.status_code == 422


def test_submit_visit_request_bad_business_type_422():
    override_db(FakeDB())
    r = client.post(
        "/api/public/visit-requests",
        json={**VALID, "business_type": "other"},
    )
    assert r.status_code == 422
