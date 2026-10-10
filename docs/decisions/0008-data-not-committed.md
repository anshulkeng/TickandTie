# 0008: Data is rebuilt, never committed

Status: Accepted, October 2026

## Context
`data/` holds downloaded filings, the facts database and, later, the search indexes. All of it comes from public SEC sources.

## Decision
`data/` is gitignored. Scripts rebuild it in order: `fetch_metadata`, `ingest_filings`, `load_facts`, and later the index build. The SEC download cache makes rebuilds fast.

## Alternatives considered
- Commit the data, or use Git LFS: large, duplicates public data, and goes stale.

## Consequences
- No backups are needed for data.
- A fresh clone needs one rebuild run with internet access.
- SEC data can change (for example, amended filings), so evaluation results record the date the data was built.