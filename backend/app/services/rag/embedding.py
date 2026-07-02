"""
Query embedding for retrieval.

Thin wrapper over the ingestion embedder using the ``retrieval_query`` task type
(the symmetric counterpart to ``retrieval_document`` used when indexing chunks).
Kept import-light: the Gemini SDK is only loaded when actually called.
"""


def embed_query(message: str) -> list[float]:
    """Embed a guest's question for similarity search against stored chunks."""
    from app.services.ingestion.embedding import embed_text

    return embed_text(message, task_type="RETRIEVAL_QUERY")
