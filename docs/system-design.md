# System design

## Problem
Language models reading 10-K filings get the prose roughly right and the numbers wrong: the wrong period, the wrong unit, or bad arithmetic. The SEC already publishes the numbers in machine-readable form (XBRL company facts). Tick & Tie treats those as ground truth, lets agents look numbers up and compute with them in Python, and refuses when the data is not there.

## Users
- **Visitor**: asks a question on the public site. No account, nothing personal stored. The main audience is hiring panels judging the project; anyone researching a covered company can use it too.
- **Maintainer (me)**: runs ingestion, evaluation and deployment.

There is no tenancy. Everyone sees the same read-only corpus.

## Core flows
1. **Numeric question**, e.g. "What were Walmart's net sales in fiscal 2025?" The answer gives the value, unit, period, XBRL concept and accession number.
2. **Narrative question**, e.g. "What supply chain risks does Apple describe?" The answer quotes passages and cites accession number and Item.
3. **Comparison** across years or companies.
4. **Risk-factor change** between two annual reports (Task 6).
5. **Unanswerable question**: a refusal that says what is missing.

## Functional requirements
- Resolve tickers to CIKs, including predecessor CIKs.
- Fetch and cache 10-K filings and XBRL company facts, respecting SEC fair access.
- Split 10-Ks into Items, record where each Item's text came from, and flag pointers and suspicious splits.
- Route each question to a numeric, narrative, comparison or risk-diff path.
- Numbers come only from the facts table or Python. The language model never writes a figure.
- Every claim cites accession number and Item; every number cites XBRL concept and period.
- A verifier checks numbers and citations, allows one rewrite, then refuses with a reason.
- Every run writes a trace (agent, inputs, outputs, timing).
- An evaluation harness runs the full question set with one command.

## Non-functional requirements
- **Correctness over speed**: no number reaches the user unless it matches XBRL within 0.5%.
- **Cost**: free tooling only. The custom domain is the one planned spend.
- **Privacy**: no accounts. Questions and traces are logged for debugging without personal data.
- **Reproducibility**: pinned dependencies, temperature 0, fixed seeds, and all data rebuildable from the SEC.
- **Latency**: measured per agent; the target is set after the first baseline, not guessed.
- **Availability**: best effort. This is a portfolio project, not a paid service.

## Capacity, year one
- **Data**: 12 companies, 36 annual reports, 128,966 XBRL values, about 15,000 text chunks. Fits on one laptop.
- **Traffic**: low, a handful of visitors a day.
- **Bottleneck**: the language model. qwen2.5:7b on a 4 GB GTX 1650 answers one question at a time and takes seconds to tens of seconds (to be measured). Questions therefore queue (submit, then poll), and rate limiting protects the model.

## Out of scope
- User accounts, payments, multi-tenancy
- Non-US filers, 10-Qs and 8-Ks, real-time prices, investment advice
- Paid APIs

## Open questions
- **Hosting** (Task 9): a 7B model on free hosting is unlikely. Options are a smaller hosted model, serving from my own machine, or a recorded demo.
- **Fiscal-year naming** (Task 4): NVIDIA and Walmart years end in late January, so "fiscal 2025" and "2025" can mean different periods.
- **Which revenue** (Task 4): Walmart and JPMorgan each report two revenue figures. The answer must say which one it used.
- **Known gaps**: XOM FY2023 and WMT FY2024 are missing some text. Decide after evaluation whether custom extractors are worth it.