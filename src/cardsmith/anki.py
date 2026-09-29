"""Export a deck to an Anki .apkg package through genanki."""

from __future__ import annotations

import hashlib

import genanki

_CSS = """
.card { font-family: -apple-system, Helvetica, Arial, sans-serif; font-size: 20px;
        text-align: center; color: #1a1a1a; background-color: #fafafa; }
.source { margin-top: 16px; font-size: 13px; color: #888; font-style: italic; }
.cloze { font-weight: bold; color: #2a5db0; }
"""


def _stable_id(seed: str, base: int) -> int:
    """Deterministic id in genanki's expected range, so re-exporting the same
    deck produces model and deck ids Anki recognizes as the same deck."""
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    return base + (int(digest, 16) % 900_000_000)


BASIC_MODEL = genanki.Model(
    _stable_id("cardsmith-basic-model-v1", 1_900_000_000),
    "cardsmith Basic",
    fields=[{"name": "Front"}, {"name": "Back"}, {"name": "Source"}],
    templates=[
        {
            "name": "Card 1",
            "qfmt": "{{Front}}",
            "afmt": '{{FrontSide}}<hr id="answer">{{Back}}<div class="source">{{Source}}</div>',
        }
    ],
    css=_CSS,
)

CLOZE_MODEL = genanki.Model(
    _stable_id("cardsmith-cloze-model-v1", 1_950_000_000),
    "cardsmith Cloze",
    model_type=genanki.Model.CLOZE,
    fields=[{"name": "Text"}, {"name": "Source"}],
    templates=[
        {
            "name": "Cloze",
            "qfmt": "{{cloze:Text}}",
            "afmt": '{{cloze:Text}}<div class="source">{{Source}}</div>',
        }
    ],
    css=_CSS,
)


def export_apkg(deck_title: str, deck_key: str, cards: list[dict], output_path: str) -> int:
    """Write cards to an .apkg file. Returns the number of notes written.

    deck_key should be stable across re-exports of the same logical deck
    (the database deck id works well) so Anki treats repeated exports as
    updates to the same deck rather than duplicates.
    """
    deck_id = _stable_id(f"cardsmith-deck-{deck_key}", 2_000_000_000)
    deck = genanki.Deck(deck_id, deck_title)
    written = 0
    for card in cards:
        source = f"{card.get('source_location', '')}: {card.get('source_quote', '')}".strip(": ")
        if card.get("card_type") == "cloze" or card.get("type") == "cloze":
            text = card.get("cloze_text", "")
            if not text.strip():
                continue
            deck.add_note(genanki.Note(model=CLOZE_MODEL, fields=[text, source]))
        else:
            front, back = card.get("front", ""), card.get("back", "")
            if not front.strip() or not back.strip():
                continue
            deck.add_note(genanki.Note(model=BASIC_MODEL, fields=[front, back, source]))
        written += 1
    genanki.Package(deck).write_to_file(output_path)
    return written
