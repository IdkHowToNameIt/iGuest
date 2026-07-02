#!/usr/bin/env python
"""Quick-start seed for a local demo.

Creates one structure, one unit and an active guest link, then prints the guest
chat URL. Optionally ingests a document you provide. It does NOT invent any
content: you pass your own structure name, country language, owner contact and
(optionally) a real manual file.

Usage (from backend/, with .env configured and `alembic upgrade head` done):

    python scripts/demo_seed.py \
        --name "My B&B" \
        --country-language it \
        --owner-contact "info@mybnb.example" \
        --unit-name "Room 1" \
        --document /path/to/your/manual.pdf

Required: --name, --country-language, --owner-contact.
--document is optional and requires GEMINI_API_KEY (it runs ingestion).
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Structure, Unit
from app.services.admin_documents import create_and_ingest_document
from app.services.links import create_guest_link


def main() -> None:
    # Non-ASCII output (→, —) crashes on Windows' default cp1252 console; force UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Seed a demo structure + unit + link.")
    parser.add_argument("--name", required=True, help="Structure name")
    parser.add_argument("--country-language", required=True, help="BCP-47 code, e.g. it, en, fr")
    parser.add_argument("--owner-contact", required=True, help="Host contact (email/phone)")
    parser.add_argument("--unit-name", default="Unit 1", help="Unit label (default: 'Unit 1')")
    parser.add_argument("--document", help="Optional path to a manual to ingest (unit scope)")
    parser.add_argument(
        "--frontend-url",
        default="http://localhost:5173",
        help="Frontend origin for the guest link (default: http://localhost:5173)",
    )
    args = parser.parse_args()

    with SessionLocal() as db:
        structure = Structure(
            name=args.name,
            country_language=args.country_language,
            owner_contact=args.owner_contact,
        )
        db.add(structure)
        db.flush()

        unit = Unit(structure_id=structure.id, name=args.unit_name)
        db.add(unit)
        db.commit()
        db.refresh(structure)
        db.refresh(unit)

        print(f"Structure created: {structure.name} ({structure.id})")
        print(f"Unit created:      {unit.name} ({unit.id})")

        if args.document:
            path = Path(args.document)
            if not path.exists():
                print(f"WARNING: document not found: {path} — skipping ingestion.")
            else:
                doc = create_and_ingest_document(
                    db, "unit", structure.id, unit.id, path.name, path.read_bytes()
                )
                print(f"Document ingested: {doc.original_filename} → status={doc.status}")
                if doc.status == "error":
                    print(f"  (ingestion error: {doc.error_message})")

        link = create_guest_link(db, unit.id)
        guest_url = f"{args.frontend_url.rstrip('/')}/c/{link.token}"

        print("\nGuest link (open in a browser):")
        print(f"  {guest_url}")
        print("\nDone.")


if __name__ == "__main__":
    main()
