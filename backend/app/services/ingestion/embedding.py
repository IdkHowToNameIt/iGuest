"""
Gemini text embeddings (Google AI Studio) via the ``google-genai`` SDK.

Used both at ingestion time (embedding document chunks) and at query time
(embedding the guest's question). The ``google.genai`` SDK is imported lazily so
modules that only need chunking/conversion don't require it, and so importing the
RAG engine doesn't hit the network or require an API key.

gemini-embedding-001 returns 3072-dim vectors by default; we request
``output_dimensionality`` = ``DocumentChunk.embedding`` width (768) so the
vectors fit the DB column. Retrieval uses cosine distance, which is
scale-invariant, so the truncated (Matryoshka) vectors need no renormalisation.
"""

from app.config import settings
from app.models.document_chunk import EMBEDDING_DIM


def _client():
    from google import genai

    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set — configure it in backend/.env to use embeddings."
        )
    return genai.Client(api_key=settings.gemini_api_key)


def embed_texts(texts: list[str], *, task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """Embed a list of texts, batching to keep request sizes reasonable.

    Returns one vector per input text, in the same order.
    """
    if not texts:
        return []

    from google.genai import types

    client = _client()
    config = types.EmbedContentConfig(
        task_type=task_type, output_dimensionality=EMBEDDING_DIM
    )
    vectors: list[list[float]] = []
    batch_size = max(1, settings.embedding_batch_size)
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        result = client.models.embed_content(
            model=settings.embedding_model, contents=batch, config=config
        )
        vectors.extend(e.values for e in result.embeddings)
    return vectors


def embed_text(text: str, *, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
    """Embed a single text and return its vector."""
    from google.genai import types

    client = _client()
    result = client.models.embed_content(
        model=settings.embedding_model,
        contents=text,
        config=types.EmbedContentConfig(
            task_type=task_type, output_dimensionality=EMBEDDING_DIM
        ),
    )
    return result.embeddings[0].values
