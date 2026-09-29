import pytest

from cardsmith.ingest.chunking import Chunk
from cardsmith.llm.client import OllamaError
from cardsmith.llm.generate import generate_cards, generate_cards_for_chunk

from .conftest import FakeChatClient, card_response

CHUNK_TEXT = "Mitochondria produce ATP through cellular respiration in the cell."
CHUNK = Chunk(label="page 1", text=CHUNK_TEXT)


def test_generate_cards_for_chunk_returns_cards():
    client = FakeChatClient(responses=[card_response("Mitochondria produce ATP", n=2)])
    cards = generate_cards_for_chunk(client, CHUNK, "Cell Biology", n_cards=2)
    assert len(cards) == 2
    assert all(c.grounded for c in cards)
    assert all(c.source_location == "page 1" for c in cards)


def test_ungrounded_quote_is_flagged():
    client = FakeChatClient(responses=[card_response("this text is not in the chunk at all")])
    cards = generate_cards_for_chunk(client, CHUNK, "Cell Biology", n_cards=1)
    assert cards[0].grounded is False


def test_cloze_card_requires_cloze_markup():
    response = {
        "cards": [
            {
                "type": "cloze",
                "front": "",
                "back": "",
                "cloze_text": "no cloze markup here",
                "source_quote": "Mitochondria produce ATP",
            },
            {
                "type": "cloze",
                "front": "",
                "back": "",
                "cloze_text": "{{c1::Mitochondria}} produce ATP.",
                "source_quote": "Mitochondria produce ATP",
            },
        ]
    }
    client = FakeChatClient(responses=[response])
    cards = generate_cards_for_chunk(client, CHUNK, "Cell Biology", n_cards=2)
    assert len(cards) == 1
    assert cards[0].card_type == "cloze"


def test_retries_once_on_bad_json_then_succeeds():
    client = FakeChatClient(
        script=None,
        responses=[{"not_cards": []}, card_response("Mitochondria produce ATP")],
    )
    cards = generate_cards_for_chunk(client, CHUNK, "Cell Biology", n_cards=1, max_retries=1)
    assert len(cards) == 1
    assert len(client.calls) == 2


def test_gives_up_after_max_retries():
    client = FakeChatClient(responses=[{"not_cards": []}, {"still_bad": []}])
    with pytest.raises(OllamaError):
        generate_cards_for_chunk(client, CHUNK, "Cell Biology", n_cards=1, max_retries=1)


def test_generate_cards_continues_after_chunk_failure():
    chunks = [Chunk("page 1", CHUNK_TEXT), Chunk("page 2", "Chloroplasts capture light energy.")]

    def script(messages, schema):
        if "page 1" in messages[1]["content"]:
            raise OllamaError("simulated failure")
        return card_response("Chloroplasts capture light energy")

    client = FakeChatClient(script=script)
    cards, errors = generate_cards(client, chunks, "Cell Biology", cards_per_chunk=1)
    assert len(errors) == 1
    assert len(cards) == 1


def test_generate_cards_dedupes_identical_cards():
    chunks = [Chunk("page 1", CHUNK_TEXT), Chunk("page 2", CHUNK_TEXT)]
    response = card_response("Mitochondria produce ATP", n=1)
    client = FakeChatClient(responses=[response, response])
    cards, errors = generate_cards(client, chunks, "Cell Biology", cards_per_chunk=1)
    assert not errors
    assert len(cards) == 1
