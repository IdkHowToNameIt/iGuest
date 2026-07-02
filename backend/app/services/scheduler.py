"""
Background schedulers: GDPR retention purge + FAQ/analytics recompute.

Both run inside the FastAPI process: once on startup, then at a configurable
interval. The DB/embedding/generation work is synchronous, so it runs in a
worker thread to avoid blocking the event loop. Failures (e.g. DB temporarily
unreachable, Gemini rate limit) are logged and never crash the app or the loop.
"""

import asyncio
import logging

from app.config import settings
from app.database import SessionLocal
from app.services.retention import purge_expired_conversations

logger = logging.getLogger(__name__)


def _purge_job() -> int:
    with SessionLocal() as db:
        return purge_expired_conversations(db)


async def _run_once() -> None:
    try:
        removed = await asyncio.to_thread(_purge_job)
        if removed:
            logger.info("Retention purge removed %d expired conversation(s).", removed)
    except Exception as exc:  # never let the loop die
        logger.warning("Retention purge failed: %s", exc)


async def retention_loop(stop_event: asyncio.Event) -> None:
    """Purge once, then every `retention_purge_interval_seconds` until stopped."""
    interval = settings.retention_purge_interval_seconds
    await _run_once()
    while not stop_event.is_set():
        try:
            # Wake early if asked to stop; otherwise run after the interval.
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            await _run_once()


def _faq_recompute_job() -> int:
    # Lazy imports: avoid pulling in the Gemini SDK / numpy at module import
    # time for code paths (e.g. tests) that never start this loop.
    from app.services.faq import recompute_all_faqs

    with SessionLocal() as db:
        results = recompute_all_faqs(db)
    return sum(r.questions for r in results)


async def _run_faq_recompute_once() -> None:
    try:
        questions = await asyncio.to_thread(_faq_recompute_job)
        logger.info("FAQ recompute processed %d guest question(s).", questions)
    except Exception as exc:  # never let one bad batch kill the loop
        logger.warning("FAQ recompute failed: %s", exc)


async def faq_recompute_loop(stop_event: asyncio.Event) -> None:
    """Recompute question clusters/FAQs/analytics for every unit, on a timer.

    Without this, question_cluster rows (which back both the guest FAQ menu
    and the admin/host analytics view) only get built by manually running
    scripts/recompute_faqs.py — so nothing ever shows up on its own.
    """
    interval = settings.faq_recompute_interval_seconds
    await _run_faq_recompute_once()
    while not stop_event.is_set():
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            await _run_faq_recompute_once()
