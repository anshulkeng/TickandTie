"""Ask Tick & Tie a question from the terminal.

Usage: python -m scripts.ask "What was Apple's revenue in fiscal 2025?"
"""
import sys

from tickandtie.agents.pipeline import ask


def show(result):
    print()
    print(result.answer if result.answer else f"No answer: {result.refusal}")
    if result.removed:
        count = len(result.removed)
        print(f"\nNote: {count} sentence(s) removed because a figure could not be matched to its cited evidence.")
    if result.sources:
        print("\nSources:")
        for item_id, source in result.sources.items():
            print(f"  [{item_id}] {source}")
    if result.periods:
        print("\nPeriods:")
        for period in result.periods:
            print(f"  {period}")
    for note in result.notes:
        print(f"\n(note: {note})")
    print(f"\n{result.attempts} draft(s), {result.seconds}s. Trace: {result.trace_path}")


def main():
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        print(__doc__)
        return 1
    show(ask(question))
    return 0


if __name__ == "__main__":
    sys.exit(main())