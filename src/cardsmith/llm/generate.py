"""Turn ingested text chunks into flashcards through the local LLM."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from cardsmith.ingest.chunking import Chunk
from cardsmith.llm.client import ChatClient, OllamaError
from cardsmith.llm.schema import CARD_RESPONSE_SCHEMA, Card

SYSTEM_PROMPT = """You write spaced-repetition flashcards from study material for a tool \
called cardsmith. Rules:
1. Use only facts stated in the passage given to you. Never add outside knowledge.
2. Every card must include source_quote: a short excerpt (under 25 words) copied \
verbatim from the passage that supports the card. Copy it exactly, do not paraphrase it.
3. Write a mix of "basic" cards (a question in `front`, the answer in `back`) and \
"cloze" cards (a sentence in `cloze_text` with the key term wrapped like \
{{c1::term}}, and leave `front` and `back` as empty strings for cloze cards; \
leave `cloze_text` as an empty string for basic cards).
4. Keep each card testing exactly one fact. Avoid yes/no questions.
5. Reply with JSON only, matching the given schema."""


def _user_prompt(chunk_text: str, chunk_label: str, deck_title: str, n_cards: int) -> str:
    return (
        f'Study material: "{deck_title}", {chunk_label}.\n\n'
        f"Passage:\n{chunk_text}\n\n"
        f"Write {n_cards} flashcards from this passage as a JSON object: "
        '{"cards": [...]}.'
    )


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _is_grounded(quote: str, chunk_text: str) -> bool:
    q = _normalize(quote)
    if len(q) < 6:
        return False
    return q in _normalize(chunk_text)


def _dedup_key(card: Card) -> str:
    if card.card_type == "cloze":
        return "c:" + _normalize(card.cloze_text)
    return "b:" + _normalize(card.front)


def generate_cards_for_chunk(
    client: ChatClient,
    chunk: Chunk,
    deck_title: str,
    n_cards: int = 4,
    max_retries: int = 1,
) -> list[Card]:
    """Call the LLM for one chunk and return validated Card objects.

    Cards whose source_quote cannot be found verbatim in the chunk are kept
    but marked grounded=False, so the preview UI can flag them instead of
    silently trusting a possibly invented quote.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": _user_prompt(chunk.text, chunk.label, deck_title, n_cards)},
    ]
    last_error: Exception | None = None
    for _attempt in range(max_retries + 1):
        try:
            data = client.chat_json(messages, CARD_RESPONSE_SCHEMA)
            return _parse_cards(data, chunk)
        except (OllamaError, ValueError, KeyError, TypeError) as e:
            last_error = e
            messages.append(
                {
                    "role": "user",
                    "content": "That reply was not valid. Reply with JSON only, matching the schema exactly.",
                }
            )
    raise OllamaError(f"failed to generate cards for {chunk.label}: {last_error}")


def _parse_cards(data: dict[str, Any], chunk: Chunk) -> list[Card]:
    raw_cards = data.get("cards")
    if not isinstance(raw_cards, list):
        raise ValueError("response missing 'cards' array")
    cards: list[Card] = []
    for raw in raw_cards:
        if not isinstance(raw, dict):
            continue
        card_type = raw.get("type") if raw.get("type") in ("basic", "cloze") else "basic"
        front = str(raw.get("front", "")).strip()
        back = str(raw.get("back", "")).strip()
        cloze_text = str(raw.get("cloze_text", "")).strip()
        quote = str(raw.get("source_quote", "")).strip()
        if card_type == "basic" and not (front and back):
            continue
        if card_type == "cloze" and ("{{c" not in cloze_text):
            continue
        cards.append(
            Card(
                card_type=card_type,
                front=front,
                back=back,
                cloze_text=cloze_text,
                source_quote=quote,
                source_location=chunk.label,
                grounded=_is_grounded(quote, chunk.text),
            )
        )
    return cards


def generate_cards(
    client: ChatClient,
    chunks: list[Chunk],
    deck_title: str,
    cards_per_chunk: int = 4,
    progress_cb: Callable[[int, int, str], None] | None = None,
) -> tuple[list[Card], list[str]]:
    """Generate cards for every chunk. Returns (cards, errors).

    A chunk that fails to generate does not abort the whole deck: its error
    is collected and generation continues with the next chunk.
    """
    all_cards: list[Card] = []
    errors: list[str] = []
    seen: set[str] = set()
    total = len(chunks)
    for i, chunk in enumerate(chunks, start=1):
        if progress_cb:
            progress_cb(i, total, chunk.label)
        try:
            chunk_cards = generate_cards_for_chunk(client, chunk, deck_title, cards_per_chunk)
        except OllamaError as e:
            errors.append(str(e))
            continue
        for card in chunk_cards:
            key = _dedup_key(card)
            if key in seen:
                continue
            seen.add(key)
            all_cards.append(card)
    return all_cards, errors
