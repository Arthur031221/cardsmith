"""Strict JSON schema for LLM-generated flashcards, plus the Card data shape.

Every card must carry a source_quote: a short verbatim excerpt from the chunk
it was built from. This is what lets the editable preview show provenance
and lets eval/run_benchmark.py check that cards are grounded in the text
rather than invented.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

CARD_TYPES = ("basic", "cloze")

# Passed as Ollama's `format` field so /api/chat returns exactly this shape.
CARD_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "cards": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": list(CARD_TYPES)},
                    "front": {"type": "string"},
                    "back": {"type": "string"},
                    "cloze_text": {"type": "string"},
                    "source_quote": {"type": "string"},
                },
                "required": ["type", "front", "back", "cloze_text", "source_quote"],
            },
        }
    },
    "required": ["cards"],
}


@dataclass
class Card:
    """One flashcard. id is None until the card is saved to the database."""

    card_type: str  # "basic" or "cloze"
    front: str
    back: str
    cloze_text: str
    source_quote: str
    source_location: str
    id: int | None = None
    grounded: bool = True  # False if source_quote could not be matched in the chunk
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.card_type,
            "front": self.front,
            "back": self.back,
            "cloze_text": self.cloze_text,
            "source_quote": self.source_quote,
            "source_location": self.source_location,
            "grounded": self.grounded,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Card:
        return cls(
            id=d.get("id"),
            card_type=d.get("type") or d.get("card_type") or "basic",
            front=d.get("front", ""),
            back=d.get("back", ""),
            cloze_text=d.get("cloze_text", ""),
            source_quote=d.get("source_quote", ""),
            source_location=d.get("source_location", ""),
            grounded=d.get("grounded", True),
            tags=d.get("tags", []),
        )

    def display_text(self) -> str:
        if self.card_type == "cloze":
            return self.cloze_text
        return f"{self.front} -> {self.back}"
