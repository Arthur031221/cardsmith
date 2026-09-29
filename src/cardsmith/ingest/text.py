"""Plain text and Markdown ingestion, split into paragraph units."""

from __future__ import annotations

import re
from pathlib import Path

from cardsmith.ingest.chunking import Chunk, merge_units

# Plain-text sources (Project Gutenberg among them) mark italics with a
# leading and trailing underscore, e.g. "_Genus_ Homo". Strip the markers so
# they do not show up inside generated cards or break verbatim quote matching.
_EMPHASIS_RE = re.compile(r"(?<!\w)_([^_\n]+)_(?!\w)")


def _strip_emphasis_markers(text: str) -> str:
    return _EMPHASIS_RE.sub(r"\1", text)


def extract_text(path: str) -> list[Chunk]:
    """Split a .txt or .md file into paragraphs and merge into LLM-sized chunks."""
    raw = Path(path).read_text(encoding="utf-8", errors="replace")
    raw = _strip_emphasis_markers(raw)
    paragraphs = [p.strip() for p in raw.split("\n\n") if p.strip()]
    units = [(f"paragraph {i}", p) for i, p in enumerate(paragraphs, start=1)]
    return merge_units(units)
