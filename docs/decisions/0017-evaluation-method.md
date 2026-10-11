# 0017: How Tick & Tie is evaluated

Status: Accepted, October 2026

## Context
The project's claims (verified figures, honest refusals) need numbers that someone else can check. The easy ways to get flattering numbers are to change the questions, the rules or the judge after seeing results.

## Decision
- A fixed question set (81 questions: numeric, narrative, should-refuse, tricky) is committed before any system runs. Numeric questions and their gold answers are generated with a fixed seed from separate SQL.
- Questions used to build or calibrate the system are excluded.
- Tick & Tie is compared with a plain RAG baseline that uses the same model and search, so the comparison isolates the facts table, Verifier and refusal rules.
- Raw results are committed before scoring, and scoring rules (with unit tests) are committed before they are applied.
- An AI judge is used only if it passes a pass mark against hand labels that is fixed before its first run. Its prompt is not tuned on those labels.
- If the judge fails, faithfulness is measured with blind hand labels on a seeded sample, with the system hidden.
- Anything read or decided after scoring is recorded as such, next to the official numbers rather than replacing them.

## Alternatives considered
- Score with an AI judge without calibrating it: fast, but its numbers would mean nothing. The 3B judge failed calibration (76% agreement).
- Re-run or re-tune until the results look good: rejected; results would not be credible.

## Consequences
- Every number in `eval/RESULTS.md` can be traced through Git history to rules committed before it.
- The results include unflattering findings: narrative refusals, no faithfulness advantage, and a regression found by the evaluation.
- Fixes made after this evaluation are measured as development-set checks, not as fresh results.