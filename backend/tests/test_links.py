"""
Unit tests for capability-link logic (token generation + validity).

The validity rules — valid / revoked / expired / not-yet-valid — are tested
directly against `check_link_validity` with lightweight stand-in objects, so
no database is required.
"""

import sys
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.base import utcnow
from app.services.links import (
    LinkExpiredError,
    LinkNotYetValidError,
    LinkRevokedError,
    check_link_validity,
    delete_link,
    generate_token,
)


def make_link(status="active", valid_from=None, valid_until=None):
    return SimpleNamespace(status=status, valid_from=valid_from, valid_until=valid_until)


# ── token generation ─────────────────────────────────────────────────────────

class TestGenerateToken:
    def test_tokens_are_long(self):
        # 32 random bytes → ~43 url-safe chars
        assert len(generate_token()) >= 40

    def test_tokens_are_unique(self):
        tokens = {generate_token() for _ in range(1000)}
        assert len(tokens) == 1000

    def test_tokens_are_url_safe(self):
        token = generate_token()
        assert all(c.isalnum() or c in "-_" for c in token)


# ── validity ──────────────────────────────────────────────────────────────────

class TestCheckLinkValidity:
    def test_valid_link_no_window_passes(self):
        # Should not raise
        check_link_validity(make_link())

    def test_valid_link_inside_window_passes(self):
        now = utcnow()
        link = make_link(valid_from=now - timedelta(days=1), valid_until=now + timedelta(days=1))
        check_link_validity(link, now=now)

    def test_revoked_link_raises(self):
        with pytest.raises(LinkRevokedError):
            check_link_validity(make_link(status="revoked"))

    def test_expired_link_raises(self):
        now = utcnow()
        link = make_link(valid_until=now - timedelta(hours=1))
        with pytest.raises(LinkExpiredError):
            check_link_validity(link, now=now)

    def test_not_yet_valid_link_raises(self):
        now = utcnow()
        link = make_link(valid_from=now + timedelta(hours=1))
        with pytest.raises(LinkNotYetValidError):
            check_link_validity(link, now=now)

    def test_revoked_takes_precedence_over_window(self):
        now = utcnow()
        link = make_link(
            status="revoked",
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=1),
        )
        with pytest.raises(LinkRevokedError):
            check_link_validity(link, now=now)

    def test_error_codes(self):
        assert LinkRevokedError().code == "revoked"
        assert LinkExpiredError().code == "expired"
        assert LinkNotYetValidError().code == "not_yet_valid"


# ── revocation = deletion ─────────────────────────────────────────────────────

class TestDeleteLink:
    def test_revoke_deletes_the_link(self):
        deleted = []

        class FakeDB:
            def delete(self, obj):
                deleted.append(obj)

            def commit(self):
                pass

        link = SimpleNamespace(status="active", conversations=[object()])

        delete_link(FakeDB(), link)

        # The link itself is deleted (conversations/messages cascade in the DB).
        assert deleted == [link]
