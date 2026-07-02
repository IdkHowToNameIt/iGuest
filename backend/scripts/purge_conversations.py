#!/usr/bin/env python
"""GDPR retention job — delete conversations past their `delete_after`.

Run manually or from a scheduler (cron / Task Scheduler):

    python scripts/purge_conversations.py

Prints how many conversations were removed. Messages cascade-delete with them.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.services.retention import purge_expired_conversations


def main() -> None:
    with SessionLocal() as db:
        removed = purge_expired_conversations(db)
        print(f"Purged {removed} expired conversation(s).")


if __name__ == "__main__":
    main()
