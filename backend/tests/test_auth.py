"""Unit tests for admin authentication logic (no DB, no network)."""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.services.auth import (
    AuthError,
    create_access_token,
    decode_token,
    verify_credentials,
)


class TestVerifyCredentials:
    def test_correct_credentials(self):
        assert verify_credentials(settings.admin_username, settings.admin_password) is True

    def test_wrong_password(self):
        assert verify_credentials(settings.admin_username, "definitely-wrong") is False

    def test_wrong_username(self):
        assert verify_credentials("not-the-admin", settings.admin_password) is False


class TestToken:
    def test_roundtrip(self):
        token = create_access_token()
        payload = decode_token(token)
        assert payload["sub"] == settings.admin_username
        assert "exp" in payload

    def test_expired_token_raises(self):
        past = datetime.now(timezone.utc) - timedelta(minutes=settings.admin_token_expire_minutes + 10)
        token = create_access_token(now=past)
        with pytest.raises(AuthError):
            decode_token(token)

    def test_invalid_token_raises(self):
        with pytest.raises(AuthError):
            decode_token("not.a.valid.jwt")

    def test_tampered_token_raises(self):
        token = create_access_token()
        tampered = token[:-2] + ("aa" if not token.endswith("aa") else "bb")
        with pytest.raises(AuthError):
            decode_token(tampered)
