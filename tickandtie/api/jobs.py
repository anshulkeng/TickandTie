"""The job list for submitted questions, kept in SQLite so nothing is lost on a restart (Task 7).

Jobs are answered in arrival order (SQLite's rowid). A job that was running when the server stopped
goes back in the queue. A queued job whose page stopped checking for it is dropped as abandoned,
so it cannot block the queue. Rate limits are counted from this list too."""
import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path

ABANDON_AFTER_SECONDS = 120  # generous, because phones slow down background tabs
ABANDONED = "This question was dropped because the page stopped checking for it. Please ask again."
SCHEMA = [
    """CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY, question TEXT NOT NULL, client TEXT NOT NULL, status TEXT NOT NULL,
        created REAL NOT NULL, started REAL, finished REAL, result TEXT, last_seen REAL)""",
]
INDEXES = [
    "CREATE INDEX IF NOT EXISTS jobs_by_client ON jobs (client, created)",
    "CREATE INDEX IF NOT EXISTS jobs_by_time ON jobs (created)",
]


class JobStore:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        with self.lock:
            for statement in SCHEMA:
                self.db.execute(statement)
            columns = {row[1] for row in self.db.execute("PRAGMA table_info(jobs)")}
            if "last_seen" not in columns:  # job lists created before this column existed
                self.db.execute("ALTER TABLE jobs ADD COLUMN last_seen REAL")
            for statement in INDEXES:
                self.db.execute(statement)
            self.db.execute("UPDATE jobs SET status = 'queued', started = NULL WHERE status = 'running'")
            self.db.commit()

    def submit(self, question, client, now=None):
        job_id = uuid.uuid4().hex
        created = time.time() if now is None else now
        with self.lock:
            self.db.execute(
                "INSERT INTO jobs (id, question, client, status, created, last_seen) VALUES (?, ?, ?, 'queued', ?, ?)",
                (job_id, question, client, created, created))
            self.db.commit()
        return job_id

    def claim(self, now=None):
        """The oldest queued job as (id, question), now marked running; None if the queue is empty.
        Queued jobs nobody has checked on for ABANDON_AFTER_SECONDS are dropped first."""
        now = time.time() if now is None else now
        with self.lock:
            self.db.execute(
                "UPDATE jobs SET status = 'abandoned', finished = ?, result = ? "
                "WHERE status = 'queued' AND COALESCE(last_seen, created) < ?",
                (now, json.dumps({"error": ABANDONED}), now - ABANDON_AFTER_SECONDS))
            row = self.db.execute("SELECT id, question FROM jobs WHERE status = 'queued' ORDER BY rowid LIMIT 1").fetchone()
            if row is None:
                self.db.commit()
                return None
            self.db.execute("UPDATE jobs SET status = 'running', started = ? WHERE id = ?", (now, row["id"]))
            self.db.commit()
            return row["id"], row["question"]

    def finish(self, job_id, result, status="done"):
        with self.lock:
            self.db.execute("UPDATE jobs SET status = ?, finished = ?, result = ? WHERE id = ?",
                            (status, time.time(), json.dumps(result), job_id))
            self.db.commit()

    def get(self, job_id, now=None):
        """The job as a dict, with its queue position while queued; None if unknown.
        Looking at a queued job counts as someone still waiting for it."""
        now = time.time() if now is None else now
        with self.lock:
            row = self.db.execute("SELECT rowid, * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if row is None:
                return None
            job = dict(row)
            if job["status"] == "queued":
                self.db.execute("UPDATE jobs SET last_seen = ? WHERE id = ?", (now, job_id))
                self.db.commit()
                job["position"] = self.db.execute(
                    "SELECT COUNT(*) FROM jobs WHERE status = 'queued' AND rowid <= ?", (job["rowid"],)).fetchone()[0]
        job["result"] = json.loads(job["result"]) if job["result"] else None
        return job

    def count_since(self, since, client=None):
        """Questions submitted after a time, by one visitor or (client=None) by everyone."""
        with self.lock:
            if client is None:
                return self.db.execute("SELECT COUNT(*) FROM jobs WHERE created > ?", (since,)).fetchone()[0]
            return self.db.execute("SELECT COUNT(*) FROM jobs WHERE created > ? AND client = ?",
                                   (since, client)).fetchone()[0]

    def oldest_since(self, since, client=None):
        """When the oldest of those questions was submitted."""
        with self.lock:
            if client is None:
                return self.db.execute("SELECT MIN(created) FROM jobs WHERE created > ?", (since,)).fetchone()[0]
            return self.db.execute("SELECT MIN(created) FROM jobs WHERE created > ? AND client = ?",
                                   (since, client)).fetchone()[0]

    def queued(self):
        """How many questions are waiting."""
        with self.lock:
            return self.db.execute("SELECT COUNT(*) FROM jobs WHERE status = 'queued'").fetchone()[0]

    def purge(self, max_age_seconds):
        """Delete jobs older than max_age_seconds. Returns how many were deleted."""
        with self.lock:
            cursor = self.db.execute("DELETE FROM jobs WHERE created < ?", (time.time() - max_age_seconds,))
            self.db.commit()
            return cursor.rowcount