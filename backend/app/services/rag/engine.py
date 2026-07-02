"""
RAG engine orchestration.

Ties together: resolve the unit → embed the question → retrieve dual-scope
chunks → build the prompt → generate the answer. The embedding and generation
functions are injectable (``embed_fn`` / ``generate_fn``) so the orchestration
can be unit-tested without the live model; ``retrieve_chunks`` is imported as a
module global so tests can monkeypatch it.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Unit
from app.services.rag.embedding import embed_query
from app.services.rag.generation import generate_answer
from app.services.rag.prompt import ChunkContext, build_prompt, resolve_owner_contact
from app.services.rag.retrieval import retrieve_chunks


class UnitNotFoundError(Exception):
    """Raised when the unit referenced by a guest link no longer exists."""


@dataclass
class RagResult:
    answer: str
    detected_language: str | None
    chunk_ids: list[uuid.UUID]


def answer_question(
    db: Session,
    unit_id: uuid.UUID,
    message: str,
    *,
    embed_fn=embed_query,
    generate_fn=generate_answer,
    top_k: int | None = None,
) -> RagResult:
    """Answer a guest's ``message`` for the given unit using dual-scope RAG.

    Args:
        embed_fn: maps the message to a query embedding (injectable for tests).
        generate_fn: maps the prompt to ``{"answer", "detected_language"}``.
        top_k: number of chunks to retrieve (defaults to ``settings.rag_top_k``).

    Raises:
        UnitNotFoundError: the unit does not exist.
    """
    unit = db.get(Unit, unit_id)
    if unit is None:
        raise UnitNotFoundError(f"Unit {unit_id} not found")

    structure = unit.structure
    owner_contact = resolve_owner_contact(unit.owner_contact, structure.owner_contact)

    query_embedding = embed_fn(message)
    k = top_k if top_k is not None else settings.rag_top_k
    chunks = retrieve_chunks(db, unit.id, unit.structure_id, query_embedding, k)

    contexts = [ChunkContext(content=c.content) for c in chunks]
    prompt = build_prompt(message, contexts, owner_contact)

    result = generate_fn(prompt)

    return RagResult(
        answer=result.get("answer", ""),
        detected_language=result.get("detected_language"),
        chunk_ids=[c.id for c in chunks],
    )
