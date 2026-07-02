"""Tests for the retention background scheduler (no DB, no network)."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.services import scheduler


def test_run_once_swallows_errors(monkeypatch):
    def boom():
        raise RuntimeError("db down")

    monkeypatch.setattr(scheduler, "_purge_job", boom)
    # Must not raise even when the purge job fails
    asyncio.run(scheduler._run_once())


def test_retention_loop_runs_then_stops(monkeypatch):
    calls = []
    monkeypatch.setattr(scheduler, "_purge_job", lambda: (calls.append(1), 0)[1])
    monkeypatch.setattr(settings, "retention_purge_interval_seconds", 0.02)

    async def run():
        stop = asyncio.Event()
        task = asyncio.create_task(scheduler.retention_loop(stop))
        await asyncio.sleep(0.07)
        stop.set()
        await task

    asyncio.run(run())
    # initial run + at least one interval run
    assert len(calls) >= 2
