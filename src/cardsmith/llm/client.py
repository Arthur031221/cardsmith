"""Client for Ollama's native /api/chat endpoint.

cardsmith talks to Ollama's own /api/chat rather than its OpenAI-compatible
/v1/chat/completions endpoint. On Ollama builds current at the time this was
written, the OpenAI-compatible endpoint ignores `think: false` for qwen3
models and the model spends its output budget on hidden reasoning tokens
instead of the answer. The native endpoint honors `think: false` and
supports passing a JSON schema object directly as `format`, which the model
is then constrained to follow.
"""

from __future__ import annotations

import json
from typing import Any, Protocol

import httpx

DEFAULT_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen3:4b"


class OllamaError(RuntimeError):
    """Raised when Ollama is unreachable, errors, or returns unparseable JSON."""


class ChatClient(Protocol):
    """Interface generate.py depends on, so tests can substitute a fake."""

    def chat_json(
        self, messages: list[dict[str, str]], schema: dict[str, Any]
    ) -> dict[str, Any]: ...


class OllamaClient:
    def __init__(
        self,
        base_url: str = DEFAULT_URL,
        model: str = DEFAULT_MODEL,
        timeout: float = 120.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.http = httpx.Client(transport=transport)

    def ping(self) -> tuple[bool, str]:
        """Return (ok, message). Used by /api/health and the CLI startup check."""
        try:
            r = self.http.get(f"{self.base_url}/api/tags", timeout=5.0)
        except httpx.HTTPError as e:
            return False, f"cannot reach ollama at {self.base_url}: {e}"
        if r.status_code != 200:
            return False, f"ollama returned HTTP {r.status_code}"
        names = [m.get("name", "") for m in r.json().get("models", [])]
        if not any(n == self.model or n.startswith(self.model.split(":")[0]) for n in names):
            return (
                False,
                f"model {self.model} not found in `ollama list` ({', '.join(names) or 'no models pulled'})",
            )
        return True, "ok"

    def chat_json(self, messages: list[dict[str, str]], schema: dict[str, Any]) -> dict[str, Any]:
        """POST /api/chat with think disabled and a strict JSON schema for the reply."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "think": False,
            "format": schema,
            "options": {"temperature": 0.2, "num_predict": 2048},
        }
        try:
            r = self.http.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout)
        except httpx.TimeoutException as e:
            raise OllamaError(f"ollama timed out after {self.timeout:.0f}s: {e}") from e
        except httpx.HTTPError as e:
            raise OllamaError(f"cannot reach ollama at {self.base_url}: {e}") from e
        if r.status_code != 200:
            raise OllamaError(f"ollama returned HTTP {r.status_code}: {r.text[:300]}")
        try:
            data = r.json()
        except ValueError as e:
            raise OllamaError(f"ollama response is not JSON: {e}") from e
        content = (data.get("message") or {}).get("content") or ""
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise OllamaError(
                f"model did not return valid JSON: {e}. content={content[:300]!r}"
            ) from e
