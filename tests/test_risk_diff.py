"""Unit tests for the risk-factor diff on small made-up reports."""
from tickandtie.diff.risk_diff import diff_texts, paragraphs

BASE = [
    "Item 1A. Risk Factors",
    "Macroeconomic Risks",
    "The Company depends on global economic conditions, and a downturn in consumer spending could reduce demand "
    "for its products and services across many regions.",
    "The Company faces intense competition in every market it serves, and competitors may introduce new products "
    "at lower prices than the Company can match.",
    "Legal Risks",
    "The Company is subject to complex laws in many countries, and changes in those laws could increase costs or "
    "restrict how the Company operates its business.",
]


def text(blocks):
    return "\n\n".join(blocks)


def test_headings_are_attached_and_the_title_is_dropped():
    found = paragraphs(text(BASE))
    assert [p.heading for p in found] == ["Macroeconomic Risks", "Macroeconomic Risks", "Legal Risks"]


def test_identical_reports_have_no_changes():
    result = diff_texts(text(BASE), text(BASE))
    assert result.changes == [] and result.unchanged == 3


def test_moving_a_paragraph_is_not_a_change():
    moved = [BASE[0], BASE[1], BASE[3], BASE[2], BASE[4], BASE[5]]
    assert diff_texts(text(BASE), text(moved)).changes == []


def test_new_removed_and_changed_paragraphs():
    newer = BASE[:3] + [
        BASE[3] + " Competitors using artificial intelligence may move faster.",
        "Cybersecurity Risks",
        "Attacks on the Company's information systems could disrupt operations, expose confidential data and lead "
        "to regulatory penalties and lasting harm to its reputation.",
    ]
    result = diff_texts(text(BASE), text(newer))
    assert sorted(c.kind for c in result.changes) == ["changed", "new", "removed"]
    changed = next(c for c in result.changes if c.kind == "changed")
    assert changed.added == ["Competitors using artificial intelligence may move faster."] and changed.removed == []
    assert next(c for c in result.changes if c.kind == "new").heading == "Cybersecurity Risks"
    assert next(c for c in result.changes if c.kind == "removed").heading == "Legal Risks"


def test_each_old_paragraph_matches_at_most_one_new_paragraph():
    newer = BASE[:4] + [BASE[3] + " This risk has grown."] + BASE[4:]
    result = diff_texts(text(BASE), text(newer))
    assert [c.kind for c in result.changes] == ["new"] and result.unchanged == 3

MOVED = "Supply disruptions in one region can affect sales in every other region."
LONG = ("The Company faces intense competition in every market it serves, and competitors that have significant "
        "resources and experience may introduce new products at lower prices than the Company can match.")


def test_text_moved_between_paragraphs_is_not_a_change():
    older = text([BASE[0], BASE[1], BASE[2] + " " + MOVED, BASE[3], BASE[4], BASE[5]])
    newer = text([BASE[0], BASE[1], BASE[2], BASE[3] + " " + MOVED, BASE[4], BASE[5]])
    assert diff_texts(older, newer).changes == []


def test_a_paragraph_broken_mid_sentence_is_joined_back():
    first, second = LONG.split(" introduce ")
    older = text(BASE[:3] + [LONG] + BASE[4:])
    newer = text(BASE[:3] + [first, "introduce " + second] + BASE[4:])
    assert diff_texts(older, newer).changes == []


def test_a_small_edit_is_shown_word_by_word():
    from tickandtie.diff.risk_diff import word_diff
    edited = BASE[:3] + [BASE[3].replace("lower prices", "much lower prices")] + BASE[4:]
    change = diff_texts(text(BASE), text(edited)).changes[0]
    assert change.kind == "changed" and change.added == [] and change.removed == []
    assert len(change.edits) == 1 and "{+much+}" in word_diff(*change.edits[0])


def test_tiny_fragments_are_ignored():
    newer = BASE[:3] + [BASE[3] + " See below."] + BASE[4:]
    assert diff_texts(text(BASE), text(newer)).changes == []