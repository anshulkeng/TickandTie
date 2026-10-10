# 0003: Decide the year from period dates, not the SEC fy field

Status: Accepted, October 2026

## Context
In SEC company facts, `fy` is the fiscal year of the filing that reported a value, not the year the value belongs to. A fiscal 2025 10-K also reports fiscal 2024 and 2023 revenue, and all three are tagged fy=2025. I confirmed this on Apple: each of its filings carries three years of revenue under one fy.

## Decision
Store fy as `filing_fy`. Identify which year a value belongs to from `period_start`, `period_end` and `duration_days`. Annual values are those lasting 350 to 380 days.

## Alternatives considered
- Use fy directly: silently returns the wrong year's numbers.
- Use the SEC `frame` field: it is aligned to calendar periods, so it does not name fiscal years the way companies with non-December year ends do.

## Consequences
- A unit test locks this behaviour in.
- How a question's "2025" maps to a period (NVIDIA's fiscal 2026 ended in January 2026, for example) still has to be settled in Task 4.