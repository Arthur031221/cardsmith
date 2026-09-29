#!/usr/bin/env python3
"""Benchmark: generate flashcards from a public-domain textbook chapter and
measure wall-clock time, chunk and card counts, and the verbatim-quote
grounding rate. Talks to a real Ollama server, no mock.

Source text: eval/chapter.txt, Chapter IV ("The Functions and Composition
of Living Things") of "A Civic Biology, Presented in Problems" by George W.
Hunter (American Book Company, 1914). Project Gutenberg ebook #39969,
public domain in the United States.
https://www.gutenberg.org/ebooks/39969

Usage:
    python3 eval/run_benchmark.py [--cards-per-chunk N] [--max-words N]

Writes eval/generated_cards.json (raw output) and prints a summary that
was pasted into eval/results.md by hand after review.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cardsmith.ingest.chunking import merge_units  # noqa: E402
from cardsmith.ingest.text import _strip_emphasis_markers  # noqa: E402
from cardsmith.llm.client import OllamaClient  # noqa: E402
from cardsmith.llm.generate import generate_cards  # noqa: E402

CHAPTER_PATH = Path(__file__).parent / "chapter.txt"
OUTPUT_PATH = Path(__file__).parent / "generated_cards.json"


def heartbeat(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards-per-chunk", type=int, default=8)
    parser.add_argument("--min-words", type=int, default=100)
    parser.add_argument("--max-words", type=int, default=350)
    parser.add_argument("--model", default="qwen3:4b")
    args = parser.parse_args()

    raw = _strip_emphasis_markers(CHAPTER_PATH.read_text())
    paragraphs = [p.strip() for p in raw.split("\n\n") if p.strip()]
    units = [(f"paragraph {i}", p) for i, p in enumerate(paragraphs, start=1)]
    chunks = merge_units(units, min_words=args.min_words, max_words=args.max_words)
    word_count = len(raw.split())
    heartbeat(f"loaded chapter: {word_count} words, {len(chunks)} chunks")

    client = OllamaClient(model=args.model)
    ok, message = client.ping()
    if not ok:
        print(f"ollama not reachable: {message}", file=sys.stderr)
        return 1

    t0 = time.monotonic()
    last_heartbeat = t0

    def progress(i, total, label):
        nonlocal last_heartbeat
        now = time.monotonic()
        if now - last_heartbeat > 15 * 60:
            heartbeat(f"still running: chunk {i}/{total} ({label})")
            last_heartbeat = now
        else:
            print(f"  chunk {i}/{total}: {label}", flush=True)

    cards, errors = generate_cards(
        client, chunks, "A Civic Biology, Chapter IV", args.cards_per_chunk, progress
    )
    elapsed = time.monotonic() - t0

    grounded = sum(1 for c in cards if c.grounded)
    summary = {
        "source": "Project Gutenberg ebook 39969, A Civic Biology by George W. Hunter (1914), "
        "Chapter IV: The Functions and Composition of Living Things",
        "chapter_word_count": word_count,
        "model": args.model,
        "chunk_count": len(chunks),
        "cards_requested_per_chunk": args.cards_per_chunk,
        "cards_generated": len(cards),
        "chunk_errors": errors,
        "elapsed_seconds": round(elapsed, 1),
        "cards_per_second": round(len(cards) / elapsed, 3) if elapsed else None,
        "grounded_quote_count": grounded,
        "grounded_quote_rate": round(grounded / len(cards), 3) if cards else None,
    }
    OUTPUT_PATH.write_text(
        json.dumps({"summary": summary, "cards": [c.to_dict() for c in cards]}, indent=2)
    )
    heartbeat(f"done: {len(cards)} cards in {elapsed:.1f}s, wrote {OUTPUT_PATH}")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
