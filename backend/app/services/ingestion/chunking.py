"""
Text chunking for the ingestion pipeline.

Splits an extracted document into overlapping windows sized for embedding.
Pure function, no I/O — kept import-light so it can be unit-tested without
SQLAlchemy / pgvector present.
"""


def chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 100) -> list[str]:
    """Split ``text`` into overlapping chunks of roughly ``chunk_size`` characters.

    Breaks at the nearest whitespace before the size limit to avoid cutting words
    in half; if no whitespace is available within the window (e.g. one very long
    token) it falls back to a hard cut so a chunk never grossly exceeds the limit.

    ``chunk_overlap`` characters from the end of each chunk are repeated at the
    start of the next, so context that straddles a boundary is not lost.

    Returns an empty list for empty/whitespace-only input.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    n = len(text)
    start = 0
    while start < n:
        end = min(start + chunk_size, n)
        if end < n:
            # Prefer a clean break at the last whitespace inside the window.
            window = text[start:end]
            brk = max(window.rfind(" "), window.rfind("\n"))
            # Only honour the break if it isn't too early (avoids tiny chunks).
            if brk > chunk_size // 2:
                end = start + brk + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= n:
            break
        # Step back by the overlap, but always make forward progress.
        start = max(end - chunk_overlap, start + 1)

    return chunks
