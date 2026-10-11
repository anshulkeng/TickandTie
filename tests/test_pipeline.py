"""End-to-end tests of the pipeline graph with fake models and search, on a real in-memory DuckDB."""
from datetime import date
from pathlib import Path

import duckdb

from tickandtie.agents.pipeline import NOT_VERIFIED, Deps, ask
from tickandtie.agents.router import RouteDecision
from tickandtie.ingest.xbrl_facts import CREATE

CONCEPT = "RevenueFromContractWithCustomerExcludingAssessedTax"


def row(concept, value, start, end, fiscal_year, accession, filed):
    start_date, end_date = date.fromisoformat(start), date.fromisoformat(end)
    return ("AAPL", "0000320193", "us-gaap", concept, concept, "USD", start_date, end_date,
            (end_date - start_date).days, float(value), accession, fiscal_year, "FY", "10-K",
            date.fromisoformat(filed), None)


def database():
    con = duckdb.connect()
    con.execute(CREATE)
    con.executemany("INSERT INTO facts VALUES (" + ", ".join(["?"] * 16) + ")", [
        row(CONCEPT, 391_035e6, "2023-10-01", "2024-09-28", 2024, "a24", "2024-11-01"),
        row(CONCEPT, 416_161e6, "2024-09-29", "2025-09-27", 2025, "a25", "2025-10-31"),
    ])
    return con


def no_text(question):
    return RouteDecision(needs_text=False, sections=[]), None


def risk_sections(question):
    return RouteDecision(needs_text=True, sections=["Item 1A"]), None


def never(*args, **kwargs):
    raise AssertionError("the model should not have been called")


def replies(*texts):
    queue = list(texts)
    return lambda messages: queue.pop(0) if len(queue) > 1 else queue[0]


class FakeSearcher:
    def __init__(self, by_items):
        self.by_items = by_items
        self.calls = []

    def search(self, question, k=8, **filters):
        self.calls.append(filters)
        return self.by_items.get(tuple(filters.get("items") or []), [])[:k]


def deps(tmp_path, **overrides):
    return Deps(con=database(), trace_dir=tmp_path, **overrides)


def test_figures_question_gives_a_verified_answer_and_a_trace(tmp_path):
    result = ask("What was Apple's revenue in fiscal 2025?",
                 deps(tmp_path, decide=no_text, chat=replies("Apple's revenue in fiscal 2025 was $416,161 million [F1].")))
    assert result.answer == "Apple's revenue in fiscal 2025 was $416,161 million [F1]."
    assert result.attempts == 1 and "F1" in result.sources
    assert Path(result.trace_path).exists()


def test_two_years_add_a_computed_change(tmp_path):
    result = ask("Apple revenue fiscal 2024 vs fiscal 2025",
                 deps(tmp_path, decide=no_text, chat=replies("Apple's revenue rose $25,126 million, or 6.4% [F3].")))
    assert "+$25,126 million (+6.4%)" in result.evidence.items["F3"].text
    assert result.answer is not None


def test_a_wrong_number_is_never_shown(tmp_path):
    result = ask("What was Apple's revenue in fiscal 2025?",
                 deps(tmp_path, decide=no_text, chat=replies("Apple's revenue was $451,161 million [F1].")))
    assert result.answer is None and result.refusal == NOT_VERIFIED
    assert result.attempts == 2 and len(result.removed) == 1
    assert "451,161" not in result.refusal


def test_partial_answer_keeps_only_verified_sentences(tmp_path):
    draft = "Apple's revenue was $416,161 million [F1]. Apple runs 999 stores [F1]."
    result = ask("What was Apple's revenue in fiscal 2025?", deps(tmp_path, decide=no_text, chat=replies(draft)))
    assert result.answer == "Apple's revenue was $416,161 million [F1]."
    assert len(result.removed) == 1 and "999" in result.removed[0]["sentence"]


def test_uncovered_company_is_refused_without_calling_any_model(tmp_path):
    result = ask("What was Tesla's revenue in 2025?", deps(tmp_path, decide=never, chat=never))
    assert result.answer is None and "Apple" in result.refusal and result.attempts == 0


def test_narrow_text_search_is_widened_when_it_finds_too_little(tmp_path):
    chunk = {"ticker": "AAPL", "period_end": "2025-09-27", "item": "Item 1", "accession": "a25",
             "text": "The Company depends on component suppliers."}
    searcher = FakeSearcher({("Item 1A",): [], (): [chunk, dict(chunk)]})
    result = ask("What risks does Apple describe?",
                 deps(tmp_path, decide=risk_sections, searcher=searcher,
                      chat=replies("Apple depends on component suppliers [P1].")))
    assert searcher.calls[0]["items"] == ["Item 1A"] and "items" not in searcher.calls[1]
    assert any("every section was searched" in note for note in result.notes)
    assert result.answer == "Apple depends on component suppliers [P1]."

def test_answers_list_the_periods_of_the_figures_they_cite(tmp_path):
    result = ask("Apple revenue fiscal 2024 vs fiscal 2025",
                 deps(tmp_path, decide=no_text, chat=replies("Apple's revenue rose $25,126 million, or 6.4% [F3].")))
    assert result.periods == ["Apple fiscal 2024: 2023-10-01 to 2024-09-28",
                              "Apple fiscal 2025: 2024-09-29 to 2025-09-27"]