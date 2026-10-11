"""Build and check the hand-labelled faithfulness set used to calibrate the judge (Task 5).

    python -m scripts.label_set build     # collect answer sentences and their cited evidence
    python -m scripts.label_set rebuild   # collect again, keeping every label already given
    python -m scripts.label_set check     # count labels and catch typos

Sentences come from final answers in data/traces. Those questions are calibration material only
and must not appear in the evaluation set."""
import json
import re
import sys
from pathlib import Path

from tickandtie.agents.pipeline import TRACE_DIR
from tickandtie.agents.verifier import CITATION, NOT_COVERED, split_claims

LABELS_PATH = Path("eval/labels/faithfulness.txt")
VALID = {"yes", "no"}
BLOCK = re.compile(r"^=== (S\d+) ", re.MULTILINE)
GUIDE = """# Hand labels for judge calibration. For each block, set LABEL to yes or no.
#
# yes: everything the sentence says is stated in, or directly follows from, the cited evidence,
#      including what each number measures (segment, period, unit).
# no:  anything is missing from the evidence, overstated, relabelled (for example "Data Center"
#      when the evidence says "Data Center computing"), or comes from outside knowledge.
# Partly right counts as no. Label from the evidence shown, not from what you know about the company.
# NOTE is optional: a few words on why, useful when the judge disagrees with you later.
# Only edit the LABEL and NOTE lines.
"""


def sentences_from_traces():
    seen, rows = set(), []
    for path in sorted(TRACE_DIR.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if not record.get("answer"):
            continue
        for claim in split_claims(record["answer"]):
            if claim.startswith(NOT_COVERED) or claim in seen:
                continue
            cited = [item.strip() for group in CITATION.findall(claim) for item in group.split(",")]
            if not cited or any(item not in record["evidence"] for item in cited):
                continue
            seen.add(claim)
            rows.append({"question": record["question"], "sentence": claim,
                         "evidence": {item: record["evidence"][item] for item in cited}})
    return rows


def field(block, name):
    found = re.search(rf"^{name}: ?(.*)$", block, re.M)
    return found.group(1).strip() if found else ""


def parse(text):
    """Every block in the label file as a dict of id, sentence, label and note."""
    starts = [match.start() for match in BLOCK.finditer(text)] + [len(text)]
    blocks = []
    for begin, end in zip(starts, starts[1:]):
        block = text[begin:end]
        blocks.append({"id": BLOCK.match(block).group(1), "sentence": field(block, "SENTENCE"),
                       "label": field(block, "LABEL").lower(), "note": field(block, "NOTE")})
    return blocks


def write(rows, keep):
    blocks = [GUIDE]
    for number, row in enumerate(rows, start=1):
        label, note = keep.get(row["sentence"], ("", ""))
        lines = [f"=== S{number:02d} | {row['question']}", f"SENTENCE: {row['sentence']}"]
        for item_id, text in row["evidence"].items():
            lines.append(f"EVIDENCE [{item_id}]: {text}")
        lines += [f"LABEL: {label}", f"NOTE: {note}", ""]
        blocks.append("\n".join(lines))
    LABELS_PATH.parent.mkdir(parents=True, exist_ok=True)
    LABELS_PATH.write_text("\n".join(blocks), encoding="utf-8")


def build():
    if LABELS_PATH.exists() and any(b["label"] for b in parse(LABELS_PATH.read_text(encoding="utf-8"))):
        print(f"{LABELS_PATH} already has labels, so it was not overwritten. Use rebuild to keep them.")
        return 1
    rows = sentences_from_traces()
    write(rows, {})
    print(f"Wrote {len(rows)} sentences to {LABELS_PATH}")
    return 0


def rebuild():
    old = parse(LABELS_PATH.read_text(encoding="utf-8")) if LABELS_PATH.exists() else []
    keep = {b["sentence"]: (b["label"], b["note"]) for b in old if b["label"]}
    rows = sentences_from_traces()
    write(rows, keep)
    kept = sum(row["sentence"] in keep for row in rows)
    print(f"Wrote {len(rows)} sentences to {LABELS_PATH}: {kept} labels kept, {len(rows) - kept} to label")
    return 0


def check():
    blocks = parse(LABELS_PATH.read_text(encoding="utf-8"))
    done = [b for b in blocks if b["label"]]
    bad = [b for b in done if b["label"] not in VALID]
    yes = sum(b["label"] == "yes" for b in done)
    print(f"{len(done)} of {len(blocks)} labelled: {yes} yes, {len(done) - yes - len(bad)} no")
    for b in bad:
        print(f"  {b['id']}: '{b['label']}' is not yes or no")
    missing = [b["id"] for b in blocks if not b["label"]]
    if missing:
        print(f"  still to label: {', '.join(missing)}")
    return 1 if bad or missing else 0


if __name__ == "__main__":
    commands = {"build": build, "rebuild": rebuild, "check": check}
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command in commands:
        sys.exit(commands[command]())
    print(__doc__)