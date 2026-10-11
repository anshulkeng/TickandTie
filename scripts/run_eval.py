"""Task 5, step 2: run the evaluation questions through Tick & Tie or the plain-RAG baseline.

    python -m scripts.run_eval system            # Tick & Tie on every question
    python -m scripts.run_eval baseline          # plain RAG on the same questions
    python -m scripts.run_eval system --limit 3  # a quick smoke run

Results are appended to eval/results/<mode>.jsonl one question at a time, so a run can be stopped
with Ctrl+C and resumed: questions already in the file are skipped. Nothing is scored here.

The baseline uses the same hybrid search filtered to the named companies, the top 6 passages and
one model call that must cite them. It has no facts table, no Verifier, no rewrite and no
refusal rules."""
import argparse
import json
import subprocess
import time
from pathlib import Path

from tickandtie import config
from tickandtie.agents.evidence import Evidence
from tickandtie.agents.numbers import connect
from tickandtie.agents.pipeline import Deps, LazySearcher, ask
from tickandtie.agents.router import find_companies
from tickandtie.agents.verifier import CITATION
from tickandtie.agents.writer import CONTEXT_TOKENS

QUESTIONS = Path("eval/questions.jsonl")
RESULTS = Path("eval/results")
EVAL_TRACES = config.DATA_DIR / "traces_eval"  # kept apart from data/traces, which feeds the label set
BASELINE_PASSAGES = 6
BASELINE_PROMPT = """You answer questions about US companies' annual reports (Form 10-K) using the passages provided.
Use only the passages. Cite the passages you use with their ids, for example [P1] or [P2, P3].
If the passages do not contain the answer, say so. Answer in 2 to 6 plain sentences."""


def cited_evidence(answer, items):
    """The text of every evidence item the answer cites, in the order first cited."""
    ids = []
    for group in CITATION.findall(answer or ""):
        for item_id in (part.strip() for part in group.split(",")):
            if item_id in items and item_id not in ids:
                ids.append(item_id)
    return {item_id: items[item_id] for item_id in ids}


def run_system(question, deps):
    result = ask(question, deps)
    items = {item_id: item.text for item_id, item in result.evidence.items.items()} if result.evidence else {}
    return {"answer": result.answer, "refusal": result.refusal, "removed": len(result.removed),
            "attempts": result.attempts, "notes": result.notes, "periods": result.periods,
            "seconds": result.seconds, "evidence": cited_evidence(result.answer, items),
            "trace": result.trace_path}


def run_baseline(question, searcher):
    import ollama
    started = time.perf_counter()
    evidence = Evidence()
    tickers = find_companies(question)
    if tickers:
        k = max(2, BASELINE_PASSAGES // len(tickers))
        chunks = [chunk for ticker in tickers for chunk in searcher.search(question, k=k, ticker=ticker)]
    else:
        chunks = searcher.search(question, k=BASELINE_PASSAGES)
    for chunk in chunks:
        evidence.add_passage(chunk)
    user = f"Question: {question}\n\n<passages>\n{evidence.render()}\n</passages>"
    response = ollama.chat(model=config.LLM_MODEL,
                           messages=[{"role": "system", "content": BASELINE_PROMPT}, {"role": "user", "content": user}],
                           options={"temperature": 0, "seed": 7, "num_ctx": CONTEXT_TOKENS})
    answer = response["message"]["content"].strip()
    items = {item_id: item.text for item_id, item in evidence.items.items()}
    return {"answer": answer, "refusal": None, "removed": 0, "attempts": 1, "notes": [], "periods": [],
            "seconds": round(time.perf_counter() - started, 1), "evidence": cited_evidence(answer, items),
            "trace": None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["system", "baseline"])
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    questions = [json.loads(line) for line in QUESTIONS.read_text(encoding="utf-8").splitlines() if line.strip()]
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / f"{args.mode}.jsonl"
    done = set()
    if out.exists():
        done = {json.loads(line)["id"] for line in out.read_text(encoding="utf-8").splitlines() if line.strip()}
    todo = [q for q in questions if q["id"] not in done]
    if args.limit:
        todo = todo[:args.limit]
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    print(f"{args.mode} at commit {commit}: {len(done)} already done, running {len(todo)}")

    con = connect()
    searcher = LazySearcher()
    deps = Deps(con=con, searcher=searcher, trace_dir=EVAL_TRACES)
    started = time.perf_counter()
    with out.open("a", encoding="utf-8") as handle:
        for number, question in enumerate(todo, start=1):
            try:
                if args.mode == "system":
                    record = run_system(question["question"], deps)
                else:
                    record = run_baseline(question["question"], searcher)
            except Exception as exc:  # recorded, never hidden; delete the line to retry it
                record = {"error": repr(exc)}
            record = {"id": question["id"], "mode": args.mode, "commit": commit,
                      "question": question["question"], **record}
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            handle.flush()
            status = "ERROR" if "error" in record else ("answer" if record.get("answer") else "refusal")
            minutes = (time.perf_counter() - started) / 60
            print(f"[{number}/{len(todo)}] {question['id']} {status:<7} {record.get('seconds', '-')}s "
                  f"(elapsed {minutes:.1f} min)")
    con.close()


if __name__ == "__main__":
    main()