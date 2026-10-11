"""Show the plan, evidence, drafts and Verifier results from the latest trace matching some words.

Usage: python -m scripts.show_trace walmart net income
"""
import json
import sys

from tickandtie.agents.pipeline import TRACE_DIR


def main():
    words = " ".join(sys.argv[1:]).lower()
    for path in sorted(TRACE_DIR.glob("*.json"), reverse=True):
        record = json.loads(path.read_text(encoding="utf-8"))
        if all(word in record["question"].lower() for word in words.split()):
            break
    else:
        print("No trace matches those words.")
        return
    print(f"{path.name}\nQ: {record['question']}")
    for step in record["steps"]:
        if step["step"] == "route":
            plan = step["plan"]
            print(f"\nPlan: companies={plan['tickers']} years={plan['fiscal_years']} metrics={plan['metrics']} "
                  f"text={plan['needs_text']} sections={plan['sections']}")
    print("\nEvidence:")
    for item_id, text in record["evidence"].items():
        print(f"  [{item_id}] {text.splitlines()[0][:170]}")
    for step in record["steps"]:
        if step["step"] == "write":
            print(f"\nDraft {step['attempt']} ({step['seconds']}s):\n  {step['draft']}")
        if step["step"] == "verify":
            print(f"Verifier: {step['problems'] or 'PASS'}")
    print(f"\nRemoved: {[item['problems'] for item in record['removed']]}")


if __name__ == "__main__":
    main()