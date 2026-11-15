"""
Tests for the RAG engine orchestration, covering the four required behaviours:
  1. answer found in context
  2. relevant question but answer missing → owner contact
  3. off-topic question → polite refusal
  4. message in a different language → answer in that language

The embedding and generation calls are injected; retrieve_chunks is monkeypatched.
This isolates our orchestration + prompt wiring from the live model. The generator
fakes simulate a model that *correctly follows* the prompt rules, and we assert that
the engine feeds it the data each rule needs (context, owner contact).

A live end-to-end check against the real model is provided separately and only runs
when GEMINI_API_KEY is set (see test_rag_live, skipped by default).
"""

import os
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rag import engine as engine_module
from app.services.rag.engine import RagResult, UnitNotFoundError, answer_question


# ── fakes ──────────────────────────────────────────────────────────────────────

class FakeDB:
    """Minimal stand-in for a SQLAlchemy Session supporting .get(Model, id)."""

    def __init__(self, unit):
        self._unit = unit

    def get(self, model, pk):
        # The engine only ever calls db.get(Unit, unit_id)
        return self._unit


def make_unit(unit_owner_contact=None, structure_owner_contact="owner@struct.com"):
    structure = SimpleNamespace(
        id=uuid.uuid4(),
        owner_contact=structure_owner_contact,
    )
    unit = SimpleNamespace(
        id=uuid.uuid4(),
        structure_id=structure.id,
        owner_contact=unit_owner_contact,
        structure=structure,
    )
    return unit


def make_chunk(content):
    return SimpleNamespace(id=uuid.uuid4(), content=content)


def fake_embed(_message):
    # Shape doesn't matter — retrieve_chunks is mocked
    return [0.0] * 768


def patch_retrieval(monkeypatch, chunks):
    monkeypatch.setattr(
        engine_module, "retrieve_chunks",
        lambda db, unit_id, structure_id, query_embedding, top_k: chunks,
    )


# ── scenario 1: answer found ─────────────────────────────────────────────────

def test_answer_found_in_context(monkeypatch):
    unit = make_unit()
    chunks = [make_chunk("Il check-in è alle 15:00."), make_chunk("Il WiFi è 'casa123'.")]
    patch_retrieval(monkeypatch, chunks)

    captured = {}

    def fake_generate(prompt):
        captured["prompt"] = prompt
        return {"answer": "Il check-in è alle 15:00.", "detected_language": "it"}

    result = answer_question(
        FakeDB(unit), unit.id, "A che ora è il check-in?",
        embed_fn=fake_embed, generate_fn=fake_generate,
    )

    assert isinstance(result, RagResult)
    assert "15:00" in result.answer
    assert result.detected_language == "it"
    assert len(result.chunk_ids) == 2
    # The engine must feed retrieved context into the prompt
    assert "Il check-in è alle 15:00." in captured["prompt"]


# ── scenario 2: relevant but missing → owner contact ─────────────────────────

def test_relevant_but_missing_provides_owner_contact(monkeypatch):
    # No relevant chunk retrieved for this property question
    unit = make_unit(unit_owner_contact=None, structure_owner_contact="host@property.com")
    patch_retrieval(monkeypatch, [])

    captured = {}

    def fake_generate(prompt):
        captured["prompt"] = prompt
        # Simulate the model following rule 3
        return {
            "answer": "Non ho questa informazione. Contatta il titolare: host@property.com",
            "detected_language": "it",
        }

    result = answer_question(
        FakeDB(unit), unit.id, "È ammesso portare animali domestici?",
        embed_fn=fake_embed, generate_fn=fake_generate,
    )

    # The owner contact must be present in the prompt so the model can apply rule 3
    assert "host@property.com" in captured["prompt"]
    assert "host@property.com" in result.answer


def test_owner_contact_unit_override_used_in_prompt(monkeypatch):
    unit = make_unit(unit_owner_contact="unit-host@x.com", structure_owner_contact="struct@x.com")
    patch_retrieval(monkeypatch, [])

    captured = {}

    def fake_generate(prompt):
        captured["prompt"] = prompt
        return {"answer": "...", "detected_language": "it"}

    answer_question(
        FakeDB(unit), unit.id, "Domanda senza risposta nel manuale?",
        embed_fn=fake_embed, generate_fn=fake_generate,
    )

    # Unit-level contact overrides the structure-level one
    assert "unit-host@x.com" in captured["prompt"]
    assert "struct@x.com" not in captured["prompt"]


# ── scenario 3: off-topic → refusal ──────────────────────────────────────────

def test_off_topic_question_is_refused(monkeypatch):
    unit = make_unit()
    patch_retrieval(monkeypatch, [make_chunk("Info sulla struttura.")])

    captured = {}

    def fake_generate(prompt):
        captured["prompt"] = prompt
        return {
            "answer": "Posso rispondere solo a domande relative a questa struttura.",
            "detected_language": "it",
        }

    result = answer_question(
        FakeDB(unit), unit.id, "Chi ha vinto i mondiali nel 2006?",
        embed_fn=fake_embed, generate_fn=fake_generate,
    )

    # The refusal rule must be present in the instructions
    assert "solo domande relative" in captured["prompt"]
    assert "solo a domande relative" in result.answer


# ── scenario 4: different language ───────────────────────────────────────────

def test_responds_in_detected_language(monkeypatch):
    unit = make_unit()
    patch_retrieval(monkeypatch, [make_chunk("L'enregistrement est à 15h00.")])

    def fake_generate(prompt):
        # Model detects French and answers in French
        return {"answer": "L'enregistrement est à 15h00.", "detected_language": "fr"}

    result = answer_question(
        FakeDB(unit), unit.id, "À quelle heure est l'enregistrement ?",
        embed_fn=fake_embed, generate_fn=fake_generate,
    )

    assert result.detected_language == "fr"
    assert "enregistrement" in result.answer


# ── error handling ───────────────────────────────────────────────────────────

def test_unknown_unit_raises():
    class EmptyDB:
        def get(self, model, pk):
            return None

    with pytest.raises(UnitNotFoundError):
        answer_question(
            EmptyDB(), uuid.uuid4(), "Ciao",
            embed_fn=fake_embed, generate_fn=lambda p: {"answer": "x", "detected_language": "it"},
        )


# ── optional live integration test (skipped unless GEMINI_API_KEY is set) ────

def _is_transient_provider_error(exc: Exception) -> bool:
    """Quota/overload errors say nothing about our code: skip, don't fail."""
    return getattr(exc, "code", None) in {429, 503, 504} or any(
        marker in str(exc)
        for marker in ("RESOURCE_EXHAUSTED", "UNAVAILABLE", "DEADLINE_EXCEEDED")
    )


@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="requires GEMINI_API_KEY")
def test_generation_parsing_live():
    """Sanity check that the real generator returns the expected dict shape.
    Only runs when an API key is configured; safe to skip in CI."""
    from app.services.rag.generation import generate_answer
    from app.services.rag.prompt import ChunkContext, build_prompt

    prompt = build_prompt(
        "What time is check-in?",
        [ChunkContext(content="Check-in is at 3 PM.")],
        "owner@example.com",
    )
    try:
        result = generate_answer(prompt)
    except Exception as exc:
        if _is_transient_provider_error(exc):
            pytest.skip(f"Gemini temporarily unavailable: {str(exc)[:80]}")
        raise
    assert "answer" in result
    assert "detected_language" in result


@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="requires GEMINI_API_KEY")
def test_generation_answers_across_languages_from_foreign_context():
    """Regression: the bot must answer in the guest's language even when the
    context (manual) is in another language — e.g. an Italian manual and a
    Chinese question. Previously ZH returned a "no information" refusal.

    Spaces calls out to respect the Gemini free-tier rate limit (5 req/min) and
    skips (rather than fails) if the quota is exhausted."""
    import time

    from google.genai.errors import ClientError

    from app.services.rag.generation import generate_answer
    from app.services.rag.prompt import ChunkContext, build_prompt

    context = [ChunkContext(content="Il check-in è alle 15:00.")]
    # A representative mix incl. non-Latin scripts, kept under the free-tier limit.
    questions = {
        "it": "A che ora è il check-in?",
        "en": "What time is check-in?",
        "zh": "几点办理入住？",
        "ar": "ما هو وقت تسجيل الوصول؟",
        "ja": "チェックインは何時ですか？",
    }
    failures = []
    for i, (lang, q) in enumerate(questions.items()):
        if i:
            time.sleep(13)  # stay under 5 requests/minute
        try:
            answer = generate_answer(build_prompt(q, context, "owner@example.com")).get("answer", "")
        except ClientError as exc:
            if "RESOURCE_EXHAUSTED" in str(exc) or "429" in str(exc):
                pytest.skip("Gemini free-tier quota exhausted")
            raise
        if "15" not in answer:  # the check-in hour survives translation
            failures.append(f"[{lang}] {answer!r}")
    assert not failures, "Lingue senza risposta corretta dal contesto:\n" + "\n".join(failures)
