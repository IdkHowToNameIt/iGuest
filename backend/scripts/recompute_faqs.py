#!/usr/bin/env python
"""Recompute the FAQ / question-analytics clusters.

Embeds guest questions, clusters them, and regenerates the top-N FAQ answers
for every unit (or a single unit with ``--unit-id``). Run off the request path,
e.g. from cron / Task Scheduler:

    python scripts/recompute_faqs.py
    python scripts/recompute_faqs.py --unit-id <uuid>

Prints a one-line summary per unit. Requires the Gemini API key (embeddings +
generation) in the environment, like the ingestion pipeline.
"""

import argparse
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Unit
from app.services.faq import recompute_all_faqs, recompute_unit_faqs


def main() -> None:
    parser = argparse.ArgumentParser(description="Recompute FAQ clusters and answers.")
    parser.add_argument(
        "--unit-id", type=uuid.UUID, default=None, help="Only recompute this unit."
    )
    args = parser.parse_args()

    with SessionLocal() as db:
        if args.unit_id is not None:
            unit = db.get(Unit, args.unit_id)
            if unit is None:
                print(f"Unit {args.unit_id} not found.")
                sys.exit(1)
            results = [recompute_unit_faqs(db, unit)]
        else:
            results = recompute_all_faqs(db)

    if not results:
        print("No units to process.")
        return
    for r in results:
        print(
            f"unit={r.unit_id} questions={r.questions} "
            f"clusters={r.clusters} faq_generated={r.faq_generated}"
        )


if __name__ == "__main__":
    main()
