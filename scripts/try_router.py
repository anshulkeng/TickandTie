"""Task 4, step 2: run the Router with the real model on varied questions and show its plans."""
import time

from tickandtie.agents.router import route

QUESTIONS = [
    "What was Apple's revenue in fiscal 2024?",
    "How did Walmart's net income change from FY2025 to FY2026?",
    "Compare Microsoft and NVIDIA research and development spending in 2025",
    "What are the main risks Pfizer describes?",
    "Why did NVIDIA's revenue grow so fast?",
    "What is Coca-Cola's long-term debt?",
    "How does JPMorgan manage interest rate risk?",
    "What was J&J's diluted EPS in 2023?",
    "Tell me about Tesla's revenue",
    "What does Exxon say about climate change?",
    "What were Caterpillar's capital expenditures last year?",
    "How much cash did Costco have at the end of FY24?",
]


def main():
    for question in QUESTIONS:
        start = time.perf_counter()
        plan = route(question)
        seconds = time.perf_counter() - start
        print(f"\nQ: {question}  ({seconds:.1f}s)")
        if plan.refusal:
            print(f"   REFUSED: {plan.refusal}")
            continue
        print(f"   companies={plan.tickers} years={plan.fiscal_years or 'latest'} metrics={plan.metrics}")
        print(f"   numbers={plan.needs_numbers} text={plan.needs_text} sections={plan.sections}")
        for note in plan.notes:
            print(f"   NOTE: {note}")


if __name__ == "__main__":
    main()