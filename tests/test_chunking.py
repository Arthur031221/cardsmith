from cardsmith.ingest.chunking import merge_units


def test_merges_small_adjacent_units():
    units = [("page 1", "short"), ("page 2", "also short"), ("page 3", "still short")]
    chunks = merge_units(units, min_words=20, max_words=100)
    assert len(chunks) == 1
    assert "short" in chunks[0].text
    assert chunks[0].label == "page 1-page 3"


def test_flushes_as_soon_as_min_words_is_reached():
    units = [("page 1", "short"), ("page 2", "also short"), ("page 3", "still short")]
    chunks = merge_units(units, min_words=3, max_words=100)
    assert len(chunks) == 2
    assert chunks[0].label == "page 1-page 2"


def test_splits_oversized_unit():
    long_text = " ".join(f"word{i}" for i in range(50))
    chunks = merge_units([("page 1", long_text)], min_words=5, max_words=20)
    assert len(chunks) == 3
    assert chunks[0].label == "page 1 (part 1)"
    assert sum(c.word_count for c in chunks) == 50


def test_drops_empty_units():
    chunks = merge_units([("page 1", ""), ("page 2", "   "), ("page 3", "real text here")])
    assert len(chunks) == 1
    assert "real text" in chunks[0].text


def test_empty_input_returns_empty_list():
    assert merge_units([]) == []
