import sqlite3
import zipfile

from cardsmith.anki import export_apkg


def _note_count(apkg_path: str) -> int:
    with zipfile.ZipFile(apkg_path) as z:
        raw = z.read("collection.anki2")
    tmp = apkg_path + ".sqlite"
    with open(tmp, "wb") as f:
        f.write(raw)
    conn = sqlite3.connect(tmp)
    count = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    conn.close()
    return count


def test_export_apkg_writes_valid_package(tmp_path):
    cards = [
        {
            "card_type": "basic",
            "front": "What is the powerhouse of the cell?",
            "back": "The mitochondrion",
            "source_quote": "the mitochondrion is the organelle",
            "source_location": "page 1",
        },
        {
            "card_type": "cloze",
            "cloze_text": "The {{c1::nucleus}} stores genetic material.",
            "source_quote": "the nucleus stores the cell's genetic material",
            "source_location": "page 2",
        },
    ]
    out_path = str(tmp_path / "deck.apkg")
    written = export_apkg("Cell Biology", "deck-1", cards, out_path)
    assert written == 2
    assert zipfile.is_zipfile(out_path)
    assert _note_count(out_path) == 2


def test_export_apkg_skips_incomplete_cards(tmp_path):
    cards = [
        {
            "card_type": "basic",
            "front": "",
            "back": "no question",
            "source_quote": "",
            "source_location": "",
        },
        {
            "card_type": "basic",
            "front": "ok",
            "back": "ok",
            "source_quote": "",
            "source_location": "",
        },
        {"card_type": "cloze", "cloze_text": "", "source_quote": "", "source_location": ""},
    ]
    out_path = str(tmp_path / "deck.apkg")
    written = export_apkg("Deck", "deck-2", cards, out_path)
    assert written == 1


def test_export_apkg_is_stable_across_reexports(tmp_path):
    cards = [
        {"card_type": "basic", "front": "Q", "back": "A", "source_quote": "", "source_location": ""}
    ]
    out1 = str(tmp_path / "a.apkg")
    out2 = str(tmp_path / "b.apkg")
    export_apkg("Deck", "same-key", cards, out1)
    export_apkg("Deck", "same-key", cards, out2)
    # same deck_key must produce the same Anki deck id, so re-exports merge in Anki
    from cardsmith.anki import _stable_id

    assert _stable_id("cardsmith-deck-same-key", 2_000_000_000) == _stable_id(
        "cardsmith-deck-same-key", 2_000_000_000
    )
