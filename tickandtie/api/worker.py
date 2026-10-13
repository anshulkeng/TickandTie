"""One background worker that answers queued questions in order (Task 7; one worker by design).

It also deletes jobs older than the retention period (7 days by default), at most once an hour."""
import os
import threading
import time

from tickandtie.api.logs import info, warning

FAILED = "Something went wrong while answering. Please try again."
PURGE_EVERY_SECONDS = 3_600


class Worker:
    def __init__(self, store, answer, poll_seconds=0.2, keep_days=None, clock=time.time):
        self.store, self.answer, self.poll_seconds = store, answer, poll_seconds
        self.keep_days = float(os.environ.get("TICKANDTIE_KEEP_DAYS", 7)) if keep_days is None else keep_days
        self.clock = clock
        self.last_purge = float("-inf")
        self.stopping = threading.Event()
        self.thread = threading.Thread(target=self.loop, name="tickandtie-worker", daemon=True)

    def maintenance(self):
        """Delete jobs older than the retention period, at most once an hour. Returns how many were deleted."""
        now = self.clock()
        if now - self.last_purge < PURGE_EVERY_SECONDS:
            return 0
        self.last_purge = now
        deleted = self.store.purge(self.keep_days * 86_400)
        if deleted:
            info("jobs_deleted", count=deleted, keep_days=self.keep_days)
        return deleted

    def run_once(self):
        """Answer the oldest queued question. Returns True if there was one."""
        job = self.store.claim()
        if job is None:
            return False
        job_id, question = job
        started = time.perf_counter()
        try:
            result = self.answer(question)
            self.store.finish(job_id, result)
            info("job_done", job=job_id, mode=result.get("mode"), answered=result.get("answer") is not None,
                 seconds=round(time.perf_counter() - started, 2), question_chars=len(question))
        except Exception as exc:  # the visitor sees a friendly message; the error type is kept for debugging
            self.store.finish(job_id, {"error": FAILED, "detail": type(exc).__name__}, status="failed")
            warning("job_failed", job=job_id, error=type(exc).__name__)
        return True

    def warm_up(self):
        """Load what the first answer needs (the search indexes) before any visitor is waiting."""
        warm = getattr(self.answer, "warm", None)
        if warm is None:
            return
        started = time.perf_counter()
        try:
            warm()
            info("warmed_up", seconds=round(time.perf_counter() - started, 2))
        except Exception as exc:
            warning("warm_up_failed", error=type(exc).__name__)

    def loop(self):
        self.warm_up()
        while not self.stopping.is_set():
            self.maintenance()
            if not self.run_once():
                self.stopping.wait(self.poll_seconds)

    def start(self):
        self.thread.start()

    def shutdown(self):
        self.stopping.set()
        self.thread.join(timeout=5)