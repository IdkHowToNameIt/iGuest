#!/usr/bin/env python
"""Demo script for Phase 2 — document ingestion pipeline.

Usage (from backend/ directory, with .env configured):

    python scripts/demo_ingestion.py /path/to/your/manual.pdf
    python scripts/demo_ingestion.py /path/to/manual.docx --scope unit

What it does:
  1. Creates a throw-away Structure and Unit in the DB.
  2. Creates a Document record with status="pending".
  3. Runs the full ingestion pipeline (convert → chunk → embed → save).
  4. Prints a summary: chunk count, first chunk preview, document status.

Prerequisites:
  - Docker DB is running: docker compose up -d  (from repo root)
  - .env is configured with GEMINI_API_KEY and DB params
  - Dependencies installed: pip install -r requirements.txt
  - Migrations applied: alembic upgrade head
"""

import argparse
import sys
from pathlib import Path

# Allow running from backend/ without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.database import SessionLocal
from app.models import Document, DocumentChunk, Structure, Unit
from app.services.ingestion import ingest_document


def main() -> None:
    # Non-ASCII output (→, …) crashes on Windows' default cp1252 console; force UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Demo: ingest a document file.")
    parser.add_argument("file", help="Path to the file to ingest (pdf, docx, txt, md, html…)")
    parser.add_argument(
        "--scope",
        choices=["structure", "unit"],
        default="unit",
        help="Ingestion scope (default: unit)",
    )
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"ERROR: file not found: {file_path}")
        sys.exit(1)

    file_content = file_path.read_bytes()
    filename = file_path.name

    with SessionLocal() as db:
        # Verify DB + pgvector are available
        db.execute(text("SELECT 1"))

        # Create throw-away structure and unit
        structure = Structure(
            name="[Demo] My Property",
            country_language="it",
            owner_contact="demo@example.com",
        )
        db.add(structure)
        db.flush()

        unit = Unit(
            structure_id=structure.id,
            name="[Demo] Room 1",
            owner_contact=None,
        )
        db.add(unit)
        db.flush()

        # Create the document record
        document = Document(
            scope_type=args.scope,
            structure_id=structure.id,
            unit_id=unit.id if args.scope == "unit" else None,
            original_filename=filename,
            file_type=file_path.suffix.lstrip(".").lower(),
            status="pending",
        )
        db.add(document)
        db.commit()

        print(f"\nDocument ID : {document.id}")
        print(f"Scope       : {args.scope}")
        print(f"File        : {filename} ({len(file_content):,} bytes)")
        print("\nRunning ingestion pipeline…")

        try:
            n_chunks = ingest_document(db, document.id, file_content, filename)
        except Exception as exc:
            # Status is already "error" in DB; surface the message
            print(f"\nIngestion FAILED: {exc}")
            db.refresh(document)
            print(f"DB status   : {document.status}")
            print(f"Error msg   : {document.error_message}")
            sys.exit(1)

        # Report results
        db.refresh(document)
        print(f"\nStatus      : {document.status}")
        print(f"Chunks saved: {n_chunks}")
        print(f"Text length : {len(document.extracted_text or ''):,} chars")

        # Preview first chunk
        first_chunk = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document.id)
            .order_by(DocumentChunk.created_at)
            .first()
        )
        if first_chunk:
            preview = first_chunk.content[:300].replace("\n", " ")
            print(f"\nFirst chunk preview:\n  {preview}…")

        print("\nDone. You can query these chunks via the RAG engine in Phase 3.")


if __name__ == "__main__":
    main()
