"""Task 5, step 3a: score the frozen results with the plain-code rules in tickandtie/eval/scoring.py.

    python -m scripts.score_eval

Writes eval/scores/code_details.jsonl and eval/scores/code_scores.json, prints the summary, and prints
every should-refuse and tricky answer and every wrong figure in full, so they can be read by hand."""
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

from tickandtie.eval.scoring import acknowledges_gap, passes_tricky, score_narrative, score_numeric

QUESTIONS = Path("eval/questions.jsonl")
RESULTS = Path("eval/results")
SCORES = Path("eval/scores")
MODES = ("system", "baseline")


def load(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def percentile(values, share):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(share * (len(ordered) - 1)))]


def shown(record, width=300):
    text = record.get("answer") or f"[REFUSED] {record.get('refusal')}"
    return text.replace("\n", " ")[:width]


def main():
    modes = tuple(sys.argv[1:]) or MODES  # for example: python -m scripts.score_eval system_v2
    suffix = "" if modes == MODES else "_" + "_".join(modes)
    questions = {q["id"]: q for q in load(QUESTIONS)}
    results = {mode: {r["id"]: r for r in load(RESULTS / f"{mode}.jsonl")} for mode in modes}
    SCORES.mkdir(parents=True, exist_ok=True)
    details, summary = [], {}
    for mode in modes:
        records = results[mode]
        counts = {kind: Counter() for kind in ("numeric", "narrative", "refuse", "tricky")}
        for qid, q in questions.items():
            record = records[qid]
            row = {"id": qid, "mode": mode, "kind": q["kind"]}
            if q["kind"] == "numeric":
                row["outcome"] = score_numeric(record.get("answer"), q["acceptable_values"])
                counts["numeric"][row["outcome"]] += 1
            elif q["kind"] == "narrative":
                row.update(score_narrative(record.get("answer"), record.get("evidence") or {}, q["phrases"]))
                counts["narrative"]["answered" if row["answered"] else "refused"] += 1
                counts["narrative"]["phrase_in_cited_evidence"] += row["phrase_hit"]
            elif q["kind"] == "refuse":
                row["acknowledged"] = acknowledges_gap(record.get("answer"))
                counts["refuse"]["acknowledged" if row["acknowledged"] else "answered_anyway"] += 1
            else:
                row["passed"] = passes_tricky(record.get("answer"), q["forbidden"])
                counts["tricky"]["passed" if row["passed"] else "failed"] += 1
            details.append(row)
        seconds = [r["seconds"] for r in records.values() if r.get("seconds") is not None]
        answerable = [qid for qid, q in questions.items() if q["kind"] in ("numeric", "narrative")]
        summary[mode] = {
            **{kind: dict(counter) for kind, counter in counts.items()},
            "refused_answerable": sum(records[qid].get("answer") is None for qid in answerable),
            "rewrites": sum(r.get("attempts") == 2 for r in records.values()),
            "partial_answers": sum(bool(r.get("removed")) and r.get("answer") is not None for r in records.values()),
            "seconds_median": statistics.median(seconds),
            "seconds_p90": percentile(seconds, 0.9),
        }

    (SCORES / f"code_details{suffix}.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in details), encoding="utf-8")
    (SCORES / f"code_scores{suffix}.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")

    for mode, s in summary.items():
        n, r, t, a = s["numeric"], s["refuse"], s["tricky"], s["narrative"]
        print(f"\n=== {mode} ===")
        print(f"Numeric (48): correct {n.get('correct', 0)}, close {n.get('close', 0)}, WRONG {n.get('wrong', 0)}, "
              f"no figure {n.get('no_figure', 0)}, refused {n.get('refused', 0)}")
        print(f"Narrative (20): answered {a.get('answered', 0)}, refused {a.get('refused', 0)}, "
              f"gold phrase in cited evidence {a.get('phrase_in_cited_evidence', 0)}")
        print(f"Should refuse (10): acknowledged {r.get('acknowledged', 0)}, answered anyway {r.get('answered_anyway', 0)}")
        print(f"Tricky (3): passed {t.get('passed', 0)}, failed {t.get('failed', 0)}")
        print(f"Answerable questions refused: {s['refused_answerable']} of 68 | rewrites {s['rewrites']} | "
              f"partial answers {s['partial_answers']}")
        print(f"Seconds per question: median {s['seconds_median']:.1f}, 90th percentile {s['seconds_p90']:.1f}")

    print("\n=== Wrong numeric answers (read these) ===")
    for row in details:
        if row.get("outcome") == "wrong":
            q = questions[row["id"]]
            print(f"\n{row['id']} [{row['mode']}] {q['question']}  GOLD {q['gold_display']}")
            print(f"   {shown(results[row['mode']][row['id']])}")

    print("\n=== Should-refuse and tricky answers, both systems (read these) ===")
    for qid, q in questions.items():
        if q["kind"] in ("refuse", "tricky"):
            print(f"\n{qid} ({q.get('expected', 'tricky')}) {q['question']}")
            for mode in modes:
                row = next(d for d in details if d["id"] == qid and d["mode"] == mode)
                verdict = row.get("acknowledged", row.get("passed"))
                print(f"   {mode:<8} {'OK ' if verdict else 'BAD'} {shown(results[mode][qid], 220)}")


if __name__ == "__main__":
    main()