"""Tests for the job list, the worker and the API, with a fake answer function (no model needed)."""
import pytest
from fastapi.testclient import TestClient

from tickandtie.api.app import create_app
from tickandtie.api.jobs import JobStore
from tickandtie.api.limits import Limits, RateLimited, check


def client_with(tmp_path, answer, limits=None):
    app = create_app(JobStore(tmp_path / "jobs.sqlite"), answer=answer, start_worker=False, limits=limits)
    return app, TestClient(app)


def test_a_question_is_queued_then_answered(tmp_path):
    app, client = client_with(tmp_path, lambda q: {"answer": f"Answer to {q}", "refusal": None})
    reply = client.post("/api/questions", json={"question": "What was Apple's revenue?"})
    assert reply.status_code == 202
    job = reply.json()
    assert job["status"] == "queued" and job["position"] == 1
    assert client.get(f"/api/questions/{job['id']}").json()["status"] == "queued"
    assert app.state.worker.run_once()
    done = client.get(f"/api/questions/{job['id']}").json()
    assert done["status"] == "done" and done["result"]["answer"] == "Answer to What was Apple's revenue?"


def test_questions_are_answered_in_order_with_queue_positions(tmp_path):
    seen = []
    app, client = client_with(tmp_path, lambda q: seen.append(q) or {"answer": q})
    client.post("/api/questions", json={"question": "First question?"})
    second = client.post("/api/questions", json={"question": "Second question?"}).json()
    assert second["position"] == 2
    app.state.worker.run_once()
    assert client.get(f"/api/questions/{second['id']}").json()["position"] == 1
    app.state.worker.run_once()
    assert seen == ["First question?", "Second question?"]


def test_a_failure_is_reported_without_internal_details(tmp_path):
    def broken(question):
        raise RuntimeError("database password is hunter2")

    app, client = client_with(tmp_path, broken)
    job = client.post("/api/questions", json={"question": "Will this fail?"}).json()
    app.state.worker.run_once()
    reply = client.get(f"/api/questions/{job['id']}").json()
    assert reply["status"] == "failed" and "try again" in reply["error"] and "hunter2" not in str(reply)


def test_unknown_ids_invalid_questions_and_health(tmp_path):
    app, client = client_with(tmp_path, lambda q: {})
    assert client.get("/api/questions/nope").status_code == 404
    assert client.post("/api/questions", json={"question": "hi"}).status_code == 422
    assert client.post("/api/questions", json={"question": "x" * 301}).status_code == 422
    assert client.get("/api/health/live").json() == {"status": "ok"}


def test_running_jobs_go_back_in_the_queue_after_a_restart(tmp_path):
    store = JobStore(tmp_path / "jobs.sqlite")
    job_id = store.submit("Question?", "client")
    store.claim()
    assert store.get(job_id)["status"] == "running"
    restarted = JobStore(tmp_path / "jobs.sqlite")
    assert restarted.get(job_id)["status"] == "queued"


def test_old_jobs_are_deleted(tmp_path):
    store = JobStore(tmp_path / "jobs.sqlite")
    job_id = store.submit("Question?", "client")
    assert store.purge(max_age_seconds=-1) == 1 and store.get(job_id) is None

def test_errors_use_one_standard_format(tmp_path):
    app, client = client_with(tmp_path, lambda q: {})
    assert client.get("/api/questions/nope").json() == {
        "error": {"code": "not_found", "message": "No question with that id."}}
    bad = client.post("/api/questions", json={"question": "hi"})
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "invalid_question"


def test_control_characters_and_extra_spaces_are_cleaned(tmp_path):
    app, client = client_with(tmp_path, lambda q: {"answer": q})
    job = client.post("/api/questions", json={"question": "What  was\x00 Apple's\n revenue?"}).json()
    assert client.get(f"/api/questions/{job['id']}").json()["question"] == "What was Apple's revenue?"


def test_a_visitor_is_limited_per_minute_with_a_retry_time(tmp_path):
    app, client = client_with(tmp_path, lambda q: {}, limits=Limits(per_minute=2, per_day=10, site_per_day=100))
    for _ in range(2):
        assert client.post("/api/questions", json={"question": "Question?"}).status_code == 202
    blocked = client.post("/api/questions", json={"question": "Question?"})
    assert blocked.status_code == 429 and blocked.json()["error"]["code"] == "rate_limited"
    assert 1 <= int(blocked.headers["Retry-After"]) <= 60


def test_daily_and_site_wide_limits(tmp_path):
    store = JobStore(tmp_path / "jobs.sqlite")
    limits = Limits(per_minute=100, per_day=3, site_per_day=5)
    start = 1_000_000.0
    for i in range(3):
        store.submit("Question?", "visitor-a", now=start + i * 120)
    with pytest.raises(RateLimited, match="today"):
        check(store, "visitor-a", limits, now=start + 400)
    check(store, "visitor-a", limits, now=start + 86_401)  # a day later the oldest has expired
    for i in range(2):
        store.submit("Question?", "visitor-b", now=start + 500 + i)
    with pytest.raises(RateLimited, match="all visitors"):
        check(store, "visitor-c", limits, now=start + 600)


def test_visitor_ids_are_scrambled_not_raw_addresses(tmp_path):
    app, client = client_with(tmp_path, lambda q: {})
    job = client.post("/api/questions", json={"question": "Question?"}).json()
    stored = app.state.store.get(job["id"])["client"]
    assert stored != "testclient" and len(stored) == 16