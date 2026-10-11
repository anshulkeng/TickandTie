"""Task 4, step 4: run the full pipeline on ten questions, then plant a wrong number.

Expected outcomes: "answer", "refusal", or "gap" (a refusal, or an answer with a Not covered sentence)."""
from tickandtie.agents.numbers import connect
from tickandtie.agents.pipeline import Deps, LazySearcher, ask
from tickandtie.agents.verifier import NOT_COVERED, verify
from tickandtie.agents.writer import ollama_chat

QUESTIONS = [
    ("What was Apple's revenue in fiscal 2025?", "answer"),
    ("How did Walmart's net income change from FY2025 to FY2026?", "answer"),
    ("Compare Microsoft and NVIDIA research and development spending in fiscal 2025", "answer"),
    ("What are the main risks Pfizer describes?", "answer"),
    ("Why did NVIDIA's revenue grow so fast?", "answer"),
    ("How does JPMorgan manage interest rate risk?", "answer"),
    ("What was J&J's diluted EPS in 2023?", "answer"),
    ("What was Walmart's research and development expense in fiscal 2026?", "gap"),
    ("Tell me about Tesla's revenue", "refusal"),
    ("What does Exxon say about climate change?", "answer"),
]


def outcome_ok(result, expected):
    if expected == "answer":
        return result.answer is not None
    if expected == "refusal":
        return result.answer is None
    return result.answer is None or NOT_COVERED in result.answer


def main():
    con = connect()
    searcher = LazySearcher()
    passed = 0
    for question, expected in QUESTIONS:
        result = ask(question, Deps(con=con, searcher=searcher))
        recheck = verify(result.answer, result.evidence) if result.answer else []
        ok = outcome_ok(result, expected) and not recheck
        passed += ok
        print(f"\n[{'OK' if ok else 'UNEXPECTED'}] {question}")
        print(f"   expected {expected}; {'answer' if result.answer else 'refusal'}, {result.attempts} draft(s), "
              f"{len(result.removed)} removed, {result.seconds}s")
        print(f"   {(result.answer or result.refusal)[:400]}")
        if result.periods:
            print(f"   periods: {result.periods}")
        for note in result.notes:
            print(f"   note: {note}")
        if recheck:
            print(f"   RECHECK FAILED: {recheck}")

    def corrupting_chat(messages):
        return ollama_chat(messages).replace("416,161", "451,161")

    planted = ask("What was Apple's revenue in fiscal 2025?", Deps(con=con, searcher=searcher, chat=corrupting_chat))
    caught = "451,161" not in (planted.answer or "")
    passed += caught
    print(f"\n[{'OK' if caught else 'FAILED'}] Planted wrong number: {'never shown' if caught else 'SHOWN TO THE USER'}")
    print(f"   {(planted.answer or planted.refusal)[:300]}")
    print(f"\n{passed}/{len(QUESTIONS) + 1} checks passed")


if __name__ == "__main__":
    main()