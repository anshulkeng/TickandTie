"""Task 6, step 1: run the risk-factor diff on real filings and show what it finds."""
import sys
import time

from tickandtie.diff.risk_diff import compare, filings, paragraphs, word_diff


def show(ticker):
    started = time.perf_counter()
    result = compare(ticker)
    seconds = time.perf_counter() - started
    if result is None:
        print(f"\n{ticker}: fewer than two filings with a real Item 1A")
        return
    counts = {p: len(paragraphs(t)) for p, _, t in filings(ticker) if p in (result.older, result.newer)}
    sentences_added = sum(len(c.added) for c in result.changes)
    sentences_removed = sum(len(c.removed) for c in result.changes)
    sentences_edited = sum(len(c.edits) for c in result.changes)
    print(f"\n=== {ticker}: {result.older} ({counts[result.older]} paragraphs) -> "
          f"{result.newer} ({counts[result.newer]} paragraphs), {seconds:.1f}s ===")
    print(f"paragraphs: unchanged {result.unchanged}, reorganised {result.reorganised}, changed "
          f"{result.count('changed')}, new {result.count('new')}, removed {result.count('removed')}")
    print(f"sentences: added {sentences_added}, removed {sentences_removed}, edited {sentences_edited}")
    for kind in ("new", "removed"):
        for change in [c for c in result.changes if c.kind == kind][:3]:
            sentence = (change.added or change.removed)[0]
            print(f"  {kind.upper():<8} [{change.heading[:35]}] {sentence[:150]}")
    for change in [c for c in result.changes if c.kind == "changed"][:3]:
        print(f"  CHANGED  [{change.heading[:35]}]")
        for old, new in change.edits[:1]:
            print(f"     ~ {word_diff(old, new)[:260]}")
        for sentence in change.added[:1]:
            print(f"     + {sentence[:150]}")
        for sentence in change.removed[:1]:
            print(f"     - {sentence[:150]}")


if __name__ == "__main__":
    for ticker in sys.argv[1:] or ["AAPL", "PFE"]:
        show(ticker)