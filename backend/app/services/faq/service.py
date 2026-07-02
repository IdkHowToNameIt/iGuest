"""
FAQ / question-analytics recompute pipeline.

For one unit (or all units) this:
  1. loads the guest questions,
  2. embeds the ones not embedded yet (cached on ``message.embedding``),
  3. clusters them by cosine similarity into questions, then into categories,
  4. rebuilds the unit's ``question_cluster`` rows with counts/shares,
  5. generates a FAQ answer for the top-N clusters (via the RAG engine).

Run from the scheduled script ``scripts/recompute_faqs.py`` (not on the request
path). The result feeds both the guest FAQ menu and the admin analytics view.
"""

import logging
from collections import Counter
from dataclasses import dataclass

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Conversation, Message, QuestionCluster, Unit
from app.services.faq.clustering import centroid_of, cluster

logger = logging.getLogger(__name__)


@dataclass
class FaqRecomputeResult:
    unit_id: str
    questions: int          # total guest questions considered
    clusters: int           # distinct question clusters produced
    faq_generated: int      # FAQ answers (re)generated


def _load_guest_messages(db: Session, unit_id) -> list[Message]:
    stmt = (
        select(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(Conversation.unit_id == unit_id, Message.role == "guest")
        .order_by(Message.created_at)
    )
    return list(db.execute(stmt).scalars().all())


def _ensure_embeddings(db: Session, messages: list[Message]) -> None:
    """Embed and cache any messages lacking an embedding (batched)."""
    pending = [m for m in messages if m.embedding is None]
    if not pending:
        return
    from app.services.ingestion.embedding import embed_texts

    vectors = embed_texts([m.content for m in pending], task_type="clustering")
    for msg, vec in zip(pending, vectors):
        msg.embedding = vec
    db.flush()


def _representative(group: list[Message], vectors: np.ndarray) -> str:
    """Pick the group's representative question.

    Prefer the most frequently asked exact text; on a tie (e.g. all unique
    phrasings) fall back to the medoid — the question nearest the centroid.
    """
    counts = Counter(m.content.strip() for m in group)
    text, freq = counts.most_common(1)[0]
    if freq > 1:
        return text
    norms = vectors / (np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-12)
    centroid = norms.mean(axis=0)
    medoid_idx = int(np.argmax(norms @ centroid))
    return group[medoid_idx].content.strip()


def recompute_unit_faqs(
    db: Session, unit: Unit, *, generate_fn=None
) -> FaqRecomputeResult:
    """Rebuild question clusters and FAQ answers for a single unit.

    Args:
        generate_fn: injectable RAG entry point ``(db, unit_id, question) ->
            RagResult`` (defaults to the real engine; overridable in tests).
    """
    if generate_fn is None:
        from app.services.rag import answer_question as generate_fn  # lazy: avoids SDK import

    messages = _load_guest_messages(db, unit.id)
    total = len(messages)

    # Drop existing clusters for this unit (message.faq_cluster_id is SET NULL by FK).
    db.execute(
        QuestionCluster.__table__.delete().where(QuestionCluster.unit_id == unit.id)
    )
    db.flush()

    if total == 0:
        db.commit()
        return FaqRecomputeResult(str(unit.id), 0, 0, 0)

    _ensure_embeddings(db, messages)

    embeddings = [list(m.embedding) for m in messages]
    q_labels = cluster(embeddings, settings.faq_question_distance)

    # Group messages by question-cluster label.
    groups: dict[int, list[Message]] = {}
    for msg, label in zip(messages, q_labels):
        groups.setdefault(label, []).append(msg)

    # Build per-group data: representative text, centroid, members.
    group_items = []  # (representative, centroid(list), members)
    for label, members in groups.items():
        vecs = np.asarray([m.embedding for m in members], dtype=np.float64)
        rep = _representative(members, vecs)
        group_items.append((rep, centroid_of([m.embedding for m in members]), members))

    # Category level: cluster the question-centroids; label each category by the
    # representative question of its largest member group.
    cat_labels = cluster([gi[1] for gi in group_items], settings.faq_category_distance)
    cat_to_groups: dict[int, list[int]] = {}
    for gi_idx, c in enumerate(cat_labels):
        cat_to_groups.setdefault(c, []).append(gi_idx)
    category_label_for: dict[int, str] = {}
    for c, gi_idxs in cat_to_groups.items():
        largest = max(gi_idxs, key=lambda i: len(group_items[i][2]))
        category_label_for[c] = group_items[largest][0]

    # Create the new cluster rows and re-link member messages.
    clusters: list[QuestionCluster] = []
    for gi_idx, (rep, centroid, members) in enumerate(group_items):
        qc = QuestionCluster(
            unit_id=unit.id,
            centroid=centroid,
            representative_question=rep,
            category_label=category_label_for[cat_labels[gi_idx]],
            question_count=len(members),
            share=len(members) / total,
        )
        db.add(qc)
        db.flush()  # assign id
        for m in members:
            m.faq_cluster_id = qc.id
        clusters.append(qc)

    # Top-N by count → FAQ; generate an answer for each via the RAG engine.
    ranked = sorted(clusters, key=lambda c: c.question_count, reverse=True)[: settings.faq_top_n]
    generated = 0
    for rank, qc in enumerate(ranked, start=1):
        qc.faq_rank = rank
        try:
            result = generate_fn(db, unit.id, qc.representative_question)
            qc.faq_answer = result.answer
            qc.faq_answer_language = result.detected_language
            generated += 1
        except Exception as exc:  # never let one answer abort the whole run
            logger.warning("FAQ answer generation failed for unit %s: %s", unit.id, exc)

    db.commit()
    return FaqRecomputeResult(str(unit.id), total, len(clusters), generated)


def recompute_all_faqs(db: Session, *, generate_fn=None) -> list[FaqRecomputeResult]:
    """Recompute FAQs for every unit. Returns a result per unit."""
    units = db.execute(select(Unit)).scalars().all()
    results = []
    for unit in units:
        results.append(recompute_unit_faqs(db, unit, generate_fn=generate_fn))
    return results
