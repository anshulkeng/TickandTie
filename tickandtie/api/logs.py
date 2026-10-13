"""Structured logging for the API: one JSON object per line, never with question text or visitor addresses."""
import json
import logging
import sys
import time


class JsonFormatter(logging.Formatter):
    def format(self, record):
        entry = {"time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
                 "level": record.levelname, "event": record.getMessage()}
        entry.update(getattr(record, "fields", {}))
        return json.dumps(entry)


def logger():
    log = logging.getLogger("tickandtie")
    if not log.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        log.addHandler(handler)
        log.setLevel(logging.INFO)
        log.propagate = False
    return log


def info(event, **fields):
    logger().info(event, extra={"fields": fields})


def warning(event, **fields):
    logger().warning(event, extra={"fields": fields})