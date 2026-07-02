"""
Ingestion pipeline orchestration: convert → chunk → embed → persist.

Given an existing ``Document`` row (status "pending"), this runs the full
pipeline and updates the document's status:
  - success → status "processed", chunks saved with their embeddings
  - failure → status "error", ``error_message`` set, then the exception re-raised

The caller (admin upload / demo scripts) decides whether to surface or swallow
the error; either way the document row reflects the outcome.
"""

import logging
import uuid

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Document, DocumentChunk
from app.services.ingestion.chunking import chunk_text
from app.services.ingestion.conversion import extract_text
from app.services.ingestion.embedding import embed_texts

logger = logging.getLogger(__name__)


def ingest_document(
    db: Session, document_id: uuid.UUID, content: bytes, filename: str
) -> int:
    """Run the ingestion pipeline for ``document_id``. Returns the chunk count.

    On any failure the document is marked status="error" (committed) and the
    exception is re-raised.
    """
    document = db.get(Document, document_id)
    if document is None:
        raise ValueError(f"Document {document_id} not found")

    # 1. Convert to plain text and persist it *immediately*. Human viewing of the
    #    manual (admin + host) must not depend on the embedding step succeeding:
    #    a later Gemini/embedding failure must never erase the readable text.
    try:
        text = extract_text(content, filename)
    except Exception as exc:
        db.rollback()
        document = db.get(Document, document_id)
        if document is not None:
            document.status = "error"
            document.error_message = str(exc)
            document.extracted_text = None
            db.commit()
        raise
    document.extracted_text = text
    document.error_message = None
    db.commit()

    # 2. Chunk + embed for RAG. If this fails the document keeps its (already
    #    committed) extracted_text and is still viewable — only indexing is lost.
    try:
        chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        if not chunks:
            raise ValueError("Document produced no text to index.")

        embeddings = embed_texts(chunks)

        # Replace any previous chunks for this document, then persist.
        document.chunks.clear()
        db.flush()
        for chunk_content, vector in zip(chunks, embeddings):
            db.add(
                DocumentChunk(
                    document_id=document.id,
                    structure_id=document.structure_id,
                    unit_id=document.unit_id,  # null for structure-scoped docs
                    content=chunk_content,
                    embedding=vector,
                )
            )

        document.status = "processed"
        document.error_message = None
        db.commit()
        logger.info("Ingested document %s: %d chunks", document.id, len(chunks))
        return len(chunks)

    except Exception as exc:
        # Indexing failed: record it, but the extracted text stays readable.
        db.rollback()
        document = db.get(Document, document_id)
        if document is not None:
            document.status = "error"
            document.error_message = str(exc)
            db.commit()
        raise
