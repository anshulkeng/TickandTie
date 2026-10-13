"""The Tick & Tie web API (Task 7): submit a question, then check back for the answer.

Run locally:  uvicorn tickandtie.api.app:create_app --factory --port 8000"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from tickandtie import config
from tickandtie.api.jobs import JobStore
from tickandtie.api.worker import Worker

JOBS_DB = config.DATA_DIR / "jobs.sqlite"


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=300)


def answer_with_pipeline():
    """The real answer function: the full pipeline, set up on first use inside the worker thread."""
    from tickandtie.agents.pipeline import ask, default_deps
    held = {}

    def answer(question):
        if "deps" not in held:
            held["deps"] = default_deps()
        result = ask(question, held["deps"])
        return {"answer": result.answer, "refusal": result.refusal, "sources": result.sources,
                "periods": result.periods, "notes": result.notes, "removed": len(result.removed),
                "seconds": result.seconds}

    return answer


def create_app(store=None, answer=None, start_worker=True):
    store = store or JobStore(JOBS_DB)
    worker = Worker(store, answer or answer_with_pipeline())

    @asynccontextmanager
    async def lifespan(app):
        if start_worker:
            worker.start()
        yield
        if start_worker:
            worker.shutdown()

    app = FastAPI(title="Tick & Tie API", lifespan=lifespan)
    app.state.store, app.state.worker = store, worker

    @app.post("/api/questions", status_code=202)
    def submit(body: Question):
        job_id = store.submit(body.question.strip(), client="anonymous")
        job = store.get(job_id)
        return {"id": job_id, "status": job["status"], "position": job.get("position")}

    @app.get("/api/questions/{job_id}")
    def check(job_id: str):
        job = store.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="No question with that id.")
        reply = {"id": job_id, "status": job["status"], "question": job["question"]}
        if job["status"] == "queued":
            reply["position"] = job["position"]
        if job["status"] == "done":
            reply["result"] = job["result"]
        if job["status"] == "failed":
            reply["error"] = job["result"]["error"]
        return reply

    @app.get("/api/health/live")
    def live():
        return {"status": "ok"}

    return app