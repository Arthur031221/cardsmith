"""Merge raw per-page or per-slide text units into LLM-sized chunks.

A "unit" is one page of a PDF, one slide of a deck, or one paragraph of a
text file, paired with a human-readable label (for example "page 4" or
"slide 12"). Units are merged so each chunk sent to the LLM has enough
context to write a good card but stays small enough to generate quickly.
"""

from __future__ import annotations

from dataclasses import dataclass

MIN_WORDS = 120
MAX_WORDS = 900


@dataclass
class Chunk:
    label: str
    text: str

    @property
    def word_count(self) -> int:
        return len(self.text.split())


def _split_long(label: str, text: str, max_words: int) -> list[Chunk]:
    words = text.split()
    if len(words) <= max_words:
        return [Chunk(label, text)]
    out = []
    part = 1
    for i in range(0, len(words), max_words):
        piece = " ".join(words[i : i + max_words])
        out.append(Chunk(f"{label} (part {part})", piece))
        part += 1
    return out


def merge_units(
    units: list[tuple[str, str]], min_words: int = MIN_WORDS, max_words: int = MAX_WORDS
) -> list[Chunk]:
    """Merge small adjacent units and split oversized ones.

    units: list of (label, text) pairs in document order. Empty texts are dropped.
    """
    cleaned = [(label, text.strip()) for label, text in units if text and text.strip()]
    if not cleaned:
        return []

    merged: list[Chunk] = []
    buf_labels: list[str] = []
    buf_text: list[str] = []
    buf_words = 0

    def flush() -> None:
        nonlocal buf_labels, buf_text, buf_words
        if not buf_text:
            return
        label = buf_labels[0] if len(buf_labels) == 1 else f"{buf_labels[0]}-{buf_labels[-1]}"
        merged.extend(_split_long(label, "\n\n".join(buf_text), max_words))
        buf_labels, buf_text, buf_words = [], [], 0

    for label, text in cleaned:
        words = len(text.split())
        if buf_words and buf_words + words > max_words:
            flush()
        buf_labels.append(label)
        buf_text.append(text)
        buf_words += words
        if buf_words >= min_words:
            flush()
    flush()
    return merged
