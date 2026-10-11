"""Verifier: plain-code checks on the Writer's answer. No language model (decision 0014).

An answer passes only if every sentence carries its own citation, every citation exists, and every
number matches the evidence cited right after it: a fact within 0.5%, or a passage that contains it exactly."""
import re

TOLERANCE = 0.005
NOT_COVERED = "Not covered:"
CITATION = re.compile(r"\[([FP]\d+(?:\s*,\s*[FP]\d+)*)\]")
CLAIM_END = re.compile(r"(?<=\])[.!?]?\s+")
FIGURE = re.compile(r"(?<![\w.\-/])(\$)?(\d[\d,]*(?:\.\d+)?)(\s?%)?")
INNER_BREAK = re.compile(r"([\w%)]+)\.\s+(?=[A-Z])")
ABBREVIATIONS = {"inc", "corp", "co", "ltd", "llc", "plc", "no", "vs", "etc", "mr", "ms", "dr", "st"}
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"

# Text that contains digits but is not a figure: dates, form names, Item numbers, fiscal-year labels, citations.
NOT_FIGURES = [
    re.compile(rf"\b(?:{MONTHS})\s+\d{{1,2}},?\s+\d{{4}}\b"),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b10-[KQ]\b"),
    re.compile(r"\bItem\s+\d+[A-C]?\b", re.IGNORECASE),
    re.compile(r"\b(?:fiscal\s+(?:year\s+)?|FY\s?)\d{2,4}\b", re.IGNORECASE),
    CITATION,
]


def split_claims(answer):
    """A claim runs up to and including its citation, so abbreviations like "Inc." never split one."""
    return [claim.strip() for claim in CLAIM_END.split(answer.strip()) if claim.strip()]


def inner_sentence_breaks(claim):
    """Sentence ends inside a claim, ignoring abbreviations such as Inc. and initials such as U.S."""
    body = CITATION.sub(" ", claim)
    return [match for match in INNER_BREAK.finditer(body)
            if match.group(1).lower() not in ABBREVIATIONS and len(match.group(1)) > 1]


def figures(claim):
    """The numbers a claim states, as (text, value, end position). Plain years such as 2025 are not figures."""
    text = claim
    for pattern in NOT_FIGURES:
        text = pattern.sub(lambda match: " " * len(match.group()), text)  # same length keeps positions
    found = []
    for match in FIGURE.finditer(text):
        dollar, raw, percent = match.groups()
        raw = raw.rstrip(",")
        digits = raw.replace(",", "")
        if not digits:
            continue
        value = float(digits)
        if not dollar and not percent and value.is_integer() and 1990 <= value <= 2100:
            continue
        found.append((raw, value, match.end()))
    return found


def matches(value, allowed, tolerance):
    return any(abs(value - other) <= tolerance * abs(other) for other in allowed)


def numbers_of(evidence, ids, kind):
    return [n for item_id in ids if evidence.items[item_id].kind == kind for n in evidence.items[item_id].numbers]


def verify(answer, evidence):
    """Return a list of problems. An empty list means the answer passes."""
    if not answer.strip():
        return ["the answer is empty"]
    problems = []
    for number, claim in enumerate(split_claims(answer), start=1):
        if claim.startswith(NOT_COVERED):
            problems += [f"claim {number} says something is not covered but states {raw}"
                         for raw, _, _ in figures(claim)]
            continue
        groups = [(match.end(), [item.strip() for item in match.group(1).split(",")])
                  for match in CITATION.finditer(claim)]
        if not groups:
            problems.append(f"claim {number} has no citation: {claim[:60]!r}")
            continue
        unknown = [item for _, ids in groups for item in ids if item not in evidence.items]
        if unknown:
            problems.append(f"claim {number} cites evidence that does not exist: {', '.join(unknown)}")
            continue
        if inner_sentence_breaks(claim):
            problems.append(f"claim {number} runs several sentences under one citation; "
                            f"end every sentence with its own citation")
        for raw, value, end in figures(claim):
            # The citation that follows a number is the one a reader would check, so that is the one tested.
            ids = next((ids for group_end, ids in groups if group_end > end), groups[-1][1])
            if not (matches(value, numbers_of(evidence, ids, "fact"), TOLERANCE)
                    or matches(value, numbers_of(evidence, ids, "passage"), 0.0)):
                problems.append(f"claim {number} states {raw}, which is not in {', '.join(ids)}, "
                                f"the evidence cited right after it")
    return problems