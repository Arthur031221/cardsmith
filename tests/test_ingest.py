import pytest

from cardsmith import ingest
from cardsmith.ingest import extract_any, extract_pdf, extract_pptx, extract_text


def test_extract_pdf(sample_pdf):
    chunks = extract_pdf(sample_pdf)
    assert chunks
    joined = " ".join(c.text for c in chunks)
    assert "mitochondrion" in joined


def test_extract_pptx(sample_pptx):
    chunks = extract_pptx(sample_pptx)
    assert chunks
    joined = " ".join(c.text for c in chunks)
    assert "chloroplasts" in joined
    assert "Slide 1" in joined


def test_extract_text(sample_txt):
    chunks = extract_text(sample_txt)
    assert chunks
    assert "nucleus" in chunks[0].text


def test_extract_any_dispatches_by_extension(sample_pdf, sample_pptx, sample_txt):
    assert extract_any(sample_pdf)
    assert extract_any(sample_pptx)
    assert extract_any(sample_txt)


def test_extract_any_rejects_unknown_extension(tmp_path):
    bogus = tmp_path / "notes.docx"
    bogus.write_text("hello")
    with pytest.raises(ingest.UnsupportedFileError):
        extract_any(str(bogus))


def test_empty_pdf_yields_no_chunks(empty_pdf):
    assert extract_pdf(empty_pdf) == []
