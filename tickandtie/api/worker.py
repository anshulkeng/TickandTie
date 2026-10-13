"""One background worker that answers queued questions in order (Task 7; one worker by design)."""
import threading

FAILED = "Something went wrong while answering. Please try again."


class Worker:
    def __init__(self, store, answer, poll_seconds=0.2):
        self.store, self.answer, self.poll_seconds = store, answer, poll_seconds
        self.stopping = threading.Event()
        self.thread = threading.Thread(target=self.loop, name="tickandtie-worker", daemon=True)

    def run_once(self):
        """Answer the oldest queued question. Returns True if there was one."""
        job = self.store.claim()
        if job is None:
            return False
        job_id, question = job
        try:
            self.store.finish(job_id, self.answer(question))
        except Exception as exc:  # the visitor sees a friendly message; the error type is kept for debugging
            self.store.finish(job_id, {"error": FAILED, "detail": type(exc).__name__}, status="failed")
        return True

    def loop(self):
        while not self.stopping.is_set():
            if not self.run_once():
                self.stopping.wait(self.poll_seconds)

    def start(self):
        self.thread.start()

    def shutdown(self):
        self.stopping.set()
        self.thread.join(timeout=5)