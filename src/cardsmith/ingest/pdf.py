"""PDF text extraction through pymupdf."""

from __future__ import annotations

import pymupdf

from cardsmith.ingest.chunking import Chunk, merge_units


def extract_pdf(path: str) -> list[Chunk]:
    """Extract text per page and merge into LLM-sized chunks labeled by page number."""
    units: list[tuple[str, str]] = []
    with pymupdf.open(path) as doc:
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text")
            units.append((f"page {i}", text))
    return merge_units(units)
