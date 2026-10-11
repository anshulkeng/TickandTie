"""Unit tests for the Router. A fake model stands in for Ollama (allowed by docs/testing.md)."""
from tickandtie.agents.router import RouteDecision, find_companies, find_metrics, find_years, route


def says(needs_text, sections):
    return lambda question: (RouteDecision(needs_text=needs_text, sections=sections), None)


def broken(question):
    return None, "ConnectionError()"


def test_companies_found_by_name_alias_and_ticker_in_order():
    assert find_companies("Compare Exxon and J&J with AAPL") == ["XOM", "JNJ", "AAPL"]
    assert find_companies("What did Coca-Cola's bottlers do?") == ["KO"]


def test_common_words_are_not_mistaken_for_tickers():
    assert find_companies("What is the cost of the cat food business?") == []


def test_years_in_several_formats():
    assert find_years("fiscal 2024 vs FY25 and FY2026") == [2024, 2025, 2026]
    assert find_years("What is Apple's latest revenue?") == []


def test_longer_metric_phrases_win():
    assert find_metrics("diluted earnings per share") == ["eps_diluted"]
    assert find_metrics("operating cash flow") == ["operating_cash_flow"]
    assert set(find_metrics("net sales and total assets")) == {"revenue", "total_assets"}
    assert find_metrics("How does profitability look?") == []


def test_question_without_a_covered_company_is_refused():
    plan = route("What was Tesla's revenue in 2025?", decide=broken)
    assert plan.refusal and "Apple" in plan.refusal


def test_figures_only_question_skips_text_when_the_model_agrees():
    plan = route("How much cash did Costco have at the end of FY24?", decide=says(False, []))
    assert (plan.tickers, plan.fiscal_years, plan.metrics) == (["COST"], [2024], ["cash"])
    assert plan.needs_numbers and not plan.needs_text and plan.sections == []


def test_why_questions_always_get_text_even_if_the_model_says_no():
    plan = route("Why did NVIDIA's revenue grow so fast?", decide=says(False, ["Item 7"]))
    assert plan.needs_text and plan.sections == ["Item 7"]


def test_model_failure_falls_back_to_default_sections_and_is_noted():
    plan = route("What risks does Pfizer describe?", decide=broken)
    assert plan.needs_text and plan.sections == ["Item 1", "Item 1A", "Item 7"]
    assert "failed" in plan.notes[0]

def never(question):
    raise AssertionError("the model should not have been called")


def test_investment_advice_is_refused_before_any_model_call():
    for question in ["Should I buy NVIDIA stock?",
                     "Is Apple a good investment?",
                     "Is it worth buying Coca-Cola shares?",
                     "Buy or sell Exxon?",
                     "What is the price target for Microsoft?"]:
        plan = route(question, decide=never)
        assert plan.refusal and "investment advice" in plan.refusal, question


def test_questions_about_a_company_investing_are_not_mistaken_for_advice():
    plan = route("How much did Apple invest in research and development in fiscal 2025?", decide=says(False, []))
    assert plan.refusal is None and plan.metrics == ["rnd"]
    plan = route("What does Verizon say about investment in its network?", decide=says(True, ["Item 7"]))
    assert plan.refusal is None