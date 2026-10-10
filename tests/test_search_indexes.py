"""Unit tests for the search index helpers. No network and no embedding model needed."""
from tickandtie.index.search_indexes import BM25Index, header, tokenize, where_filter


def make_chunk(chunk_id, ticker, item, text):
    return {"chunk_id": chunk_id, "ticker": ticker, "period_end": "2025-12-31",
            "item": item, "text": text}


def test_header_names_company_period_and_section():
    chunk = make_chunk("x", "AAPL", "Item 1A", "...")
    assert header(chunk) == "Apple (AAPL) 10-K, period ending 2025-12-31, Item 1A Risk Factors"


def test_tokenize_lowercases_and_drops_punctuation():
    assert tokenize("Goodwill impairment, 2025!") == ["goodwill", "impairment", "2025"]


def test_where_filter_combines_only_what_is_given():
    assert where_filter() is None
    assert where_filter(ticker="AAPL") == {"ticker": "AAPL"}
    assert where_filter(ticker="AAPL", items=["Item 1A"]) == {
        "$and": [{"ticker": "AAPL"}, {"item": {"$in": ["Item 1A"]}}]}


def test_bm25_ranks_exact_terms_first_and_respects_filters():
    chunks = [
        make_chunk("a", "AAPL", "Item 7", "Revenue grew in every region."),
        make_chunk("b", "PFE", "Item 8", "We recorded a goodwill impairment charge."),
        make_chunk("c", "AAPL", "Item 8", "No goodwill impairment was recorded this year."),
    ]
    index = BM25Index(chunks)
    assert index.search("goodwill impairment", k=2) [0] in {"b", "c"}
    assert index.search("goodwill impairment", ticker="AAPL") == ["c"]