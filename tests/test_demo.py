"""Tests for demo mode: the switch, saved answers, questions that need no model, and the endpoints."""
import json

from fastapi.testclient import TestClient

from tickandtie.agents.pipeline import Deps, Result
from tickandtie.api.app import answer_with_pipeline, create_app
from tickandtie.api.demo import DemoMode
from tickandtie.api.jobs import JobStore
from tickandtie.llm import ModelUnavailable

SAVED_QUESTION = "What was Apple's revenue in fiscal 2025?"


def saved_file(tmp_path):
    path = tmp_path / "saved.jsonl"
    record = {"id": "q", "question": SAVED_QUESTION, "answer": "Apple's revenue in fiscal 2025 was $416,161 million [F1].",
              "refusal": None, "evidence": {"F1": "Apple revenue, fiscal 2025: $416,161 million."},
              "periods": ["Apple fiscal 2025: 2024-09-29 to 2025-09-27"], "notes": [], "removed": 0}
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    return path


class Clock:
    def __init__(self):
        self.now = 1_000.0

    def __call__(self):
        return self.now


def unavailable(messages):
    raise ModelUnavailable("hosted model returned HTTP 402")


def fake_ask(question, deps):
    """Like the pipeline: the risk-factor diff needs no model; everything else calls the Writer's model."""
    if "risk factors" in question:
        return Result(question, answer="Code-built diff answer.")
    return Result(question, answer=deps.chat([]))


def test_live_answers_are_labelled_live(tmp_path):
    demo = DemoMode(minutes=10, saved_path=saved_file(tmp_path), clock=Clock())
    answer = answer_with_pipeline(demo, ask_fn=fake_ask,
                                  make_deps=lambda: Deps(con=None, chat=lambda m: "Live answer [F1]."))
    result = answer("Some question?")
    assert result["mode"] == "live" and result["answer"] == "Live answer [F1]." and not demo.active()


def test_an_unavailable_model_switches_to_demo_with_saved_answers(tmp_path):
    demo = DemoMode(minutes=10, saved_path=saved_file(tmp_path), clock=Clock())
    answer = answer_with_pipeline(demo, ask_fn=fake_ask, make_deps=lambda: Deps(con=None, chat=unavailable))
    result = answer(SAVED_QUESTION)
    assert demo.active() and result["mode"] == "demo" and result["saved"] is True
    assert "$416,161 million" in result["answer"] and "saved answer" in result["notes"][-1]
    other = answer("A question with no saved answer?")
    assert other["answer"] is None and "paused" in other["refusal"] and SAVED_QUESTION in other["suggestions"]
    assert "402" not in json.dumps(result) + json.dumps(other)


def test_questions_that_need_no_model_still_work_in_demo_mode(tmp_path):
    demo = DemoMode(minutes=10, saved_path=saved_file(tmp_path), clock=Clock())
    demo.trip("test")
    answer = answer_with_pipeline(demo, ask_fn=fake_ask, make_deps=lambda: Deps(con=None, chat=lambda m: "unused"))
    result = answer("What changed in Pfizer's risk factors?")
    assert result["answer"] == "Code-built diff answer." and result["mode"] == "demo"


def test_live_answers_are_tried_again_after_the_pause(tmp_path):
    clock = Clock()
    demo = DemoMode(minutes=10, saved_path=saved_file(tmp_path), clock=clock)
    demo.trip("test")
    assert demo.active()
    clock.now += 601
    assert not demo.active()


def test_status_and_saved_questions_endpoints(tmp_path, monkeypatch):
    monkeypatch.delenv("TICKANDTIE_FORCE_DEMO", raising=False)
    demo = DemoMode(minutes=10, saved_path=saved_file(tmp_path), clock=Clock())
    app = create_app(JobStore(tmp_path / "jobs.sqlite"), answer=lambda q: {}, start_worker=False, demo=demo)
    client = TestClient(app)
    assert client.get("/api/status").json() == {"mode": "live"}
    assert client.get("/api/demo").json() == {"questions": [SAVED_QUESTION]}
    monkeypatch.setenv("TICKANDTIE_FORCE_DEMO", "1")
    assert client.get("/api/status").json()["mode"] == "demo"