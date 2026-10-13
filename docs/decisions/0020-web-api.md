# 0020: The web API: submit and check back, one worker, limits and privacy by default

Status: Accepted, October 2026

## Context
The website needs an API in front of the pipeline. Answers usually take 1 to 3 seconds on the hosted model, but some took over a minute in the deployment check. The API must control cost, never leak internal details or visitor data, and keep working honestly when the hosted model is unavailable (decision 0019).

## Decision
- Submit, then check back: POST /api/questions returns a ticket and queue position; GET /api/questions/{id} returns the status, then the answer. A slow answer cannot time out a browser request.
- Jobs are kept in SQLite with their arrival order; a job that was running when the server stopped goes back in the queue.
- One worker answers questions in order, for cost control and simplicity.
- Rate limits, counted from the job list so they survive restarts: 5 a minute and 30 a day per visitor, 500 a day for the whole site. Over a limit: 429 with Retry-After and a plain message.
- Visitors are identified only by a salted, scrambled 16-character code of their address. Addresses are never stored. X-Forwarded-For is trusted only behind a configured proxy.
- Questions are deleted after 7 days. Logs are JSON, one line per request and per answer, with timings, mode and question length, never question text or addresses. Uvicorn's own access log is turned off (--no-access-log) because it prints addresses.
- One error format, {"error": {"code", "message"}}, with no internal details. Questions are cleaned of control characters and limited to 3 to 300 characters.
- Each model call gives up after 40 seconds. A failed or timed-out call switches the site to demo mode for 10 minutes; every answer is labelled live or demo.
- /api/health checks the job list, facts database, search index and filings (503 if any is missing); /api/health/live only confirms the process is up. Only the website's origin may call the API from a browser (CORS).
- Every setting can be changed with an environment variable (.env.example).

## Alternatives considered
- One long request per question: simpler, but hosting platforms and browsers cut long requests off.
- Streaming the answer: the Verifier checks the whole answer before it is shown, so there is nothing safe to stream early.
- Redis and Celery for the queue: the standard production choice, but an extra service for one worker.

## Consequences
- The queue and rate limits assume one server instance. Running several would need a shared store.
- TICKANDTIE_IP_SALT must be set in production. Without it, a new random salt is used on each start, so visitor codes and per-visitor limits reset on every restart.
- Checking back creates many small requests; the website should check less often as the wait grows.
- Found while running it: uvicorn's default access log printed visitor addresses, which would have broken the privacy promise on a host that keeps logs.
