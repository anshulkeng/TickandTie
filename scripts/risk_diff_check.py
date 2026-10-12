"""Task 6, step 2: check that reported risk-factor changes are real, on companies not read while building.

    python -m scripts.risk_diff_check build   # draw the sample (once)
    python -m scripts.risk_diff_check check   # count labels and catch typos
    python -m scripts.risk_diff_check score   # report against the pass mark

Rules, fixed before the sample was drawn:
- Population: every reported item (an added, removed or edited sentence) for MSFT, WMT, JPM, KO and CAT,
  latest filing against the one before. Apple and Pfizer are excluded: their output was read while building.
- Sample: 10 items, numpy PCG64 seed 2026.
- Label yes: a real difference in content between the two filings (even one word).
  Label no: noise, meaning the text is really in both filings, or it is a fragment or a split sentence.
- Pass mark: at least 8 of 10 labelled yes. On a fail, the cause is fixed and a fresh sample is drawn."""
import json
import sys
from pathlib import Path

import numpy as np

from scripts.label_set import parse
from tickandtie.diff.risk_diff import compare, filings, paragraphs, ratio, sentences, word_diff

TICKERS = ["MSFT", "WMT", "JPM", "KO", "CAT"]
LABELS = Path("eval/labels/risk_diff_check.txt")
OUT = Path("eval/scores/risk_diff_check.json")
SEED = 2026
SAMPLE = 10
PASS_MARK = 8
GUIDE = """# Risk-factor diff check. For each block, set LABEL to yes or no.
#
# yes: a real difference in content between the two filings, even a single word.
# no:  noise. The text is really in both filings, or it is a fragment, or a sentence was split differently.
# The CLOSEST line shows the most similar sentence in the other filing, to help you decide.
# Only edit the LABEL and NOTE lines.
"""


def all_sentences(text):
    return [s for p in paragraphs(text) for s in sentences(p.text)]


def closest(sentence, pool):
    best = max(pool, key=lambda s: ratio(s, sentence), default="")
    return ratio(best, sentence) if best else 0.0, best


def items():
    found = []
    for ticker in TICKERS:
        result = compare(ticker)
        if result is None:
            continue
        texts = {period: text for period, _, text in filings(ticker)}
        older, newer = all_sentences(texts[result.older]), all_sentences(texts[result.newer])
        span = f"{ticker} {result.older} -> {result.newer}"
        for change in result.changes:
            for sentence in change.added:
                found.append((span, "added", sentence, "OLDER", *closest(sentence, older)))
            for sentence in change.removed:
                found.append((span, "removed", sentence, "NEWER", *closest(sentence, newer)))
            for old, new in change.edits:
                found.append((span, "edited", word_diff(old, new), "", 0.0, ""))
    return found


def build():
    if LABELS.exists() and any(b["label"] for b in parse(LABELS.read_text(encoding="utf-8"))):
        print(f"{LABELS} already has labels, so it was not overwritten.")
        return 1
    population = items()
    print(f"{len(population)} reported items across {', '.join(TICKERS)}")
    chosen = np.random.default_rng(SEED).choice(len(population), size=SAMPLE, replace=False)
    blocks = [GUIDE]
    for number, index in enumerate(chosen, start=1):
        span, kind, text, side, score, nearest = population[index]
        lines = [f"=== S{number:02d} | {span} | {kind}", f"SENTENCE: {text}"]
        if side:
            lines.append(f"CLOSEST IN {side} FILING (similarity {score:.2f}): {nearest}")
        lines += ["LABEL: ", "NOTE: ", ""]
        blocks.append("\n".join(lines))
    LABELS.write_text("\n".join(blocks), encoding="utf-8")
    print(f"Wrote {SAMPLE} items to {LABELS}")
    return 0


def check():
    blocks = parse(LABELS.read_text(encoding="utf-8"))
    bad = [b for b in blocks if b["label"] and b["label"] not in ("yes", "no")]
    missing = [b["id"] for b in blocks if not b["label"]]
    print(f"{len(blocks) - len(missing)} of {len(blocks)} labelled")
    for b in bad:
        print(f"  {b['id']}: '{b['label']}' is not yes or no")
    if missing:
        print(f"  still to label: {', '.join(missing)}")
    return 1 if bad or missing else 0


def score():
    if check():
        return 1
    blocks = parse(LABELS.read_text(encoding="utf-8"))
    real = sum(b["label"] == "yes" for b in blocks)
    passed = real >= PASS_MARK
    OUT.write_text(json.dumps({"real": real, "n": len(blocks), "pass_mark": PASS_MARK, "passed": passed},
                              indent=1), encoding="utf-8")
    print(f"Real changes: {real} of {len(blocks)}. Pass mark {PASS_MARK}: {'PASS' if passed else 'FAIL'}")
    return 0


if __name__ == "__main__":
    commands = {"build": build, "check": check, "score": score}
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command in commands:
        sys.exit(commands[command]())
    print(__doc__)