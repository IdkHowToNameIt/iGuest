"""Unit tests for the bilingual opening message builder."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.opening import build_opening


class TestBuildOpening:
    def test_italian_structure(self):
        op = build_opening("it", "host@example.com", 30)
        assert op.primary_language == "it"
        assert "assistente virtuale" in op.primary_message.lower()
        # English version is always provided separately
        assert "virtual assistant" in op.english_message.lower()

    def test_auto_detect_note_present(self):
        op = build_opening("it", "host@example.com", 30)
        assert "lingua" in op.language_note.lower()

    def test_privacy_notice_includes_retention_and_contact(self):
        op = build_opening("en", "host@example.com", 45)
        assert "45" in op.privacy_notice
        assert "host@example.com" in op.privacy_notice
        assert "AI" in op.privacy_notice or "Gemini" in op.privacy_notice

    def test_unknown_language_falls_back_to_english(self):
        op = build_opening("jp", "host@example.com", 30)
        assert op.primary_language == "en"
        assert op.primary_message == op.english_message

    def test_locale_tag_is_normalized(self):
        op = build_opening("it-IT", "host@example.com", 30)
        assert op.primary_language == "it"

    def test_english_structure_both_messages_english(self):
        op = build_opening("en", "host@example.com", 30)
        assert op.primary_language == "en"
        assert "virtual assistant" in op.primary_message.lower()

    def test_stay_notice_localized_and_mentions_deletion(self):
        it = build_opening("it", "host@example.com", 30)
        assert "soggiorno" in it.stay_notice.lower()
        assert "revoc" in it.stay_notice.lower()
        # Unknown language falls back to the English stay notice.
        jp = build_opening("jp", "host@example.com", 30)
        assert "stay" in jp.stay_notice.lower()
