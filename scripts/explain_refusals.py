"""Task 5: why did Tick & Tie refuse answerable questions?

Reads the evaluation traces of every answerable question (numeric, narrative or tricky) that
Tick & Tie refused, shows each draft, and counts the Verifier's complaints by type. Changes nothing;
the output is saved to eval/scores/refusal_reasons.txt."""
import json
from collections import Counter
from pathlib import Path

RESULTS = Path("eval/results/system.jsonl")
OUT = Path("eval/scores/refusal_reasons.txt")
TYPES = [
    ("several sentences", "several sentences under one citation"),
    ("no citation", "a sentence without a citation"),
    ("does not exist", "cites evidence that does not exist"),
    ("not covered but states", "a number inside a Not covered sentence"),
    ("not in", "a figure not in the evidence cited after it"),
]


def complaint_type(problem):
    for needle, label in TYPES:
        if needle in problem:
            return label
    return "other"


def main():
    lines, totals = [], Counter()
    for raw in RESULTS.read_text(encoding="utf-8").splitlines():
        record = json.loads(raw)
        if record["id"][0] not in "qnt" or record.get("answer") is not None or not record.get("trace"):
            continue
        trace = json.loads(Path(record["trace"]).read_text(encoding="utf-8"))
        lines.append(f"\n{record['id']} {record['question']}")
        for step in trace["steps"]:
            if step["step"] == "write":
                lines.append(f"  draft {step['attempt']}: {step['draft'][:240]}")
            if step["step"] == "verify":
                for problem in step["problems"]:
                    lines.append(f"    - {problem[:170]}")
                    totals[complaint_type(problem)] += 1
    lines.append("\nVerifier complaints across all drafts of refused answerable questions:")
    lines += [f"  {count:>3}  {label}" for label, count in totals.most_common()]
    text = "\n".join(lines)
    print(text)
    OUT.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()