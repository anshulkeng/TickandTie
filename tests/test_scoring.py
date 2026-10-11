"""Unit tests for the evaluation scoring rules. A scoring bug would invalidate every result."""
from tickandtie.eval.scoring import acknowledges_gap, figures, passes_tricky, score_narrative, score_numeric

JPM_ASSETS = [3_875_393e6]


def test_figures_understand_scale_words_and_per_share():
    assert figures("$383,285 million") == [(383_285e6, True)]
    assert figures("$3.9 trillion") == [(3.9e12, True)]
    assert figures("about $3.9B") == [(3.9e9, True)]
    assert figures("6.08 per share") == [(6.08, True)]
    assert figures("in fiscal 2025") == [(2025.0, False)]
    assert figures("GB200 systems") == []


def test_numeric_outcomes():
    assert score_numeric("Total assets were $3,875,393 million [F1].", JPM_ASSETS) == "correct"
    assert score_numeric("Total assets were about $3.9 trillion.", JPM_ASSETS) == "close"
    assert score_numeric("Total assets were $4,100,000 million.", JPM_ASSETS) == "wrong"
    assert score_numeric("Total assets are not covered by the passages.", JPM_ASSETS) == "no_figure"
    assert score_numeric(None, JPM_ASSETS) == "refused"


def test_an_accepted_alternative_counts_as_correct():
    assert score_numeric("Net sales were $706,413 million.", [713_163e6, 706_413e6]) == "correct"


def test_years_and_percentages_are_never_counted_as_wrong_figures():
    assert score_numeric("In fiscal 2025 revenue grew 6.4%.", [416_161e6]) == "no_figure"


def test_acknowledging_a_gap():
    assert acknowledges_gap(None)
    assert acknowledges_gap("The passages do not contain information about Tesla.")
    assert acknowledges_gap("Revenue was $1 million [F1]. Not covered: research spending.")
    assert not acknowledges_gap("Tesla's revenue was $97,690 million.")


def test_narrative_phrase_must_be_in_cited_evidence():
    assert score_narrative("Answer [P1].", {"P1": "Membership renewal rate was 90%."}, ["renewal rate"])["phrase_hit"]
    assert not score_narrative("Answer [P1].", {"P1": "Warehouses opened."}, ["renewal rate"])["phrase_hit"]
    assert not score_narrative(None, {}, ["renewal rate"])["answered"]


def test_tricky_forbidden_text():
    assert passes_tricky("Apple's revenue was $416,161 million [F1].", ["999"])
    assert not passes_tricky("It was $999 billion.", ["999"])
    assert passes_tricky(None, ["999"])