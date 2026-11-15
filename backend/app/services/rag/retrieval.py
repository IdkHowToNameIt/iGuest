"""
Vector retrieval over document chunks (pgvector).

Dual-scope retrieval: for a given unit we search the unit's own chunks PLUS the
shared structure-level chunks (unit_id IS NULL), ranked by cosine distance to
the query embedding.
"""

import uuid

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import DocumentChunk


def retrieve_chunks(
    db: Session,
    unit_id: uuid.UUID,
    structure_id: uuid.UUID,
    query_embedding: list[float],
    top_k: int,
) -> list[DocumentChunk]:
    """Return the ``top_k`` chunks most similar to ``query_embedding``.

    Scope = chunks of this unit OR structure-level chunks of its structure.

    Chunks farther than ``RAG_MAX_DISTANCE`` (cosine distance) are dropped: on a
    big manual the tail of the top-k is often unrelated text, and feeding it to
    the model only invites answers stitched together from the wrong sections.
    Set ``RAG_MAX_DISTANCE=0`` to disable the filter and always take the top-k.
    """
    distance = DocumentChunk.embedding.cosine_distance(query_embedding)

    stmt = (
        select(DocumentChunk)
        .where(
            or_(
                DocumentChunk.unit_id == unit_id,
                and_(
                    DocumentChunk.structure_id == structure_id,
                    DocumentChunk.unit_id.is_(None),
                ),
            )
        )
        .order_by(distance)
        .limit(top_k)
    )
    if settings.rag_max_distance > 0:
        stmt = stmt.where(distance <= settings.rag_max_distance)
    return list(db.execute(stmt).scalars().all())
