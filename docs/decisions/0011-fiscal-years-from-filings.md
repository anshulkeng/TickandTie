# 0011: Fiscal years come from the filings

Status: Accepted, October 2026

## Context
"2025" means different periods for different companies. Apple's fiscal 2025 ended on 27 September 2025, Walmart's fiscal 2026 ended on 31 January 2026, and Johnson & Johnson's fiscal 2022 ended on 1 January 2023. A calendar rule guesses some of these wrong.

## Decision
A fiscal year's label is the fiscal year of the 10-K whose latest annual period it is. The SEC records that year with each filing, and it matches what the company calls the year. A year in a question means the company's own fiscal year, and every answer states the real start and end dates.

## Alternatives considered
- The calendar year in which the period ends: wrong for years that end in the first days of January, as Johnson & Johnson's sometimes do.
- The SEC frame field: aligned to calendar periods, not to how companies name their years.

## Consequences
- This depends on the SEC's fiscal-year field being right for each filing. `scripts/try_numbers.py` prints every company's years so they can be checked by eye; on the first run all 12 matched the companies' real year ends.
- "Walmart 2025" means Walmart's fiscal 2025, which ran from February 2024 to January 2025. The answer says so explicitly.