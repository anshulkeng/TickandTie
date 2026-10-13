"""Rate limits for submitted questions (Task 7): per visitor per minute and per day, and for the whole site per day.

They are counted from the job list, so they survive restarts. Change them with environment variables."""
import math
import os
import time
from dataclasses import dataclass

MINUTE, DAY = 60, 86_400


@dataclass
class Limits:
    per_minute: int = 5
    per_day: int = 30
    site_per_day: int = 500

    @classmethod
    def from_env(cls):
        return cls(int(os.environ.get("TICKANDTIE_LIMIT_PER_MINUTE", 5)),
                   int(os.environ.get("TICKANDTIE_LIMIT_PER_DAY", 30)),
                   int(os.environ.get("TICKANDTIE_LIMIT_SITE_PER_DAY", 500)))


class RateLimited(Exception):
    def __init__(self, message, retry_after):
        super().__init__(message)
        self.message, self.retry_after = message, retry_after


def wait_text(seconds):
    if seconds < 120:
        return f"{seconds} seconds"
    if seconds < 7200:
        return f"about {math.ceil(seconds / 60)} minutes"
    return f"about {math.ceil(seconds / 3600)} hours"


def check(store, client, limits, now=None):
    """Raise RateLimited, with a retry time in seconds, if this visitor or the site is over a limit."""
    now = time.time() if now is None else now
    rules = [
        (MINUTE, limits.per_minute, client,
         "You have asked {limit} questions in the last minute. Please wait {wait}."),
        (DAY, limits.per_day, client,
         "You have reached today's limit of {limit} questions. Please try again in {wait}."),
        (DAY, limits.site_per_day, None,
         "Tick & Tie has reached today's limit of {limit} questions across all visitors. Please try again in {wait}."),
    ]
    for window, limit, who, message in rules:
        since = now - window
        if store.count_since(since, who) >= limit:
            retry = max(1, math.ceil(store.oldest_since(since, who) + window - now))
            raise RateLimited(message.format(limit=limit, wait=wait_text(retry)), retry)