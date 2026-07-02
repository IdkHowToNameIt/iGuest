"""
Unit tests for the FAQ read-side helpers (no DB, no network).

``build_unit_analytics`` and ``list_unit_faqs`` are fed a fake session whose
``execute`` returns prebuilt cluster rows, so we exercise the grouping/sorting
and mapping without Postgres.
"""

import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.faq.analytics import build_unit_analytics, list_unit_faqs


class _Result:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return self

    def all(self):
        return self._items


class _DB:
    def __init__(self, items):
        self._items = items

    def execute(self, *a, **k):
        return _Result(self._items)


def _cluster(question, category, count, share, rank=None, answer=None, lang=None):
    return SimpleNamespace(
        representative_question=question,
        category_label=category,
        question_count=count,
        share=share,
        faq_rank=rank,
        faq_answer=answer,
        faq_answer_language=lang,
    )


def test_build_unit_analytics_groups_and_sorts():
    clusters = [
        _cluster("Where is the key?", "Check-in", 3, 0.3),
        _cluster("What time is check-in?", "Check-in", 5, 0.5),
        _cluster("Is there wifi?", "Amenities", 2, 0.2),
    ]
    analytics = build_unit_analytics(_DB(clusters), uuid.uuid4())

    assert analytics.total == 10
    # Categories ordered by descending total count: Check-in (8) before Amenities (2).
    assert [c.label for c in analytics.categories] == ["Check-in", "Amenities"]
    checkin = analytics.categories[0]
    assert checkin.count == 8
    assert abs(checkin.share - 0.8) < 1e-9
    # Questions within a category ordered by descending count.
    assert [q.question for q in checkin.questions] == [
        "What time is check-in?",
        "Where is the key?",
    ]


def test_build_unit_analytics_empty():
    analytics = build_unit_analytics(_DB([]), uuid.uuid4())
    assert analytics.total == 0
    assert analytics.categories == []


def test_list_unit_faqs_maps_entries():
    clusters = [
        _cluster("Q1", "C", 5, 0.5, rank=1, answer="A1", lang="en"),
        _cluster("Q2", "C", 3, 0.3, rank=2, answer="A2", lang="it"),
    ]
    entries = list_unit_faqs(_DB(clusters), uuid.uuid4())
    assert [(e.rank, e.question, e.answer, e.answer_language) for e in entries] == [
        (1, "Q1", "A1", "en"),
        (2, "Q2", "A2", "it"),
    ]
