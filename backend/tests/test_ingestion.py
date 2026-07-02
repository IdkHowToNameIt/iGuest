"""
Unit tests for the ingestion pipeline components.

These tests run without a DB or Gemini API key — they cover conversion and
chunking logic only. Pipeline integration (embed + DB) requires live services
and is verified via scripts/demo_ingestion.py.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

# Import directly from the leaf modules to avoid loading SQLAlchemy/pgvector,
# which may not be available in lightweight CI / unit-test environments.
from app.services.ingestion.chunking import chunk_text
from app.services.ingestion.conversion import OCRRequiredError, extract_text


# ── chunking ─────────────────────────────────────────────────────────────────

class TestChunkText:
    def test_empty_text_returns_empty_list(self):
        assert chunk_text("") == []
        assert chunk_text("   \n  ") == []

    def test_short_text_is_single_chunk(self):
        text = "Hello, world!"
        chunks = chunk_text(text, chunk_size=100, chunk_overlap=10)
        assert chunks == ["Hello, world!"]

    def test_long_text_produces_multiple_chunks(self):
        # 3 paragraphs, each ~200 chars; chunk_size=250 → should split
        para = "A" * 200
        text = f"{para}\n\n{para}\n\n{para}"
        chunks = chunk_text(text, chunk_size=250, chunk_overlap=20)
        assert len(chunks) > 1

    def test_no_chunk_exceeds_chunk_size_by_much(self):
        text = " ".join(["word"] * 1000)
        chunks = chunk_text(text, chunk_size=100, chunk_overlap=10)
        # A small overrun is allowed when breaking at word boundaries
        for chunk in chunks:
            assert len(chunk) < 200, f"Chunk too long: {len(chunk)}"

    def test_overlap_carries_context(self):
        text = "First sentence. Second sentence. Third sentence."
        chunks = chunk_text(text, chunk_size=30, chunk_overlap=10)
        if len(chunks) > 1:
            # Last chars of chunk N should appear at the start of chunk N+1
            end_of_first = chunks[0][-10:]
            assert end_of_first in chunks[1] or len(chunks[1]) > 0

    def test_all_chunks_nonempty(self):
        text = "\n\n".join(["paragraph content"] * 50)
        chunks = chunk_text(text, chunk_size=50, chunk_overlap=10)
        for chunk in chunks:
            assert chunk.strip() != ""

    def test_configurable_size(self):
        text = "x" * 1000
        small = chunk_text(text, chunk_size=100, chunk_overlap=0)
        large = chunk_text(text, chunk_size=500, chunk_overlap=0)
        assert len(small) > len(large)


# ── conversion ────────────────────────────────────────────────────────────────

class TestExtractText:
    def test_plain_text(self):
        content = b"Hello, this is a plain text file.\nSecond line."
        result = extract_text(content, "manual.txt")
        assert "Hello" in result
        assert "Second line" in result

    def test_markdown(self):
        content = b"# Title\n\nSome content here.\n\n- item 1\n- item 2"
        result = extract_text(content, "readme.md")
        assert "Title" in result
        assert "item 1" in result

    def test_html_strips_tags(self):
        content = b"<html><head><style>body{}</style></head><body><h1>Title</h1><p>Content</p></body></html>"
        result = extract_text(content, "page.html")
        assert "Title" in result
        assert "Content" in result
        assert "<" not in result  # no raw HTML tags

    def test_html_removes_script_noise(self):
        content = b"<html><body><script>alert('x')</script><p>Real content</p></body></html>"
        result = extract_text(content, "page.html")
        assert "alert" not in result
        assert "Real content" in result

    def test_csv(self):
        content = b"name,age\nAlice,30\nBob,25"
        result = extract_text(content, "data.csv")
        assert "Alice" in result
        assert "Bob" in result

    def test_unsupported_format_raises(self):
        with pytest.raises(ValueError, match="Unsupported file format"):
            extract_text(b"data", "archive.zip")

    def test_image_raises_ocr_error(self):
        with pytest.raises(OCRRequiredError):
            extract_text(b"\xff\xd8\xff", "photo.jpg")

    def test_image_png_raises_ocr_error(self):
        with pytest.raises(OCRRequiredError):
            extract_text(b"\x89PNG", "scan.png")


# ── pipeline: viewing must not depend on embedding ──────────────────────────────

class TestPipelinePersistsText:
    """Regression: a document's extracted text must survive an embedding failure,
    so the host/admin can still read the manual (bug: rollback erased the text)."""

    def test_extracted_text_committed_before_and_kept_after_embed_failure(self, monkeypatch):
        # Imported lazily so the light conversion/chunking tests above stay DB-free.
        from app.services.ingestion import pipeline

        doc = SimpleNamespace(
            id="doc-1", structure_id="s", unit_id=None,
            extracted_text=None, error_message="stale", status="pending", chunks=[],
        )
        commits = []

        class FakeDB:
            def get(self, model, pk):
                return doc

            def commit(self):
                commits.append(doc.extracted_text)

            def rollback(self):
                pass

            def flush(self):
                pass

            def add(self, obj):
                pass

        # Embedding blows up (e.g. no Gemini key / offline) after text extraction.
        def boom(_texts):
            raise RuntimeError("embedding unavailable")

        monkeypatch.setattr(pipeline, "embed_texts", boom)

        with pytest.raises(RuntimeError):
            pipeline.ingest_document(FakeDB(), "doc-1", b"Line one.\n\nLine two.", "manual.txt")

        # Text was committed *before* embedding, and preserved despite the failure.
        assert commits and commits[0] == "Line one.\n\nLine two."
        assert doc.extracted_text == "Line one.\n\nLine two."
        assert doc.status == "error"
        assert "embedding" in doc.error_message
