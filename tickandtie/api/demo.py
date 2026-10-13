"""Demo mode (decision 0019): when the hosted model is unavailable, the site keeps working honestly.

Questions that need no model (refusals, unreported figures, the risk-factor diff) are still answered.
Other questions get a saved answer from the deployment check if one exists, clearly labelled, or a
message listing the saved questions. The switch lasts a few minutes, then live answers are tried again."""
import json
import os
import time
from pathlib import Path

SAVED = Path(__file__).resolve().parents[2] / "eval" / "results" / "system_hosted.jsonl"
SAVED_NOTE = "Live answers are paused, so this is a saved answer from the October 2026 evaluation of the hosted model."
PAUSED = ("Live answers are paused right now. You can still ask what changed in a company's risk factors, "
          "or try one of the saved questions.")


def normalise(question):
    return " ".join(question.lower().split())


def load_saved(path):
    """Saved answers from an evaluation run, keyed by the normalised question."""
    saved = {}
    path = Path(path)
    if not path.exists():
        return saved
    for line in path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line) if line.strip() else {}
        if record.get("answer"):
            saved[normalise(record["question"])] = {
                "question": record["question"], "answer": record["answer"], "refusal": None,
                "sources": {i: text.split("\n")[0] for i, text in (record.get("evidence") or {}).items()},
                "periods": record.get("periods") or [], "notes": record.get("notes") or [],
                "removed": record.get("removed") or 0, "seconds": 0}
    return saved


class DemoMode:
    def __init__(self, minutes=None, saved_path=SAVED, clock=time.time):
        self.minutes = float(os.environ.get("TICKANDTIE_DEMO_MINUTES", 10)) if minutes is None else minutes
        self.clock = clock
        self.until, self.reason = 0.0, ""
        self.saved = load_saved(saved_path)

    def forced(self):
        return os.environ.get("TICKANDTIE_FORCE_DEMO") == "1"

    def active(self):
        return self.forced() or self.clock() < self.until

    def trip(self, reason):
        """Switch to demo mode for a few minutes. The reason is kept for the logs, never shown to visitors."""
        self.until, self.reason = self.clock() + self.minutes * 60, reason

    def status(self):
        if self.forced():
            return {"mode": "demo", "reason": "Live answers are switched off."}
        if self.active():
            return {"mode": "demo", "reason": "Live answers are paused for a few minutes.",
                    "retry_after": max(1, int(self.until - self.clock()))}
        return {"mode": "live"}

    def questions(self):
        return [entry["question"] for entry in self.saved.values()]

    def answer_for(self, question):
        saved = self.saved.get(normalise(question))
        if saved:
            result = {key: value for key, value in saved.items() if key != "question"}
            return {**result, "notes": saved["notes"] + [SAVED_NOTE], "mode": "demo", "saved": True}
        return {"answer": None, "refusal": PAUSED, "sources": {}, "periods": [], "notes": [], "removed": 0,
                "seconds": 0, "mode": "demo", "saved": False, "suggestions": self.questions()[:5]}