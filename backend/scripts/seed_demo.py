#!/usr/bin/env python
"""Seed a complete demo: Casa Sole B&B (Florence), two units, sample manuals.

Creates the structure with its location/contact details, both units, ingests the
four fictional manuals from ``samples/manuals/casa-sole/`` (two structure-scoped,
two unit-scoped) and creates a guest link for the Suite Giardino. Prints the
guest chat URL so you can open the demo straight away.

Usage (from backend/, database running and ``alembic upgrade head`` done):

    python scripts/seed_demo.py                # creates the demo if missing
    python scripts/seed_demo.py --reset        # drops + recreates it
    python scripts/seed_demo.py --host-email you@example.com   # + host account
    python scripts/seed_demo.py --frontend-url http://localhost:5174

Requires GEMINI_API_KEY: the manuals are embedded during ingestion, exactly like
a real upload from the admin panel. Every document must reach status
"processed", otherwise the script exits with code 1.
"""

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Structure, Unit
from app.services.admin_documents import create_and_ingest_document
from app.services.links import create_guest_link
from app.services.passwords import generate_temp_password, hash_password
from app.models import Host

# Local runs see <repo>/samples; in Docker only ./backend is mounted, so the
# compose file mounts ./samples at /samples (read-only) instead.
_SAMPLES_CANDIDATES = [
    BACKEND_DIR.parent / "samples" / "manuals" / "casa-sole",
    Path("/samples/manuals/casa-sole"),
]
DEFAULT_SAMPLES_DIR = next(
    (p for p in _SAMPLES_CANDIDATES if p.exists()), _SAMPLES_CANDIDATES[0]
)

STRUCTURE_NAME = "Casa Sole"
STRUCTURE_DOCS = ["house-rules.it.md", "local-guide.it.md"]
# unit name -> documents uploaded at unit scope
UNIT_DOCS = {
    "Suite Giardino": ["suite-giardino.it.md"],
    "Camera Oliva": ["olive-room.en.md"],
}

WELCOME_MESSAGE = (
    "Ciao! Sono l'assistente di Casa Sole. Chiedimi qualsiasi cosa sull'alloggio "
    "— orari, Wi-Fi, colazione, parcheggio, ristoranti in zona — e ti rispondo "
    "nella tua lingua."
)

DEMO_EMAIL = "marco.rossi@casasole.example"


def _ingest(db, scope_type: str, structure_id, unit_id, filename: str):
    path = SAMPLES_DIR / filename
    if not path.exists():
        raise SystemExit(f"Sample manual not found: {path}")

    document = create_and_ingest_document(
        db, scope_type, structure_id, unit_id, path.name, path.read_bytes()
    )
    scope = "structure" if unit_id is None else "unit"
    status = document.status
    n_chunks = len(document.chunks)
    icon = "OK " if status == "processed" else "ERR"
    print(f"  [{icon}] {filename:<24} scope={scope:<9} status={status:<9} chunks={n_chunks}")
    if status != "processed":
        print(f"        reason: {document.error_message}")
    return status


def main() -> None:
    # Non-ASCII output (→, —) crashes on Windows' default cp1252 console; force UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Seed the Casa Sole demo data.")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate the demo")
    parser.add_argument(
        "--frontend-url",
        default="http://localhost:5174",
        help="Frontend origin for the printed guest link (default: http://localhost:5174)",
    )
    parser.add_argument(
        "--host-email",
        help="Optional: create a host account for the structure and print its temporary password",
    )
    parser.add_argument(
        "--samples-dir",
        default=str(DEFAULT_SAMPLES_DIR),
        help="Folder with the sample manuals (default: samples/manuals/casa-sole)",
    )
    args = parser.parse_args()

    global SAMPLES_DIR, STRUCTURE_DOCS, UNIT_DOCS
    SAMPLES_DIR = Path(args.samples_dir)
    if not SAMPLES_DIR.exists():
        raise SystemExit(f"Samples folder not found: {SAMPLES_DIR}")

    with SessionLocal() as db:
        existing = (
            db.execute(select(Structure).where(Structure.name == STRUCTURE_NAME))
            .scalars()
            .first()
        )
        if existing is not None:
            if not args.reset:
                print(
                    f"'{STRUCTURE_NAME}' already exists (id={existing.id}).\n"
                    "Use --reset to delete and recreate it."
                )
                return
            print(f"Removing existing '{STRUCTURE_NAME}' (cascade)…")
            db.delete(existing)
            db.commit()

        structure = Structure(
            name=STRUCTURE_NAME,
            country_language="it",
            owner_contact=DEMO_EMAIL,
            welcome_message=WELCOME_MESSAGE,
            region="Toscana",
            province="Firenze",
            city="Firenze",
            contact_name="Marco Rossi",
            contact_phone="+39 055 1234567",
            contact_email=DEMO_EMAIL,
        )
        db.add(structure)
        db.commit()
        db.refresh(structure)
        print(f"Structure: {structure.name} ({structure.id})")

        units: dict[str, Unit] = {}
        for name in UNIT_DOCS:
            unit = Unit(structure_id=structure.id, name=name)
            db.add(unit)
            db.commit()
            db.refresh(unit)
            units[name] = unit
            print(f"Unit:      {unit.name} ({unit.id})")

        print("\nIngesting sample manuals (Gemini embeddings)…")
        statuses = []
        for filename in STRUCTURE_DOCS:
            statuses.append(_ingest(db, "structure", structure.id, None, filename))
        for unit_name, filenames in UNIT_DOCS.items():
            for filename in filenames:
                statuses.append(
                    _ingest(db, "unit", structure.id, units[unit_name].id, filename)
                )

        if args.host_email:
            password = generate_temp_password()
            db.add(
                Host(
                    structure_id=structure.id,
                    email=args.host_email,
                    password_hash=hash_password(password),
                    must_change_password=True,
                )
            )
            db.commit()
            print(f"\nHost account: {args.host_email}")
            print(f"Temporary password (shown once): {password}")

        link = create_guest_link(db, units["Suite Giardino"].id)
        guest_url = f"{args.frontend_url.rstrip('/')}/c/{link.token}"

        print("\nGuest chat (Suite Giardino):")
        print(f"  {guest_url}")
        print("\nTry asking:")
        print("  • A che ora è il check-in?")
        print("  • What's the Wi-Fi password?")
        print("  • Dove posso parcheggiare?")
        print("  • Quel est le petit-déjeuner ?")
        print("\nAdmin panel: /admin  ·  Host portal: /host")

        if any(s != "processed" for s in statuses):
            raise SystemExit("\nSome documents failed to ingest — see the errors above.")

        print("\nDone.")


if __name__ == "__main__":
    main()
