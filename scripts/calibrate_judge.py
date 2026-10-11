"""Task 5, step 3b: measure the judge against the hand labels before trusting it.

    python -m scripts.calibrate_judge

Pass mark, fixed before the first run: agreement of at least 80% with the hand labels, and at
least 6 of the 8 sentences labelled "no" caught. An unreadable verdict counts as a miss. The judge
prompt is not tuned on these labels. If the judge fails, that is reported, and faithfulness is
measured instead by hand-labelling a random sample of answer sentences (plan B)."""
import json
from pathlib import Path

from scripts.label_set import LABELS_PATH, parse, sentences_from_traces
from tickandtie.eval.judge import agreement, judge

OUT = Path("eval/scores/judge_calibration.jsonl")
MIN_AGREEMENT = 0.80
MIN_CAUGHT_NO = 6


def main():
    labels = {block["sentence"]: block for block in parse(LABELS_PATH.read_text(encoding="utf-8"))}
    rows = [row for row in sentences_from_traces() if row["sentence"] in labels]
    assert len(rows) == len(labels) == 25, f"expected the 25 labelled sentences, found {len(rows)} of {len(labels)}"

    records, pairs = [], []
    for number, row in enumerate(rows, start=1):
        block = labels[row["sentence"]]
        human = block["label"] == "yes"
        supported, reason = judge(row["sentence"], row["evidence"])
        pairs.append((human, supported))
        records.append({"id": block["id"], "human": human, "judge": supported, "reason": reason,
                        "sentence": row["sentence"], "human_note": block["note"]})
        mark = "agree" if supported == human else "DISAGREE"
        print(f"[{number}/25] {block['id']} you={'yes' if human else 'no '} judge={supported} {mark}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    result = agreement(pairs)
    passed = result["agreement"] >= MIN_AGREEMENT and result["caught_no"] >= MIN_CAUGHT_NO

    print("\nDisagreements:")
    for r in records:
        if r["judge"] != r["human"]:
            print(f"\n{r['id']} you={'yes' if r['human'] else 'no'} judge={r['judge']}")
            print(f"   sentence: {r['sentence'][:200]}")
            print(f"   judge's reason: {r['reason']}")
            if r["human_note"]:
                print(f"   your note: {r['human_note']}")
    print(f"\nAgreement {result['agreement']:.0%} ({round(result['agreement'] * result['n'])} of {result['n']}), "
          f"kappa {result['kappa']:.2f}")
    print(f"Unsupported sentences caught: {result['caught_no']} of {result['human_no']} | "
          f"false alarms: {result['false_alarms']}")
    print(f"\nPass mark (80% and at least {MIN_CAUGHT_NO} caught): {'PASS' if passed else 'FAIL'}")


if __name__ == "__main__":
    main()