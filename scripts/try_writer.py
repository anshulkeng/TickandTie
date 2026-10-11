"""Task 4, step 3: run the Writer and Verifier on real evidence, then plant a wrong number."""
import time

from tickandtie.agents.evidence import Evidence
from tickandtie.agents.numbers import connect, lookup
from tickandtie.agents.verifier import verify
from tickandtie.agents.writer import write
from tickandtie.index.hybrid import HybridSearcher


def answer(question, evidence):
    start = time.perf_counter()
    draft = write(question, evidence)
    problems = verify(draft, evidence)
    attempts = 1
    if problems:
        print(f"   first draft failed: {problems}")
        draft = write(question, evidence, problems=problems, previous=draft)
        problems = verify(draft, evidence)
        attempts = 2
    print(f"   ({time.perf_counter() - start:.0f}s, {attempts} attempt(s))")
    print(f"   ANSWER: {draft}")
    print(f"   VERIFIER: {'PASS' if not problems else problems}")
    return draft, problems


def main():
    with connect() as con:
        apple_new, apple_old = lookup(con, "AAPL", "revenue", 2025), lookup(con, "AAPL", "revenue", 2024)
        nvda_new, nvda_old = lookup(con, "NVDA", "revenue", 2026), lookup(con, "NVDA", "revenue", 2025)

    q1 = "What was Apple's revenue in fiscal 2025, and how did it change from fiscal 2024?"
    ev1 = Evidence()
    ev1.add_fact(apple_new)
    ev1.add_fact(apple_old)
    ev1.add_change(apple_old, apple_new)
    print(f"\nQ1: {q1}")
    draft1, problems1 = answer(q1, ev1)

    q2 = "Why did NVIDIA's revenue grow so fast?"
    ev2 = Evidence()
    ev2.add_fact(nvda_new)
    ev2.add_fact(nvda_old)
    ev2.add_change(nvda_old, nvda_new)
    searcher = HybridSearcher()
    for chunk in searcher.search(q2, k=5, ticker="NVDA", period_end=str(nvda_new.period_end), items=["Item 7"]):
        ev2.add_passage(chunk)
    print(f"\nQ2: {q2}")
    answer(q2, ev2)

    print("\nPlanted error: Apple's revenue in the Q1 answer changed to a wrong figure")
    if "416,161" in draft1 and not problems1:
        caught = verify(draft1.replace("416,161", "451,161"), ev1)
        print(f"   {'CAUGHT' if caught else 'MISSED'}: {caught}")
    else:
        print("   skipped: Q1 did not produce a passing answer containing 416,161")


if __name__ == "__main__":
    main()