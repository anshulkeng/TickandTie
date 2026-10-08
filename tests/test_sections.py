"""Unit tests for 10-K section handling. None of these touch the network."""
from tickandtie.ingest import sections
from tickandtie.ingest.sections import KEEP_ITEMS, clean, latest_10ks, pick_items


def test_clean_drops_page_footer_and_non_breaking_spaces():
    text = "Item 1A.\xa0\xa0Risk Factors\n\nApple Inc. | 2025 Form 10-K | 20\n\nDemand may fall."
    assert clean(text) == "Item 1A. Risk Factors\n\nDemand may fall."


def test_clean_keeps_a_line_that_ends_in_a_year():
    line = "This Annual Report on Form 10-K for fiscal 2025"
    assert clean(line) == line


def test_clean_keeps_a_long_sentence_that_mentions_form_10k():
    sentence = ("Refer to Part II, Item 7 of this Form 10-K for a discussion of results, "
                "which we describe in more detail on page 45")
    assert clean(sentence) == sentence


def test_item_8_pointer_falls_back_to_item_15():
    raw = {"Item 8": "See the financial statements.", "Item 15": "x" * 25_000}
    items, sources = pick_items(raw)
    assert items["Item 8"] == "x" * 25_000
    assert sources["Item 8"] == "Item 15"


def test_item_8_pointer_is_kept_when_item_15_is_not_usable():
    raw = {"Item 8": "Reference is made to the Financial Section.", "Item 15": "Exhibits"}
    items, sources = pick_items(raw)
    assert items["Item 8"] == raw["Item 8"]
    assert sources["Item 8"] == "Item 8"


def test_missing_items_come_back_empty():
    items, sources = pick_items({})
    assert all(items[item] == "" for item in KEEP_ITEMS)
    assert all(sources[item] == item for item in KEEP_ITEMS)


class FakeClient:
    def __init__(self, ticker_cik, filings_by_cik):
        self._ticker_cik = ticker_cik
        self._filings = filings_by_cik

    def ticker_to_cik(self, ticker):
        return self._ticker_cik

    def filings(self, cik):
        return self._filings[cik]


def test_latest_10ks_searches_predecessor_cik_and_ignores_other_forms(monkeypatch):
    monkeypatch.setattr(sections.config, "PREDECESSOR_CIKS", {"XOM": ["OLD"]})
    client = FakeClient("NEW", {
        "NEW": [{"form": "8-K", "accessionNumber": "a1", "filingDate": "2026-07-01"}],
        "OLD": [
            {"form": "10-K", "accessionNumber": "b1", "filingDate": "2024-02-28"},
            {"form": "10-K", "accessionNumber": "b2", "filingDate": "2026-02-18"},
            {"form": "10-K/A", "accessionNumber": "b3", "filingDate": "2026-03-01"},
            {"form": "10-K", "accessionNumber": "b0", "filingDate": "2025-02-19"},
        ],
    })
    rows = latest_10ks(client, "XOM", 2)
    assert [row["accessionNumber"] for row in rows] == ["b2", "b0"]
    assert all(row["cik"] == "OLD" for row in rows)