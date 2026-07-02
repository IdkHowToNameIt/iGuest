"""
Document → plain text conversion for the ingestion pipeline.

Supports the text-bearing formats typical of a digital property manual. Heavy,
format-specific libraries (PyMuPDF, python-docx, BeautifulSoup) are imported
lazily inside each branch so importing this module stays cheap and the chunking
unit tests can run without them.

Scanned images / image-only PDFs raise ``OCRRequiredError`` rather than silently
returning empty text — OCR is out of scope for the MVP (budget 0).
"""

from pathlib import Path


class OCRRequiredError(Exception):
    """Raised when a file carries no extractable text and would need OCR."""


# Extensions handled as UTF-8 text as-is (decoded, not parsed).
_PLAIN_TEXT_EXT = {"txt", "text", "md", "markdown", "csv", "tsv", "log"}
# Raster image formats — no embedded text, would require OCR.
_IMAGE_EXT = {"jpg", "jpeg", "png", "gif", "bmp", "tif", "tiff", "webp", "heic"}


def _decode(content: bytes) -> str:
    # Manuals may arrive in various encodings; never crash on a stray byte.
    return content.decode("utf-8", errors="replace")


def extract_text(content: bytes, filename: str) -> str:
    """Extract plain text from ``content`` based on ``filename``'s extension.

    Raises:
        OCRRequiredError: the format carries no machine-readable text (images,
            or a PDF that turns out to be image-only).
        ValueError: the format is not supported at all.
    """
    ext = Path(filename).suffix.lstrip(".").lower()

    if ext in _IMAGE_EXT:
        raise OCRRequiredError(
            f"'{filename}' is an image with no extractable text (OCR not supported)."
        )

    if ext in _PLAIN_TEXT_EXT:
        return _decode(content)

    if ext in {"html", "htm"}:
        return _extract_html(content)

    if ext == "pdf":
        return _extract_pdf(content, filename)

    if ext in {"docx"}:
        return _extract_docx(content)

    raise ValueError(f"Unsupported file format: '{ext or filename}'")


def _extract_html(content: bytes) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(_decode(content), "html.parser")
    # Drop non-content noise so it doesn't pollute the text / embeddings.
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)


def _extract_pdf(content: bytes, filename: str) -> str:
    import fitz  # PyMuPDF

    parts: list[str] = []
    with fitz.open(stream=content, filetype="pdf") as doc:
        for page in doc:
            parts.append(page.get_text())
    text = "\n".join(parts).strip()
    if not text:
        # No text layer → scanned/image-only PDF.
        raise OCRRequiredError(
            f"'{filename}' appears to be a scanned PDF with no text layer (OCR not supported)."
        )
    return text


def _extract_docx(content: bytes) -> str:
    import io

    from docx import Document as DocxDocument

    document = DocxDocument(io.BytesIO(content))
    return "\n".join(p.text for p in document.paragraphs).strip()
