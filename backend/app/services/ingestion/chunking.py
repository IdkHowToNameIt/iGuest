"""
Text chunking for the ingestion pipeline.

Splits an extracted document into overlapping windows sized for embedding.
Pure function, no I/O — kept import-light so it can be unit-tested without
SQLAlchemy / pgvector present.
"""


_PARAGRAPH_MARKERS = ("\n\n",)
_SENTENCE_MARKERS = (". ", "? ", "! ", "; ", ": ", ".\n", "?\n", "!\n")


def _best_break(window: str, chunk_size: int) -> int:
    """Return the best place to cut ``window``, or -1 to keep the full window.

    Preference order: paragraph break, sentence end, then whitespace. A marker in
    the first half of the window is ignored, otherwise chunks become tiny.
    """
    floor = chunk_size // 2

    def _last(markers: tuple[str, ...]) -> int:
        best = -1
        for marker in markers:
            idx = window.rfind(marker)
            if idx != -1:
                best = max(best, idx + len(marker))
        return best

    paragraph = _last(_PARAGRAPH_MARKERS)
    if paragraph > floor:
        return paragraph

    sentence = _last(_SENTENCE_MARKERS)
    if sentence > floor:
        return sentence

    # Fall back to the last space/newline: never cut a word in half unless the
    # window is a single very long token (then the hard cut is the only option).
    whitespace = max(window.rfind(" "), window.rfind("\n"))
    return whitespace + 1 if whitespace > floor else -1


def chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 100) -> list[str]:
    """Split ``text`` into overlapping chunks of roughly ``chunk_size`` characters.

    The cut point prefers paragraph boundaries, then sentence ends, then the last
    whitespace before the size limit, so a chunk rarely ends mid-sentence or
    mid-word. If the window holds no usable boundary (e.g. one very long token)
    it falls back to a hard cut so the size limit still holds roughly.

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
            # Prefer a clean break at a paragraph/sentence/word boundary.
            window = text[start:end]
            brk = _best_break(window, chunk_size)
            if brk > 0:
                end = start + brk

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= n:
            break
        # Step back by the overlap, but always make forward progress.
        start = max(end - chunk_overlap, start + 1)

    return chunks
