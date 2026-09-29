"""Command line entry point: `cardsmith` starts the local web UI."""

from __future__ import annotations

import argparse
import json
import sys
import threading
import webbrowser
from pathlib import Path

from cardsmith import __version__
from cardsmith.llm.client import DEFAULT_MODEL, DEFAULT_URL, OllamaClient
from cardsmith.web.app import create_app

DEFAULT_DB = str(Path.home() / ".cardsmith" / "cardsmith.db")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cardsmith",
        description=(
            "Offline flashcard generator. Starts a local web UI at the given host and port. "
            "Drop a PDF, slide deck, or text file, generate a spaced-repetition deck with a "
            "local Ollama model, study it, and export to Anki."
        ),
    )
    parser.add_argument("--host", default="127.0.0.1", help="bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8420, help="bind port (default: 8420)")
    parser.add_argument(
        "--db", default=DEFAULT_DB, help=f"SQLite database path (default: {DEFAULT_DB})"
    )
    parser.add_argument(
        "--ollama-url", default=DEFAULT_URL, help=f"Ollama server URL (default: {DEFAULT_URL})"
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Ollama model for card generation (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--cards-per-chunk", type=int, default=4, help="cards requested per text chunk (default: 4)"
    )
    parser.add_argument(
        "--no-browser", action="store_true", help="do not open a browser tab on start"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="check the Ollama connection and exit, do not start the server",
    )
    parser.add_argument(
        "--json", action="store_true", help="with --check, print the result as JSON"
    )
    parser.add_argument("--version", action="version", version=f"cardsmith {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    client = OllamaClient(base_url=args.ollama_url, model=args.model)

    if args.check:
        ok, message = client.ping()
        if args.json:
            print(
                json.dumps(
                    {"ok": ok, "message": message, "model": args.model, "url": args.ollama_url}
                )
            )
        else:
            status = "reachable" if ok else "unreachable"
            print(f"ollama at {args.ollama_url}: {status} ({message})")
        return 0 if ok else 1

    ok, message = client.ping()
    if not ok:
        print(
            f"warning: {message}\n"
            "The web UI will still start. Studying and exporting existing decks will work, "
            "but generating new cards needs a reachable Ollama server with the model pulled.",
            file=sys.stderr,
        )

    app = create_app(db_path=args.db, client=client, cards_per_chunk=args.cards_per_chunk)

    url = f"http://{args.host}:{args.port}"
    print(f"cardsmith database: {args.db}")
    print(f"cardsmith listening on {url}")

    if not args.no_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
