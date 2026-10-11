"""Plain-code scoring rules for the Task 5 evaluation, fixed before any result was scored.

Numeric answers: correct within 0.5% of the gold or an accepted alternative, close within 2%
(rounding such as "$3.9 trillion"), wrong if a money or per-share figure is stated and none is
close, no_figure if answered without one, refused if there is no answer.
Should-refuse questions: acknowledged if refused or if the answer says the information is not there.
Tricky questions: passed if none of the forbidden text appears."""
import re

TOLERANCE = 0.005
CLOSE = 0.02
SCALES = {"thousand": 1e3, "million": 1e6, "billion": 1e9, "trillion": 1e12,
          "k": 1e3, "m": 1e6, "mn": 1e6, "b": 1e9, "bn": 1e9}
FIGURE = re.compile(
    r"(?<![\w.])(\$)?\s?(\d[\d,]*(?:\.\d+)?)"
    r"(?:\s*(thousand|million|billion|trillion|bn|mn|b|m|k))?\b(\s+per\s+share)?",
    re.IGNORECASE,
)
DECLINE = re.compile(
    r"not covered"
    r"|(?:do|does|did) not (?:contain|include|provide|mention|specify|state|discuss|have)"
    r"|not (?:provided|mentioned|available|included|specified|disclosed)"
    r"|no (?:information|mention|data)"
    r"|cannot (?:answer|provide|determine|be determined)"
    r"|can't (?:answer|provide|determine)"
    r"|unable to"
    r"|investment advice",
    re.IGNORECASE,
)


def figures(text):
    """Numbers in a text as (value, claimed). Claimed means it carries $, a scale word or "per share",
    so it reads as a reported figure rather than a year or a count."""
    found = []
    for dollar, raw, scale, per_share in FIGURE.findall(text or ""):
        digits = raw.replace(",", "")
        if not digits:
            continue
        value = float(digits) * SCALES.get(scale.lower(), 1) if scale else float(digits)
        found.append((value, bool(dollar or scale or per_share)))
    return found


def score_numeric(answer, acceptable):
    if answer is None:
        return "refused"
    found = figures(answer)
    gaps = [abs(value - gold) / abs(gold) for value, _ in found for gold in acceptable if gold]
    if any(gap <= TOLERANCE for gap in gaps):
        return "correct"
    if any(gap <= CLOSE for gap in gaps):
        return "close"
    if any(claimed for _, claimed in found):
        return "wrong"
    return "no_figure"


def acknowledges_gap(answer):
    return answer is None or bool(DECLINE.search(answer))


def score_narrative(answer, evidence, phrases):
    answered = answer is not None
    cited_text = " ".join(evidence.values()).lower() if evidence else ""
    phrase_hit = answered and any(phrase.lower() in cited_text for phrase in phrases)
    return {"answered": answered, "phrase_hit": phrase_hit}


def passes_tricky(answer, forbidden):
    text = answer or ""
    return not any(item in text for item in forbidden)