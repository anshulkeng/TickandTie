# 0013: The Router uses rules first and the model for one decision

Status: Accepted, October 2026

## Context
The Router turns a question into a plan: companies, fiscal years, metrics, whether report text is needed, and which 10-K sections to search. A 7B model can misread a company name or a year, and a wrong company or year makes every later step wrong.

## Decision
- Companies, years and metrics are found with plain rules. Companies match by name, alias or ticker; tickers only match in capitals, so ordinary words such as "cost" or "cat" are never read as tickers. Metric phrases match longest first.
- A question that mentions no covered company is refused straight away, with the list of covered companies.
- A question asking for investment advice ("should I buy", "worth buying", "price target") is refused before anything else runs. Tick & Tie reports what companies filed, not whether to trade their shares. The rule is narrow on purpose, and a test checks that questions about a company's own investment, such as R&D spending, are still answered.
- The model makes one structured decision: whether text is needed and which sections to search. Its reply must fit a fixed schema.
- Words such as why, explain, risks or describe always turn text search on. "How much" and "how many" do not.
- If the model fails or replies with something invalid, the Router falls back to default sections and records that in the plan.

## Alternatives considered
- Let the model produce the whole plan: easier to write, but company, year and metric mistakes would be silent.
- No model at all: section choice would rely on keyword lists, which handle unusual questions poorly.

## Consequences
- Companies, years and metrics are fully covered by unit tests.
- Questions about companies not in the corpus never reach the model.
- The section choice can still be wrong. The evaluation in Task 5 measures it.- Added after the Task 5 evaluation, from trying the website: "How did X do?" questions name no figure, so they get the headline figures (revenue, net income, diluted EPS) plus the explaining text. A year with no filing text in the index is named as a gap instead of ending in a bare refusal. These changes were not part of the evaluated system.