"""Document ingestion: turn a PDF, slide deck, or text file into labeled text chunks."""

from cardsmith.ingest.chunking import Chunk, merge_units
from cardsmith.ingest.pdf import extract_pdf
from cardsmith.ingest.pptx import extract_pptx
from cardsmith.ingest.text import extract_text

__all__ = ["Chunk", "extract_pdf", "extract_pptx", "extract_text", "merge_units"]


class UnsupportedFileError(ValueError):
    """Raised when a file extension is not one cardsmith knows how to ingest."""


def extract_any(path: str) -> list[Chunk]:
    """Dispatch on file extension and return merged chunks ready for card generation."""
    lower = path.lower()
    if lower.endswith(".pdf"):
        return extract_pdf(path)
    if lower.endswith(".pptx"):
        return extract_pptx(path)
    if lower.endswith((".txt", ".md")):
        return extract_text(path)
    raise UnsupportedFileError(f"unsupported file type: {path}. Use .pdf, .pptx, .txt, or .md")
