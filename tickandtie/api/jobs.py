"""The job list for submitted questions, kept in SQLite so nothing is lost on a restart (Task 7).

Jobs are answered in arrival order (SQLite's rowid). A job that was running when the server stopped
goes back in the queue when it starts again."""
import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path

SCHEMA = """CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY, question TEXT NOT NULL, client TEXT NOT NULL, status TEXT NOT NULL,
    created REAL NOT NULL, started REAL, finished REAL, result TEXT)"""


class JobStore:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        with self.lock:
            self.db.execute(SCHEMA)
            self.db.execute("UPDATE jobs SET status = 'queued', started = NULL WHERE status = 'running'")
            self.db.commit()

    def submit(self, question, client):
        job_id = uuid.uuid4().hex
        with self.lock:
            self.db.execute("INSERT INTO jobs (id, question, client, status, created) VALUES (?, ?, ?, 'queued', ?)",
                            (job_id, question, client, time.time()))
            self.db.commit()
        return job_id

    def claim(self):
        """The oldest queued job as (id, question), now marked running; None if the queue is empty."""
        with self.lock:
            row = self.db.execute("SELECT id, question FROM jobs WHERE status = 'queued' ORDER BY rowid LIMIT 1").fetchone()
            if row is None:
                return None
            self.db.execute("UPDATE jobs SET status = 'running', started = ? WHERE id = ?", (time.time(), row["id"]))
            self.db.commit()
            return row["id"], row["question"]

    def finish(self, job_id, result, status="done"):
        with self.lock:
            self.db.execute("UPDATE jobs SET status = ?, finished = ?, result = ? WHERE id = ?",
                            (status, time.time(), json.dumps(result), job_id))
            self.db.commit()

    def get(self, job_id):
        """The job as a dict, with its queue position while queued; None if unknown."""
        with self.lock:
            row = self.db.execute("SELECT rowid, * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if row is None:
                return None
            job = dict(row)
            if job["status"] == "queued":
                job["position"] = self.db.execute(
                    "SELECT COUNT(*) FROM jobs WHERE status = 'queued' AND rowid <= ?", (job["rowid"],)).fetchone()[0]
        job["result"] = json.loads(job["result"]) if job["result"] else None
        return job

    def purge(self, max_age_seconds):
        """Delete jobs older than max_age_seconds. Returns how many were deleted."""
        with self.lock:
            cursor = self.db.execute("DELETE FROM jobs WHERE created < ?", (time.time() - max_age_seconds,))
            self.db.commit()
            return cursor.rowcount