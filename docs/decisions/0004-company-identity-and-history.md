# 0004: A ticker is not a company identity; read the full filing history

Status: Accepted, October 2026

## Context
Two surprises in Task 2. ExxonMobil moved under a new Texas parent company on 1 July 2026, so the ticker XOM now maps to a new CIK with no 10-Ks, while every earlier report sits under the old CIK 0000034088. Separately, the SEC's "recent filings" list stops at 1,000 entries, which for JPMorgan covers only about a year.

## Decision
`config.PREDECESSOR_CIKS` lists earlier CIKs for a ticker, and every lookup searches all of them. `EdgarClient.filings()` also reads the older pages that the submissions file points to, not just the recent block.

## Alternatives considered
- Hard-code CIKs instead of tickers: hides the problem and breaks the next time a company reorganises.
- Read only the recent block: JPMorgan showed one 10-K instead of 27.

## Consequences
- XOM has its full history (31 annual reports across both CIKs) and JPM shows 27.
- The predecessor list is maintained by hand. A future reorganisation would show up as a company with zero 10-Ks in `fetch_metadata`, so it would not go unnoticed.
- A unit test covers the predecessor search.