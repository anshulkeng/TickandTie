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

def test_risk_factor_change_questions_go_to_the_diff_without_a_model():
    plan = route("What changed in Pfizer's risk factors?", decide=never)
    assert plan.task == "risk_diff" and plan.tickers == ["PFE"] and plan.refusal is None
    plan = route("What new risks did Microsoft add in fiscal 2026?", decide=never)
    assert plan.task == "risk_diff" and plan.fiscal_years == [2026]


def test_ordinary_risk_questions_are_not_mistaken_for_a_diff():
    for question in ["What risks does Pfizer describe?", "How does Exxon describe climate change risks?",
                     "How does JPMorgan manage interest rate risk?"]:
        assert route(question, decide=says(True, ["Item 1A"])).task == "answer", question


def test_a_risk_diff_needs_exactly_one_company():
    plan = route("Compare the risk factors of Apple and Microsoft", decide=never)
    assert plan.refusal and "one company" in plan.refusal

def test_how_did_a_company_do_questions_get_the_headline_figures():
    # Found while trying the website: "How is apple doing in 2022" named no figure and was refused.
    for question in ["How is apple doing in 2022", "How did Walmart perform in fiscal 2025?",
                     "What was Pfizer's performance in 2024?"]:
        plan = route(question, decide=says(True, ["Item 7"]))
        assert plan.metrics == ["revenue", "net_income", "eps_diluted"] and plan.needs_numbers, question


def test_questions_with_their_own_figure_or_about_methods_are_unchanged():
    assert route("How does JPMorgan manage interest rate risk?", decide=says(True, ["Item 7A"])).metrics == []
    plan = route("How did Walmart's net income change from FY2025 to FY2026?", decide=says(True, ["Item 7"]))
    assert plan.metrics == ["net_income"]