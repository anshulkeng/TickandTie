"""Unit tests for the Verifier: the plain-code gate every answer must pass."""
from tickandtie.agents.evidence import Evidence, numbers_in
from tickandtie.agents.verifier import verify


def evidence():
    ev = Evidence()
    ev.add("fact", "Apple revenue, fiscal 2025: $416,161 million.", numbers_in("$416,161 million"))  # F1
    ev.add("fact", "Change in Apple revenue from fiscal 2024 to fiscal 2025: +$25,126 million (+6.4%).",
           numbers_in("+$25,126 million (+6.4%)"))  # F2
    ev.add("passage", "Apple 10-K: The Company has approximately 166,000 full-time employees.",
           numbers_in("The Company has approximately 166,000 full-time employees."))  # P1
    return ev


def test_correct_answer_passes():
    answer = ("Apple's revenue in fiscal 2025 was $416,161 million [F1]. "
              "That was up $25,126 million, or 6.4%, from fiscal 2024 [F2].")
    assert verify(answer, evidence()) == []


def test_small_rounding_passes_but_a_wrong_number_fails():
    assert verify("Revenue was about $416,000 million [F1].", evidence()) == []
    problems = verify("Revenue was $451,161 million [F1].", evidence())
    assert len(problems) == 1 and "451,161" in problems[0]


def test_number_must_come_from_the_evidence_its_sentence_cites():
    assert verify("Apple has about 166,000 full-time employees [F1].", evidence())
    assert verify("Apple has about 166,000 full-time employees [P1].", evidence()) == []


def test_sentence_without_a_citation_fails():
    assert "no citation" in verify("Revenue was $416,161 million.", evidence())[0]


def test_citing_evidence_that_does_not_exist_fails():
    assert "does not exist" in verify("Revenue was $416,161 million [F9].", evidence())[0]


def test_invented_percentage_fails():
    assert verify("Revenue grew 7% from fiscal 2024 [F2].", evidence())


def test_years_dates_form_names_and_items_are_not_figures():
    answer = ("In fiscal 2025, which ended September 27, 2025, Apple's 10-K Item 7 "
              "reported revenue of $416,161 million [F1].")
    assert verify(answer, evidence()) == []


def test_not_covered_sentence_needs_no_citation_but_may_not_state_numbers():
    base = "Revenue was $416,161 million [F1]. "
    assert verify(base + "Not covered: segment details.", evidence()) == []
    assert verify(base + "Not covered: the 3 business segments.", evidence())


def test_covid_19_is_a_name_not_a_figure():
    assert verify("Apple discusses lower COVID-19 demand [P1].", evidence()) == []


def test_empty_answer_fails():
    assert verify("   ", evidence()) == ["the answer is empty"]

def test_each_number_is_checked_against_the_citation_that_follows_it():
    # Found in the first live run: a figure from a passage was followed by a citation to a fact.
    mixed_up = "Apple has about 166,000 employees [F1], and revenue was $416,161 million [P1]."
    assert len(verify(mixed_up, evidence())) == 2
    correct = "Apple has about 166,000 employees [P1], and revenue was $416,161 million [F1]."
    assert verify(correct, evidence()) == []

def test_each_sentence_needs_its_own_citation():
    # Found in the second live run: three sentences shared one citation placed after the last one.
    answer = "Revenue grew strongly. Apple has about 166,000 employees. [P1]"
    assert any("several sentences" in problem for problem in verify(answer, evidence()))
    assert verify("Apple Inc. has about 166,000 employees [P1].", evidence()) == []
    assert verify("The U.S. workforce is about 166,000 employees [P1].", evidence()) == []