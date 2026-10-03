import zipfile

import starlette.datastructures
from fastapi.testclient import TestClient

from cardsmith.web import app as web_app
from cardsmith.web.app import create_app

from .conftest import FakeChatClient, card_response


def make_client(tmp_db, chat_client=None):
    chat_client = chat_client or FakeChatClient(responses=[card_response("nucleus stores")])
    app = create_app(db_path=tmp_db, client=chat_client, cards_per_chunk=1)
    return TestClient(app), chat_client


def test_index_page_serves_html(tmp_db):
    client, _ = make_client(tmp_db)
    r = client.get("/")
    assert r.status_code == 200
    assert "cardsmith" in r.text.lower()


def test_health_endpoint(tmp_db):
    client, _ = make_client(tmp_db)
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["ollama_ok"] is True


def test_generate_rejects_unsupported_extension(tmp_db):
    client, _ = make_client(tmp_db)
    r = client.post(
        "/api/generate", files={"file": ("notes.docx", b"hello", "application/octet-stream")}
    )
    assert r.status_code == 400
    assert "unsupported" in r.json()["detail"]


def test_generate_rejects_empty_file(tmp_db):
    client, _ = make_client(tmp_db)
    r = client.post("/api/generate", files={"file": ("notes.txt", b"", "text/plain")})
    assert r.status_code == 400


def test_generate_reads_only_one_byte_over_upload_limit(tmp_db, monkeypatch):
    monkeypatch.setattr(web_app, "MAX_UPLOAD_BYTES", 16)
    original_read = starlette.datastructures.UploadFile.read
    requested_sizes = []

    async def tracking_read(file, size=-1):
        requested_sizes.append(size)
        return await original_read(file, size)

    monkeypatch.setattr(starlette.datastructures.UploadFile, "read", tracking_read)
    client, _ = make_client(tmp_db)

    r = client.post("/api/generate", files={"file": ("notes.txt", b"x" * 17, "text/plain")})

    assert r.status_code == 400
    assert "16 byte limit" in r.json()["detail"]
    assert requested_sizes == [17]


def test_full_workflow_generate_save_study_export(tmp_db, sample_txt):
    chat_client = FakeChatClient(responses=[card_response("nucleus stores the cell", n=2)])
    client, _ = make_client(tmp_db, chat_client)

    with open(sample_txt, "rb") as f:
        r = client.post(
            "/api/generate",
            files={"file": ("notes.txt", f, "text/plain")},
            data={"title": "Cell Biology"},
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["deck_title"] == "Cell Biology"
    assert len(body["cards"]) == 2

    r = client.post(
        "/api/decks",
        json={
            "title": body["deck_title"],
            "source_filename": body["source_filename"],
            "cards": body["cards"],
        },
    )
    assert r.status_code == 200, r.text
    deck_id = r.json()["deck"]["id"]
    assert len(r.json()["cards"]) == 2

    r = client.get("/api/decks")
    assert r.status_code == 200
    assert any(d["id"] == deck_id for d in r.json()["decks"])

    r = client.get(f"/api/decks/{deck_id}")
    assert r.status_code == 200
    cards = r.json()["cards"]
    assert len(cards) == 2
    assert r.json()["stats"]["due"] == 2

    card_id = cards[0]["id"]
    r = client.put(f"/api/decks/{deck_id}/cards/{card_id}", json={"front": "Edited question"})
    assert r.status_code == 200
    assert r.json()["front"] == "Edited question"

    r = client.get(f"/api/decks/{deck_id}/study/next")
    assert r.status_code == 200
    due_card = r.json()["card"]
    assert due_card is not None

    r = client.post(f"/api/decks/{deck_id}/study/{due_card['id']}", json={"quality": 4})
    assert r.status_code == 200
    assert r.json()["card"]["repetition"] == 1

    r = client.delete(f"/api/decks/{deck_id}/cards/{cards[1]['id']}")
    assert r.status_code == 200

    r = client.get(f"/api/decks/{deck_id}/export")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/octet-stream"
    out_path = str(client.app.state.db_path) + "-export.apkg"
    with open(out_path, "wb") as f:
        f.write(r.content)
    assert zipfile.is_zipfile(out_path)

    r = client.delete(f"/api/decks/{deck_id}")
    assert r.status_code == 200
    assert client.get(f"/api/decks/{deck_id}").status_code == 404


def test_study_next_on_empty_deck(tmp_db):
    client, _ = make_client(tmp_db)
    r = client.post("/api/decks", json={"title": "Empty", "cards": []})
    deck_id = r.json()["deck"]["id"]
    r = client.get(f"/api/decks/{deck_id}/study/next")
    assert r.status_code == 200
    assert r.json()["card"] is None


def test_export_with_no_cards_returns_400(tmp_db):
    client, _ = make_client(tmp_db)
    r = client.post("/api/decks", json={"title": "Empty", "cards": []})
    deck_id = r.json()["deck"]["id"]
    r = client.get(f"/api/decks/{deck_id}/export")
    assert r.status_code == 400


def test_generate_failure_returns_502(tmp_db):
    def always_fail(messages, schema):
        from cardsmith.llm.client import OllamaError

        raise OllamaError("ollama down")

    chat_client = FakeChatClient(script=always_fail)
    client, _ = make_client(tmp_db, chat_client)
    r = client.post(
        "/api/generate", files={"file": ("notes.txt", b"some study notes text here", "text/plain")}
    )
    assert r.status_code == 502


def test_manual_card_add(tmp_db):
    client, _ = make_client(tmp_db)
    r = client.post("/api/decks", json={"title": "Manual", "cards": []})
    deck_id = r.json()["deck"]["id"]
    r = client.post(
        f"/api/decks/{deck_id}/cards",
        json={
            "type": "basic",
            "front": "Q",
            "back": "A",
            "source_quote": "",
            "source_location": "manual",
        },
    )
    assert r.status_code == 200
    assert r.json()["front"] == "Q"
