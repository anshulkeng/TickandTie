"""Task 5, step 1: build the evaluation question set, eval/questions.jsonl.

Numeric questions are generated from the XBRL facts with their own SQL, separate from the
Numbers agent's lookup code; the metric rules (which concepts count) are shared on purpose,
because they are the definition being tested. Narrative, should-refuse and tricky questions are
hand-written in eval/questions_handwritten.json. None of the ten calibration questions in
scripts/check_pipeline.py may appear here."""
import json
from collections import Counter
from pathlib import Path

import duckdb
import numpy as np

from scripts.check_pipeline import QUESTIONS as CALIBRATION
from tickandtie import config
from tickandtie.agents.numbers import CONCEPT_OVERRIDES, METRICS, format_value
from tickandtie.ingest.xbrl_facts import DB_PATH

OUT = Path("eval/questions.jsonl")
HANDWRITTEN = Path("eval/questions_handwritten.json")
SEED = 2026
EVAL_METRICS = ["revenue", "net_income", "eps_diluted", "total_assets"]
TEMPLATES = {
    "revenue": ["What was {name}'s revenue in fiscal {year}?",
                "How much revenue did {name} report for fiscal {year}?",
                "What were {name}'s total sales in fiscal {year}?"],
    "net_income": ["What was {name}'s net income in fiscal {year}?",
                   "How much profit did {name} make in fiscal {year}?",
                   "What were {name}'s net earnings for fiscal {year}?"],
    "eps_diluted": ["What was {name}'s diluted earnings per share in fiscal {year}?",
                    "What diluted EPS did {name} report for fiscal {year}?"],
    "total_assets": ["What were {name}'s total assets at the end of fiscal {year}?",
                     "How much did {name} hold in total assets at the end of fiscal {year}?"],
}

LATEST_YEARS = """
    SELECT filing_fy, max(period_end) FROM facts
    WHERE ticker = ? AND form = '10-K' AND filing_fp = 'FY' AND taxonomy = 'us-gaap'
      AND duration_days BETWEEN 350 AND 380 AND filing_fy IS NOT NULL
    GROUP BY filing_fy ORDER BY filing_fy DESC LIMIT 3"""

LATEST_VALUE = """
    SELECT value FROM facts
    WHERE ticker = ? AND taxonomy = 'us-gaap' AND concept = ? AND unit = ? AND period_end = ? AND {period}
    ORDER BY filed DESC LIMIT 1"""


def gold_values(con, ticker, metric, year_end):
    """Every reported value for the metric's concepts in that year, in rule order: [(concept, value)]."""
    rule = METRICS[metric]
    period = "duration_days BETWEEN 350 AND 380" if rule.kind == "duration" else "period_start IS NULL"
    found = []
    for concept in CONCEPT_OVERRIDES.get((ticker, metric), rule.concepts):
        row = con.execute(LATEST_VALUE.format(period=period), [ticker, concept, rule.unit, year_end]).fetchone()
        if row:
            found.append((concept, row[0]))
    return found


def numeric_questions(con, rng):
    calibration = {question for question, _ in CALIBRATION}
    questions = []
    for ticker in config.COMPANIES:
        name = config.COMPANY_NAMES[ticker]
        years = con.execute(LATEST_YEARS, [ticker]).fetchall()
        for metric in EVAL_METRICS:
            fiscal_year, year_end = years[int(rng.integers(len(years)))]
            found = gold_values(con, ticker, metric, year_end)
            if not found:
                continue
            templates = TEMPLATES[metric]
            choice = int(rng.integers(len(templates)))
            question = templates[choice].format(name=name, year=fiscal_year)
            if question in calibration:
                question = templates[(choice + 1) % len(templates)].format(name=name, year=fiscal_year)
            concept, value = found[0]
            questions.append({
                "id": f"q{len(questions) + 1:02d}", "kind": "numeric", "question": question,
                "ticker": ticker, "metric": metric, "fiscal_year": fiscal_year, "period_end": str(year_end),
                "gold_concept": concept, "gold_value": value,
                "gold_display": format_value(value, METRICS[metric].unit),
                "acceptable_values": [value for _, value in found],
            })
    return questions


def main():
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        numeric = numeric_questions(con, np.random.default_rng(SEED))
    handwritten = json.loads(HANDWRITTEN.read_text(encoding="utf-8"))
    questions = numeric + handwritten
    ids = [q["id"] for q in questions]
    assert len(ids) == len(set(ids)), "duplicate question ids"
    clashes = {q["question"] for q in questions} & {question for question, _ in CALIBRATION}
    assert not clashes, f"calibration questions in the evaluation set: {clashes}"
    OUT.write_text("".join(json.dumps(q, ensure_ascii=False) + "\n" for q in questions), encoding="utf-8")

    counts = Counter(q["kind"] for q in questions)
    print(f"{len(questions)} questions -> {OUT}: " + ", ".join(f"{n} {k}" for k, n in counts.items()))
    print(f"\n{'id':<4} {'ticker':<5} {'FY':<5} {'gold':>20}  {'concept':<55} question")
    for q in numeric:
        extra = f" (also {len(q['acceptable_values']) - 1})" if len(q["acceptable_values"]) > 1 else ""
        print(f"{q['id']:<4} {q['ticker']:<5} {q['fiscal_year']:<5} {q['gold_display']:>20}  "
              f"{q['gold_concept'] + extra:<55} {q['question']}")


if __name__ == "__main__":
    main()