"""
Unit tests for the pure prompt/contact functions of the RAG engine.

No DB, no network — these verify that the behavioural rules and the
owner-contact fallback logic are encoded correctly in the prompt.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rag.prompt import (
    ChunkContext,
    build_context,
    build_prompt,
    resolve_owner_contact,
)


class TestResolveOwnerContact:
    def test_unit_contact_overrides_structure(self):
        assert resolve_owner_contact("unit@x.com", "struct@x.com") == "unit@x.com"

    def test_falls_back_to_structure_when_unit_none(self):
        assert resolve_owner_contact(None, "struct@x.com") == "struct@x.com"

    def test_falls_back_when_unit_empty_or_whitespace(self):
        assert resolve_owner_contact("", "struct@x.com") == "struct@x.com"
        assert resolve_owner_contact("   ", "struct@x.com") == "struct@x.com"

    def test_strips_whitespace(self):
        assert resolve_owner_contact("  unit@x.com  ", "s") == "unit@x.com"


class TestBuildContext:
    def test_empty_returns_sentinel(self):
        ctx = build_context([])
        assert "Nessun documento" in ctx

    def test_joins_chunks_with_labels(self):
        chunks = [ChunkContext(content="Check-in 15:00"), ChunkContext(content="WiFi: casa123")]
        ctx = build_context(chunks)
        assert "Check-in 15:00" in ctx
        assert "WiFi: casa123" in ctx
        assert "[Documento 1]" in ctx
        assert "[Documento 2]" in ctx


class TestBuildPrompt:
    def test_contains_all_five_rules(self):
        prompt = build_prompt("Ciao", [], "owner@x.com")
        # Rule keywords from the system instructions
        assert "LINGUA" in prompt
        assert "SOLO CONTESTO" in prompt
        assert "contattare il titolare" in prompt
        assert "non riguarda la struttura" in prompt.lower() or "NON PERTINENTE" in prompt
        assert "dati personali" in prompt

    def test_includes_owner_contact(self):
        prompt = build_prompt("Ciao", [], "owner@example.com")
        assert "owner@example.com" in prompt

    def test_includes_message_and_context(self):
        chunks = [ChunkContext(content="La piscina apre alle 9.")]
        prompt = build_prompt("A che ora apre la piscina?", chunks, "o@x.com")
        assert "La piscina apre alle 9." in prompt
        assert "A che ora apre la piscina?" in prompt

    def test_requests_json_output(self):
        prompt = build_prompt("Ciao", [], "o@x.com")
        assert "detected_language" in prompt
        assert "answer" in prompt
