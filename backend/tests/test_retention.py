"""
Unit tests for GDPR retention date logic (no DB).

The DB-level purge is exercised by the opt-in integration test
(test_guest_flow_db.py); here we verify the pure policy functions.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.retention import compute_delete_after, is_conversation_expired


class TestComputeDeleteAfter:
    def test_default_retention_is_30_days(self):
        created = datetime(2026, 1, 1, tzinfo=timezone.utc)
        # explicit retention to keep the test independent of env config
        assert compute_delete_after(created, retention_days=30) == created + timedelta(days=30)

    def test_custom_retention(self):
        created = datetime(2026, 1, 1, tzinfo=timezone.utc)
        assert compute_delete_after(created, retention_days=7) == created + timedelta(days=7)


class TestIsConversationExpired:
    def test_none_never_expires(self):
        assert is_conversation_expired(None) is False

    def test_past_delete_after_is_expired(self):
        now = datetime(2026, 6, 1, tzinfo=timezone.utc)
        delete_after = now - timedelta(days=1)
        assert is_conversation_expired(delete_after, now=now) is True

    def test_future_delete_after_is_not_expired(self):
        now = datetime(2026, 6, 1, tzinfo=timezone.utc)
        delete_after = now + timedelta(days=1)
        assert is_conversation_expired(delete_after, now=now) is False

    def test_exact_boundary_is_expired(self):
        now = datetime(2026, 6, 1, tzinfo=timezone.utc)
        assert is_conversation_expired(now, now=now) is True
