"""Tests for the Ollama native /api/chat client, with the network replaced by httpx.MockTransport."""

import json

import httpx
import pytest

from cardsmith.llm.client import OllamaClient, OllamaError
from cardsmith.llm.schema import CARD_RESPONSE_SCHEMA

CAPTURED = {}


def _handler(request: httpx.Request) -> httpx.Response:
    CAPTURED["request"] = request
    if request.url.path == "/api/tags":
        return httpx.Response(200, json={"models": [{"name": "qwen3:4b"}]})
    CAPTURED["payload"] = json.loads(request.content)
    return httpx.Response(
        200,
        json={
            "message": {
                "content": json.dumps(
                    {
                        "cards": [
                            {
                                "type": "basic",
                                "front": "Q",
                                "back": "A",
                                "cloze_text": "",
                                "source_quote": "x",
                            }
                        ]
                    }
                )
            },
            "done": True,
        },
    )


def test_chat_json_posts_to_native_api_chat_with_think_false_and_schema_format():
    client = OllamaClient(transport=httpx.MockTransport(_handler))
    result = client.chat_json([{"role": "user", "content": "hi"}], CARD_RESPONSE_SCHEMA)

    request = CAPTURED["request"]
    payload = CAPTURED["payload"]
    assert request.url.path == "/api/chat"
    assert payload["think"] is False
    assert payload["stream"] is False
    assert payload["format"] == CARD_RESPONSE_SCHEMA
    assert payload["model"] == "qwen3:4b"
    assert result["cards"][0]["front"] == "Q"


def test_chat_json_raises_on_invalid_json_content():
    def handler(request):
        return httpx.Response(200, json={"message": {"content": "not json"}})

    client = OllamaClient(transport=httpx.MockTransport(handler))
    with pytest.raises(OllamaError, match="not return valid JSON"):
        client.chat_json([{"role": "user", "content": "hi"}], CARD_RESPONSE_SCHEMA)


def test_chat_json_raises_on_http_error():
    def handler(request):
        return httpx.Response(500, text="internal error")

    client = OllamaClient(transport=httpx.MockTransport(handler))
    with pytest.raises(OllamaError, match="HTTP 500"):
        client.chat_json([{"role": "user", "content": "hi"}], CARD_RESPONSE_SCHEMA)


def test_ping_ok_when_model_present():
    client = OllamaClient(model="qwen3:4b", transport=httpx.MockTransport(_handler))
    ok, _message = client.ping()
    assert ok is True


def test_ping_reports_missing_model():
    def handler(request):
        return httpx.Response(200, json={"models": [{"name": "other-model"}]})

    client = OllamaClient(model="qwen3:4b", transport=httpx.MockTransport(handler))
    ok, message = client.ping()
    assert ok is False
    assert "qwen3:4b" in message


def test_ping_does_not_accept_a_different_tag_from_the_same_model_family():
    def handler(request):
        return httpx.Response(200, json={"models": [{"name": "qwen3:32b"}]})

    client = OllamaClient(model="qwen3:4b", transport=httpx.MockTransport(handler))
    ok, message = client.ping()

    assert ok is False
    assert "qwen3:4b" in message


def test_ping_accepts_a_tagged_model_when_configured_without_a_tag():
    def handler(request):
        return httpx.Response(200, json={"models": [{"name": "qwen3:latest"}]})

    client = OllamaClient(model="qwen3", transport=httpx.MockTransport(handler))
    ok, _message = client.ping()

    assert ok is True


def test_ping_reports_unreachable_server():
    def handler(request):
        raise httpx.ConnectError("connection refused")

    client = OllamaClient(transport=httpx.MockTransport(handler))
    ok, message = client.ping()
    assert ok is False
    assert "cannot reach ollama" in message
