"""The Tick & Tie web API (Task 7): submit a question, then check back for the answer.

Run locally:  uvicorn tickandtie.api.app:create_app --factory --port 8000

Every error has one format: {"error": {"code": ..., "message": ...}}, with no internal details.
Visitors are identified only by a salted, scrambled code of their address, used for rate limits.
Every answer says whether it is "live" or "demo" (decision 0019)."""
import dataclasses
import hashlib
import hmac
import os
import re
import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from starlette.exceptions import HTTPException

from tickandtie import config
from tickandtie.api.demo import DemoMode
from tickandtie.api.jobs import JobStore
from tickandtie.api.limits import Limits, RateLimited, check
from tickandtie.api.worker import Worker
from tickandtie.llm import ModelUnavailable

JOBS_DB = config.DATA_DIR / "jobs.sqlite"
CONTROL = re.compile(r"[\x00-\x1f\x7f]")
CODES = {400: "bad_request", 404: "not_found", 405: "method_not_allowed"}
INVALID = "A question must be 3 to 300 characters of plain text."
INTERNAL = "Something went wrong. Please try again."


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=300)

    @field_validator("question")
    @classmethod
    def clean(cls, value):
        value = " ".join(CONTROL.sub(" ", value).split())
        if len(value) < 3:
            raise ValueError("too short")
        return value


def error(status, code, message, headers=None):
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status, headers=headers)


def client_id(request, salt):
    """A salted, scrambled code for the visitor's address. The address itself is never stored.
    A proxy's X-Forwarded-For is trusted only when TICKANDTIE_TRUST_PROXY=1, so visitors cannot fake it."""
    address = request.client.host if request.client else "unknown"
    if os.environ.get("TICKANDTIE_TRUST_PROXY") == "1":
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            address = forwarded.split(",")[0].strip()
    return hmac.new(salt, address.encode("utf-8"), hashlib.sha256).hexdigest()[:16]


def as_dict(result, mode):
    return {"answer": result.answer, "refusal": result.refusal, "sources": result.sources,
            "periods": result.periods, "notes": result.notes, "removed": len(result.removed),
            "seconds": result.seconds, "mode": mode, "saved": False}


def answer_with_pipeline(demo, ask_fn=None, make_deps=None):
    """The answer function used by the worker: the full pipeline, with demo mode around it.

    In demo mode the pipeline still runs, but its model calls are blocked, so anything that needs no model
    (refusals, unreported figures, the risk-factor diff) is still answered. A failed model call switches
    the site to demo mode and the question gets a saved answer or a clear message instead."""
    if ask_fn is None or make_deps is None:
        from tickandtie.agents import pipeline
        ask_fn = ask_fn or pipeline.ask
        make_deps = make_deps or pipeline.default_deps
    held = {}

    def no_model_decide(question):
        return None, "demo mode: the routing model was not called"

    def no_model_chat(messages):
        raise ModelUnavailable("demo mode: the model was not called")

    def answer(question):
        if "deps" not in held:
            held["deps"] = make_deps()
        live = not demo.active()
        deps = held["deps"] if live else dataclasses.replace(held["deps"], decide=no_model_decide, chat=no_model_chat)
        try:
            return as_dict(ask_fn(question, deps), "live" if live else "demo")
        except ModelUnavailable as exc:
            if live:
                demo.trip(str(exc))
            return demo.answer_for(question)

    return answer


def create_app(store=None, answer=None, start_worker=True, limits=None, salt=None, demo=None):
    store = store or JobStore(JOBS_DB)
    demo = demo or DemoMode()
    worker = Worker(store, answer or answer_with_pipeline(demo))
    limits = limits or Limits.from_env()
    salt = salt or os.environ.get("TICKANDTIE_IP_SALT", "").encode("utf-8") or secrets.token_bytes(32)

    @asynccontextmanager
    async def lifespan(app):
        if start_worker:
            worker.start()
        yield
        if start_worker:
            worker.shutdown()

    app = FastAPI(title="Tick & Tie API", lifespan=lifespan)
    app.state.store, app.state.worker, app.state.demo = store, worker, demo

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return error(exc.status_code, CODES.get(exc.status_code, "error"), str(exc.detail),
                     getattr(exc, "headers", None))

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return error(422, "invalid_question", INVALID)

    @app.exception_handler(RateLimited)
    async def limited(request, exc):
        return error(429, "rate_limited", exc.message, {"Retry-After": str(exc.retry_after)})

    @app.exception_handler(Exception)
    async def internal(request, exc):
        return error(500, "internal_error", INTERNAL)

    @app.post("/api/questions", status_code=202)
    def submit(body: Question, request: Request):
        client = client_id(request, salt)
        check(store, client, limits)
        job_id = store.submit(body.question, client)
        job = store.get(job_id)
        return {"id": job_id, "status": job["status"], "position": job.get("position")}

    @app.get("/api/questions/{job_id}")
    def look_up(job_id: str):
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

    @app.get("/api/status")
    def status():
        return demo.status()

    @app.get("/api/demo")
    def saved_questions():
        return {"questions": demo.questions()}

    @app.get("/api/health/live")
    def live():
        return {"status": "ok"}

    return app