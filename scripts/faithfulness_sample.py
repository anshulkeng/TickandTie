"""Task 5, plan B: measure faithfulness with blind hand labels, because the judge failed calibration.

    python -m scripts.faithfulness_sample build   # draw the blind sample (once)
    python -m scripts.faithfulness_sample check   # count labels and catch typos
    python -m scripts.faithfulness_sample score   # unblind and report, after labelling

Rules, fixed before the sample was drawn:
- Population: every answer sentence from both systems on the 20 narrative questions (ids n01-n20).
- Sentences are split the same way for both systems, at sentence ends; a fragment that is only
  citations is joined to the sentence before it.
- Excluded: sentences matching the gap phrases used in code scoring (for example "Not covered",
  "do not contain"). They state an absence rather than a claim.
- A sentence with no citation of its own is judged against all the evidence its answer cites.
- Sample: 25 sentences per system, numpy PCG64 seed 2026; then all 50 shuffled together and numbered,
  with the system hidden. The key is written to a separate file, opened only by the score command.
- Known leaks: Tick & Tie may cite facts as [F1], and its sentences always carry their own citation.
- Reported: share labelled supported per system, with a 95% Wilson interval."""
import json
import re
import sys
from pathlib import Path

import numpy as np

from scripts.label_set import GUIDE, parse
from tickandtie.agents.verifier import CITATION
from tickandtie.eval.scoring import DECLINE
from tickandtie.eval.stats import wilson

RESULTS = Path("eval/results")
LABELS = Path("eval/labels/faithfulness_blind.txt")
KEY = Path("eval/labels/faithfulness_blind_key.json")
OUT = Path("eval/scores/faithfulness.json")
SEED = 2026
PER_SYSTEM = 25
MODES = ("system", "baseline")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z\[])")
ONLY_CITATIONS = re.compile(r"(?:\[[^\]]*\][\s,.]*)+")


def sentences(answer):
    merged = []
    for part in (p.strip() for p in SENTENCE_END.split(answer or "")):
        if not part:
            continue
        if merged and ONLY_CITATIONS.fullmatch(part):
            merged[-1] += " " + part
        else:
            merged.append(part)
    return merged


def population(mode):
    rows = []
    for line in (RESULTS / f"{mode}.jsonl").read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if not record["id"].startswith("n") or not record.get("answer"):
            continue
        evidence = record.get("evidence") or {}
        for sentence in sentences(record["answer"]):
            if DECLINE.search(sentence):
                continue
            ids = [i.strip() for group in CITATION.findall(sentence) for i in group.split(",") if i.strip() in evidence]
            rows.append({"qid": record["id"], "question": record["question"], "mode": mode, "sentence": sentence,
                         "own_citation": bool(ids),
                         "evidence": {i: evidence[i] for i in ids} if ids else dict(evidence)})
    return rows


def build():
    if LABELS.exists() and any(b["label"] for b in parse(LABELS.read_text(encoding="utf-8"))):
        print(f"{LABELS} already has labels, so it was not overwritten.")
        return 1
    rng = np.random.default_rng(SEED)
    picked = []
    for mode in MODES:
        rows = population(mode)
        print(f"{mode}: {len(rows)} sentences in the population")
        chosen = rng.choice(len(rows), size=min(PER_SYSTEM, len(rows)), replace=False)
        picked += [rows[i] for i in sorted(chosen)]
    order = rng.permutation(len(picked))
    blocks = [GUIDE + "# A sentence marked 'no citation of its own' is judged against all the evidence shown.\n"]
    key = {}
    for number, index in enumerate(order, start=1):
        row = picked[index]
        sentence_id = f"S{number:02d}"
        key[sentence_id] = {"mode": row["mode"], "qid": row["qid"], "own_citation": row["own_citation"]}
        lines = [f"=== {sentence_id} | {row['question']}", f"SENTENCE: {row['sentence']}"]
        if not row["own_citation"]:
            lines.append("(no citation of its own: judged against all the evidence its answer cites)")
        for item_id, text in row["evidence"].items():
            lines.append(f"EVIDENCE [{item_id}]: {text}")
        lines += ["LABEL: ", "NOTE: ", ""]
        blocks.append("\n".join(lines))
    LABELS.write_text("\n".join(blocks), encoding="utf-8")
    KEY.write_text(json.dumps(key, indent=1), encoding="utf-8")
    print(f"Wrote {len(picked)} blind sentences to {LABELS}. Do not open {KEY} until scoring.")
    return 0


def check():
    blocks = parse(LABELS.read_text(encoding="utf-8"))
    done = [b for b in blocks if b["label"]]
    bad = [b for b in done if b["label"] not in ("yes", "no")]
    missing = [b["id"] for b in blocks if not b["label"]]
    print(f"{len(done)} of {len(blocks)} labelled")
    for b in bad:
        print(f"  {b['id']}: '{b['label']}' is not yes or no")
    if missing:
        print(f"  still to label: {', '.join(missing)}")
    return 1 if bad or missing else 0


def score():
    if check():
        print("Finish labelling first.")
        return 1
    labels = {b["id"]: b["label"] == "yes" for b in parse(LABELS.read_text(encoding="utf-8"))}
    key = json.loads(KEY.read_text(encoding="utf-8"))
    report = {}
    for mode in MODES:
        ids = [i for i, k in key.items() if k["mode"] == mode]
        supported = sum(labels[i] for i in ids)
        low, high = wilson(supported, len(ids))
        report[mode] = {"n": len(ids), "supported": supported, "share": supported / len(ids),
                        "ci95": [round(low, 3), round(high, 3)],
                        "without_own_citation": sum(not key[i]["own_citation"] for i in ids)}
        print(f"{mode:<8} supported {supported} of {len(ids)} = {supported / len(ids):.0%} "
              f"(95% CI {low:.0%} to {high:.0%}); sentences without their own citation: "
              f"{report[mode]['without_own_citation']}")
    OUT.write_text(json.dumps(report, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    commands = {"build": build, "check": check, "score": score}
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command in commands:
        sys.exit(commands[command]())
    print(__doc__)