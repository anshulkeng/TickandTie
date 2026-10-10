# 0002: XBRL facts are the ground truth for numbers

Status: Accepted, October 2026

## Context
Language models misreport figures they read from filing text. The SEC already publishes every reported number as structured XBRL company facts.

## Decision
Every number in an answer comes from the DuckDB facts table or from Python arithmetic on those values. The language model writes the prose around numbers but never produces a figure. A verifier rejects any answer whose numbers do not match XBRL within 0.5%.

## Alternatives considered
- Let the model read numbers from the text and trust it: the exact failure this project exists to fix.
- Parse tables out of the 10-K HTML: fragile, and XBRL already holds the values.

## Consequences
- Numeric answers can be checked. The first tie-out matched Apple's published revenue exactly: 383,285 and 394,328 (USD millions, fiscal 2023 and 2022).
- Questions must be mapped to XBRL concepts, which differ between companies and change over time. That mapping is the main problem in Task 4.
- A number that exists only in text and was never tagged cannot be answered. The system refuses instead.