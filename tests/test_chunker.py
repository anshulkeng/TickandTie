"""Unit tests for chunking. No network needed."""
from tickandtie.index.chunker import MAX_CHARS, chunk_filing, chunk_text


def no_spaces(text):
    return "".join(text.split())


def test_short_paragraphs_share_a_chunk():
    text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    assert chunk_text(text) == [text]


def test_no_chunk_is_over_the_limit_even_for_tables():
    table = " ".join(["1,234"] * 2000)  # no sentence ends at all
    prose = ("A sentence about risk. " * 300).strip()
    for text in (table, prose, table + "\n\n" + prose):
        assert all(len(chunk) <= MAX_CHARS for chunk in chunk_text(text))


def test_chunking_never_drops_text():
    text = "\n\n".join(["Intro line.", ("Revenue grew. " * 150).strip(), " ".join(["9"] * 3000)])
    assert no_spaces("".join(chunk_text(text))) == no_spaces(text)


def test_pointer_items_are_skipped_and_ids_are_unique():
    record = {
        "ticker": "TEST", "cik": "1", "accession": "a", "period_end": "2025-12-31",
        "filing_date": "2026-02-01",
        "items": {"Item 1A": ("Risk. " * 1000).strip(), "Item 7A": "See Item 7."},
        "sources": {"Item 1A": "Item 1A", "Item 7A": "Item 7A"},
    }
    chunks, skipped = chunk_filing(record)
    assert skipped == ["Item 7A"]
    assert len(chunks) > 1
    assert len({chunk["chunk_id"] for chunk in chunks}) == len(chunks)