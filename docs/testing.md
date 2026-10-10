# Testing strategy

## Levels

| Level | Where | Runs in CI | What it covers |
| --- | --- | --- | --- |
| Unit tests | tests/ | Yes, on every pull request | Parsing, cleaning, Item fallbacks, predecessor CIKs, XBRL flattening, chunking. No network. |
| Pipeline checks | scripts/ | No (needs the SEC and Ollama) | smoke_test, fetch_metadata, ingest warnings, load_facts tie-outs. Run locally after any change to ingestion. |
| Retrieval check | Task 3 | No | 10 hand-written questions must each find the Item that holds the answer. |
| Evaluation | eval/, Task 5 | No | Numeric, narrative and unanswerable questions, a plain-RAG baseline, and a calibrated judge. |
| API tests | tests/, Task 7 | Yes | Input validation, error format, submit and poll, rate limits, using a fake agent graph. |
| Website tests | web/, Task 8 | Yes | The ask-a-question flow end to end, and an automated accessibility check. |

## What may be faked
- The SEC network, in unit tests. A fake client stands in for EdgarClient.
- The language model, in unit and API tests. Real model calls belong to evaluation.

## What is never faked
- My own logic: cleaning, fallbacks, period handling, chunking, verification.
- DuckDB. Tests that need the facts table use a real in-memory database.

## Rules
- Never edit a test to make it pass. Fix the code, or stop and report.
- A bug gets a failing test first, then the fix.
- Every skipped test carries a written reason.
- main only accepts pull requests with a green test check. GitHub enforces this with a ruleset.
- Any decision record that encodes logic has a test that locks it in. Today: 0003 (period dates), 0004 (predecessor CIKs) and 0005 (Item fallbacks).

## Coverage
I don't chase a coverage percentage. The target is that every rule a wrong answer could come from has a test.