"""The question-answering pipeline, wired as a LangGraph graph (decision 0016):

    route -> gather -> write -> verify -> (one rewrite) -> finalise

If the rewritten draft still fails, only its verified sentences are kept and the answer says how
many were removed; if nothing verified is left, the question is refused. Every run writes a trace."""
import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from tickandtie import config
from tickandtie.agents.evidence import Evidence
from tickandtie.agents.numbers import METRICS, fiscal_years, lookup
from tickandtie.agents.router import route
from tickandtie.agents.verifier import CITATION, NOT_COVERED, split_claims, verify
from tickandtie.agents.writer import write

TRACE_DIR = config.DATA_DIR / "traces"
PASSAGES_PER_QUESTION = 6
MIN_PASSAGES = 2
MAX_ATTEMPTS = 2
NOT_VERIFIED = ("I could not produce an answer that passes verification, so I am not showing one. "
                "The reasons are recorded in the trace.")


class LazySearcher:
    """Loads the search indexes only when a question needs filing text; loading takes several seconds."""

    def __init__(self):
        self._searcher = None

    def search(self, *args, **kwargs):
        if self._searcher is None:
            from tickandtie.index.hybrid import HybridSearcher
            self._searcher = HybridSearcher()
        return self._searcher.search(*args, **kwargs)


@dataclass
class Deps:
    con: Any
    searcher: Any = None
    decide: Any = None  # the Router's model call; None means the real model
    chat: Any = None    # the Writer's model call; None means the real model
    trace_dir: Path = TRACE_DIR


def default_deps():
    from tickandtie.agents.numbers import connect
    return Deps(con=connect(), searcher=LazySearcher())


class State(TypedDict, total=False):
    question: str
    plan: Any
    evidence: Any
    gaps: list
    notes: list
    draft: str
    problems: list
    attempts: int
    answer: str
    removed: list
    refusal: str
    trace: list


@dataclass
class Result:
    question: str
    answer: str = None
    refusal: str = None
    removed: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    sources: dict = field(default_factory=dict)
    attempts: int = 0
    seconds: float = 0.0
    evidence: Any = None
    trace_path: str = None
    periods: list = field(default_factory=list)


def as_sentence(claim):
    return claim if claim[-1] in ".!?" else claim + "."


def build_graph(deps):
    def logged(state, name, started, **details):
        entry = {"step": name, "seconds": round(time.perf_counter() - started, 2), **details}
        return state.get("trace", []) + [entry]

    def route_node(state):
        started = time.perf_counter()
        plan = route(state["question"], decide=deps.decide)
        update = {"plan": plan, "notes": list(plan.notes),
                  "trace": logged(state, "route", started, plan=vars(plan))}
        if plan.refusal:
            update["refusal"] = plan.refusal
        return update

    def gather_node(state):
        started = time.perf_counter()
        plan = state["plan"]
        evidence, gaps, notes = Evidence(), [], list(state.get("notes", []))
        for ticker in plan.tickers:
            name = config.COMPANY_NAMES[ticker]
            available = fiscal_years(deps.con, ticker)
            years = plan.fiscal_years or ([max(available)] if available else [])
            for metric in plan.metrics:
                found = []
                for year in years:
                    if year not in available:
                        gaps.append(f"{name} has no annual report for fiscal {year} in my data")
                        continue
                    fact = lookup(deps.con, ticker, metric, year)
                    if fact is None:
                        gaps.append(f"{name} does not report {METRICS[metric].label.lower()} "
                                    f"as a separate figure for fiscal {year}")
                        continue
                    evidence.add_fact(fact)
                    found.append(fact)
                if len(found) == 2:
                    older, newer = sorted(found, key=lambda fact: fact.fiscal_year)
                    evidence.add_change(older, newer)
            if plan.needs_text:
                year = max(years) if years else None
                period_end = str(available[year]) if year in available else None
                k = max(MIN_PASSAGES, PASSAGES_PER_QUESTION // len(plan.tickers))
                chunks = deps.searcher.search(plan.question, k=k, ticker=ticker,
                                              period_end=period_end, items=plan.sections)
                if len(chunks) < MIN_PASSAGES:
                    notes.append(f"{name}: too little text in {', '.join(plan.sections)}, "
                                 f"so every section was searched")
                    chunks = deps.searcher.search(plan.question, k=k, ticker=ticker, period_end=period_end)
                for chunk in chunks:
                    evidence.add_passage(chunk)
        update = {"evidence": evidence, "gaps": gaps, "notes": notes,
                  "trace": logged(state, "gather", started, evidence=list(evidence.items), gaps=gaps)}
        if not evidence.items:
            reason = (" " + "; ".join(gaps) + ".") if gaps else ""
            update["refusal"] = "I could not find reported figures or filing text that answer this question." + reason
        return update

    def write_node(state):
        started = time.perf_counter()
        attempt = state.get("attempts", 0) + 1
        if attempt == 1:
            draft = write(state["question"], state["evidence"], gaps=state["gaps"], chat=deps.chat)
        else:
            draft = write(state["question"], state["evidence"], gaps=state["gaps"],
                          problems=state["problems"], previous=state["draft"], chat=deps.chat)
        return {"draft": draft, "attempts": attempt,
                "trace": logged(state, "write", started, attempt=attempt, draft=draft)}

    def verify_node(state):
        started = time.perf_counter()
        problems = verify(state["draft"], state["evidence"])
        return {"problems": problems, "trace": logged(state, "verify", started, problems=problems)}

    def finalise_node(state):
        started = time.perf_counter()
        if not state["problems"]:
            update = {"answer": state["draft"], "removed": []}
        else:
            kept, removed = [], []
            for claim in split_claims(state["draft"]):
                claim_problems = verify(claim, state["evidence"])
                if claim_problems:
                    removed.append({"sentence": claim, "problems": claim_problems})
                else:
                    kept.append(as_sentence(claim))
            if any(not claim.startswith(NOT_COVERED) for claim in kept):
                update = {"answer": " ".join(kept), "removed": removed}
            else:
                update = {"refusal": NOT_VERIFIED, "removed": removed}
        update["trace"] = logged(state, "finalise", started, removed=len(update["removed"]))
        return update

    def after_route(state):
        return END if state.get("refusal") else "gather"

    def after_gather(state):
        return END if state.get("refusal") else "write"

    def after_verify(state):
        return "write" if state["problems"] and state["attempts"] < MAX_ATTEMPTS else "finalise"

    graph = StateGraph(State)
    graph.add_node("route", route_node)
    graph.add_node("gather", gather_node)
    graph.add_node("write", write_node)
    graph.add_node("verify", verify_node)
    graph.add_node("finalise", finalise_node)
    graph.add_edge(START, "route")
    graph.add_conditional_edges("route", after_route, {"gather": "gather", END: END})
    graph.add_conditional_edges("gather", after_gather, {"write": "write", END: END})
    graph.add_edge("write", "verify")
    graph.add_conditional_edges("verify", after_verify, {"write": "write", "finalise": "finalise"})
    graph.add_edge("finalise", END)
    return graph.compile()


def ask(question, deps=None):
    """Answer one question. Returns a Result and writes a trace file."""
    deps = deps or default_deps()
    started = time.perf_counter()
    state = build_graph(deps).invoke({"question": question, "trace": [], "notes": []})
    evidence = state.get("evidence")
    answer = state.get("answer")
    cited = []
    for group in CITATION.findall(answer or ""):
        for item_id in (part.strip() for part in group.split(",")):
            if item_id not in cited:
                cited.append(item_id)
    sources = {item_id: evidence.items[item_id].text.split("\n")[0] for item_id in cited} if evidence else {}
    result = Result(question, answer, state.get("refusal"), state.get("removed", []), state.get("notes", []),
                    sources, state.get("attempts", 0), round(time.perf_counter() - started, 1), evidence)
    for item_id in cited:
        for period in (evidence.items[item_id].period or "").split("; "):
            if period and period not in result.periods:
                result.periods.append(period)
    result.trace_path = save_trace(result, state, deps.trace_dir)
    return result


def save_trace(result, state, trace_dir):
    trace_dir = Path(trace_dir)
    trace_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(result.question.encode("utf-8")).hexdigest()[:8]
    path = trace_dir / f"{datetime.now():%Y%m%d-%H%M%S-%f}-{digest}.json"
    record = {
        "question": result.question,
        "answer": result.answer,
        "refusal": result.refusal,
        "removed": result.removed,
        "notes": result.notes,
        "periods": result.periods,
        "attempts": result.attempts,
        "seconds": result.seconds,
        "evidence": {item_id: item.text for item_id, item in result.evidence.items.items()} if result.evidence else {},
        "steps": state.get("trace", []),
    }
    path.write_text(json.dumps(record, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return str(path)