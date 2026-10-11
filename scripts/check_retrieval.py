"""Task 3, step 3: measure meaning, word and hybrid search on the hand-checked questions.

Each question is asked twice: as written (using the documents' own terms) and as a
paraphrase without those terms, so word search does not get an unfair advantage.
"""
import json
from pathlib import Path

from tickandtie.index.hybrid import HybridSearcher, reciprocal_rank_fusion

QUESTIONS_PATH = Path("eval/retrieval_questions.json")
TOP = 5
DEPTH = 10
METHODS = ("meaning", "words", "hybrid")
SETS = (("question", "As written"), ("paraphrase", "Paraphrased"))


def is_relevant(chunk, question):
    """Right company, an allowed Item, and the text contains one of the key phrases."""
    text = chunk["text"].lower()
    return (chunk["ticker"] == question["ticker"]
            and chunk["item"] in question["items"]
            and any(phrase.lower() in text for phrase in question["phrases"]))


def first_hit_rank(ids, by_id, question):
    for rank, chunk_id in enumerate(ids[:DEPTH], start=1):
        if is_relevant(by_id[chunk_id], question):
            return rank
    return None


def evaluate(searcher, questions, field):
    totals = {method: {"hits": 0, "rr": 0.0} for method in METHODS}
    rows = []
    for question in questions:
        ranked = searcher.rankings(question[field], ticker=question["ticker"])
        ranked["hybrid"] = reciprocal_rank_fusion([ranked["meaning"], ranked["words"]])
        ranks = {method: first_hit_rank(ranked[method], searcher.by_id, question) for method in METHODS}
        for method, rank in ranks.items():
            if rank is not None:
                totals[method]["rr"] += 1.0 / rank
                if rank <= TOP:
                    totals[method]["hits"] += 1
        rows.append((question, ranks, ranked["hybrid"][0] if ranked["hybrid"] else None))
    return totals, rows


def print_summary(totals, count):
    for method in METHODS:
        print(f"  {method:<8} recall@{TOP}: {totals[method]['hits']}/{count}"
              f"   MRR@{DEPTH}: {totals[method]['rr'] / count:.2f}")


def main():
    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    searcher = HybridSearcher()
    available = {q["id"]: sum(is_relevant(c, q) for c in searcher.chunks) for q in questions}
    combined = {method: {"hits": 0, "rr": 0.0} for method in METHODS}

    for field, title in SETS:
        totals, rows = evaluate(searcher, questions, field)
        print(f"\n=== {title} ===")
        print(f"{'id':<4} {'ticker':<6} {'answers':>7}  " + "  ".join(f"{m:>7}" for m in METHODS))
        for question, ranks, _ in rows:
            cells = "  ".join(f"{(ranks[m] or '-'):>7}" for m in METHODS)
            flag = "  NO ANSWER IN DATA" if available[question["id"]] == 0 else ""
            print(f"{question['id']:<4} {question['ticker']:<6} {available[question['id']]:>7}  {cells}{flag}")
        print_summary(totals, len(questions))
        for method in METHODS:
            combined[method]["hits"] += totals[method]["hits"]
            combined[method]["rr"] += totals[method]["rr"]
        misses = [(q, top) for q, ranks, top in rows if ranks["hybrid"] != 1]
        if misses:
            print("  Hybrid's top result where it was not a correct chunk:")
            for question, top_id in misses:
                snippet = searcher.by_id[top_id]["text"][:90] if top_id else "(nothing found)"
                print(f"    {question['id']} {top_id}\n        {snippet!r}")

    count = 2 * len(questions)
    print(f"\n=== Both sets ({count} questions) ===")
    print_summary(combined, count)

    # Decision rule, fixed before the results were seen: highest recall@5, then highest MRR,
    # then hybrid wins a full tie because it is the safer choice for paraphrased questions.
    preference = {"hybrid": 2, "words": 1, "meaning": 0}
    winner = max(METHODS, key=lambda m: (combined[m]["hits"], round(combined[m]["rr"], 6), preference[m]))
    print(f"\nDecision rule picks: {winner}")


if __name__ == "__main__":
    main()