"""Tests for the job list, the worker and the API, with a fake answer function (no model needed)."""
from fastapi.testclient import TestClient

from tickandtie.api.app import create_app
from tickandtie.api.jobs import JobStore


def client_with(tmp_path, answer):
    app = create_app(JobStore(tmp_path / "jobs.sqlite"), answer=answer, start_worker=False)
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