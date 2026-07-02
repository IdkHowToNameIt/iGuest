"""
Document ingestion package.

``ingest_document`` is exposed lazily (PEP 562) so that importing the leaf
modules ``chunking`` / ``conversion`` for unit tests does not pull in
SQLAlchemy / pgvector via the pipeline.
"""

__all__ = ["ingest_document", "chunk_text", "extract_text", "OCRRequiredError"]


def __getattr__(name):  # pragma: no cover - thin lazy re-export
    if name == "ingest_document":
        from app.services.ingestion.pipeline import ingest_document

        return ingest_document
    if name in {"chunk_text"}:
        from app.services.ingestion.chunking import chunk_text

        return chunk_text
    if name in {"extract_text", "OCRRequiredError"}:
        from app.services.ingestion import conversion

        return getattr(conversion, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
