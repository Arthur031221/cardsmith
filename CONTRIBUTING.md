# Contributing

## Setup

```
git clone https://github.com/Arthur031221/cardsmith
cd cardsmith
uv sync
```

Card generation needs a local [Ollama](https://ollama.com) server with
`qwen3:4b` pulled (`ollama pull qwen3:4b`). Everything else, including the
whole test suite, runs without it.

## Running tests

```
uv run pytest
```

Tests mock the LLM (see `tests/conftest.py`, `FakeChatClient`), so they run
in under a second and never touch the network. If you add a feature that
calls the LLM, add a fake response for it rather than hitting a real
server.

## Lint and format

```
uv run ruff check src tests
uv run ruff format src tests
```

CI runs both, plus the test suite, on every push and pull request.

## Making changes

- Keep pull requests focused on one change.
- Add a test for new behavior.
- Update `CHANGELOG.md` under an `Unreleased` heading.
- Run the benchmark in `eval/` if you touch card generation, ingestion, or
  the grounding check, and mention the effect in your pull request
  description.

## Reporting bugs

Open an issue with the template. Include your `cardsmith --version`,
your OS, and `ollama list` output if generation is involved.
