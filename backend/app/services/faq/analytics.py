"""
Read-side helpers over the precomputed ``question_cluster`` rows.

The recompute script (``faq.service``) writes one row per question cluster with
a ``category_label``, count and share. These helpers shape those rows for the
two read surfaces — the admin/host analytics drill-down and the guest FAQ menu —
without touching the model SDK (pure DB reads).
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import QuestionCluster, Unit


@dataclass
class QuestionStat:
    question: str
    count: int
    share: float


@dataclass
class CategoryStat:
    label: str
    count: int
    share: float
    questions: list[QuestionStat]


@dataclass
class UnitAnalytics:
    total: int
    categories: list[CategoryStat]


def _analytics_from_clusters(clusters: list[QuestionCluster]) -> UnitAnalytics:
    """Group clusters by category, ordered by descending volume.

    ``total`` is the number of guest questions the clusters were built from (the
    sum of per-cluster counts); shares are recomputed against that total so they
    stay consistent when clusters are aggregated across multiple units.
    """
    total = sum(c.question_count for c in clusters)

    by_category: dict[str, list[QuestionCluster]] = {}
    for c in clusters:
        by_category.setdefault(c.category_label, []).append(c)

    def share_of(count: int) -> float:
        return count / total if total else 0.0

    categories: list[CategoryStat] = []
    for label, members in by_category.items():
        questions = sorted(
            (
                QuestionStat(m.representative_question, m.question_count, share_of(m.question_count))
                for m in members
            ),
            key=lambda q: q.count,
            reverse=True,
        )
        cat_count = sum(m.question_count for m in members)
        categories.append(
            CategoryStat(
                label=label,
                count=cat_count,
                share=share_of(cat_count),
                questions=questions,
            )
        )

    categories.sort(key=lambda c: c.count, reverse=True)
    return UnitAnalytics(total=total, categories=categories)


def build_unit_analytics(db: Session, unit_id: uuid.UUID) -> UnitAnalytics:
    """Question analytics for a single unit (admin per-unit drill-down)."""
    clusters = (
        db.execute(select(QuestionCluster).where(QuestionCluster.unit_id == unit_id))
        .scalars()
        .all()
    )
    return _analytics_from_clusters(list(clusters))


def build_structure_analytics(db: Session, structure_id: uuid.UUID) -> UnitAnalytics:
    """Question analytics aggregated across all units of a structure (host view)."""
    clusters = (
        db.execute(
            select(QuestionCluster)
            .join(Unit, QuestionCluster.unit_id == Unit.id)
            .where(Unit.structure_id == structure_id)
        )
        .scalars()
        .all()
    )
    return _analytics_from_clusters(list(clusters))


def build_global_analytics(db: Session) -> UnitAnalytics:
    """Question analytics aggregated across every unit (admin dashboard view).

    Groups all guest questions into topic categories so the admin can see, at a
    glance, what guests ask most across all properties.
    """
    clusters = db.execute(select(QuestionCluster)).scalars().all()
    return _analytics_from_clusters(list(clusters))


@dataclass
class FaqEntry:
    rank: int
    question: str
    answer: str
    answer_language: str | None


def list_unit_faqs(db: Session, unit_id: uuid.UUID) -> list[FaqEntry]:
    """Top-N FAQ entries for a unit (those the recompute script answered)."""
    clusters = (
        db.execute(
            select(QuestionCluster)
            .where(
                QuestionCluster.unit_id == unit_id,
                QuestionCluster.faq_rank.is_not(None),
                QuestionCluster.faq_answer.is_not(None),
            )
            .order_by(QuestionCluster.faq_rank)
        )
        .scalars()
        .all()
    )
    return [
        FaqEntry(
            rank=c.faq_rank,
            question=c.representative_question,
            answer=c.faq_answer,
            answer_language=c.faq_answer_language,
        )
        for c in clusters
    ]


def list_structure_faqs(db: Session, structure_id: uuid.UUID) -> list[FaqEntry]:
    """Top FAQ entries across all units of a structure (host view).

    FAQ ranks are computed per unit, so across a multi-unit structure we re-rank
    by question volume and cap at ``faq_top_n`` to keep the list focused.
    """
    clusters = (
        db.execute(
            select(QuestionCluster)
            .join(Unit, QuestionCluster.unit_id == Unit.id)
            .where(
                Unit.structure_id == structure_id,
                QuestionCluster.faq_rank.is_not(None),
                QuestionCluster.faq_answer.is_not(None),
            )
            .order_by(QuestionCluster.question_count.desc())
        )
        .scalars()
        .all()
    )
    return [
        FaqEntry(
            rank=rank,
            question=c.representative_question,
            answer=c.faq_answer,
            answer_language=c.faq_answer_language,
        )
        for rank, c in enumerate(clusters[: settings.faq_top_n], start=1)
    ]
