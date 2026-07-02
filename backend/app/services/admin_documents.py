"""
Admin document upload orchestration.

Creates a Document row, then runs the Phase-2 ingestion pipeline. Ingestion
failures are intentionally swallowed here: the pipeline records the failure on
the Document (status="error", error_message), and the upload still "succeeds"
in the sense that the document is stored and visible in the admin list with its
error status. This matches the requirement of listing documents with their status.
"""

import logging
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import Document
from app.services.ingestion import ingest_document

logger = logging.getLogger(__name__)


def create_and_ingest_document(
    db: Session,
    scope_type: str,
    structure_id: uuid.UUID,
    unit_id: uuid.UUID | None,
    filename: str,
    content: bytes,
) -> Document:
    """Persist a Document and run ingestion. Returns the (refreshed) Document.

    The returned document's `status` reflects the ingestion outcome
    ("processed" or "error").
    """
    file_type = Path(filename).suffix.lstrip(".").lower()
    document = Document(
        scope_type=scope_type,
        structure_id=structure_id,
        unit_id=unit_id,
        original_filename=filename,
        file_type=file_type,
        status="pending",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        ingest_document(db, document.id, content, filename)
    except Exception:
        # The pipeline has already marked the document as "error" and committed.
        # Swallow so the upload endpoint returns the document with its status.
        logger.warning("Ingestion failed for uploaded document %s", document.id)

    db.refresh(document)
    return document
