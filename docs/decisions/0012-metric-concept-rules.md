# 0012: Everyday metrics map to SEC concepts by written rules

Status: Accepted, October 2026

## Context
Companies use different SEC concepts for the same idea and switch between them over time (Pfizer and Costco did between 2023 and 2026). Some report two revenue figures: Walmart's total revenues include membership income, its net sales do not. For a bank, the meaningful revenue is net of interest expense.

## Decision
- 12 metrics at launch, each with an ordered list of concepts. The first concept reported for that year is used; any others found are kept as alternates and mentioned in the answer.
- JPMorgan's revenue uses net revenue first.
- When a value was re-reported in a later filing, the latest filed version is used.
- Every answer names the concept it used.

## Alternatives considered
- Let the language model choose the concept: unreliable and impossible to verify.
- One fixed concept per metric: misses companies that switch concepts.

## Checked on real data
A coverage check of the 12 metrics across all 12 companies (latest fiscal year) found 20 gaps.

- Fixed with fallback concepts, chosen from what each company actually reports: Caterpillar net income (`NetIncomeLossAvailableToCommonStockholdersBasic`, then `ProfitLoss`); long-term debt for ExxonMobil, Coca-Cola and Verizon (`LongTermDebtAndCapitalLeaseObligations`) and JPMorgan (the total including current maturities, because banks do not split debt); Verizon capital spending (`PaymentsToAcquireOtherProductiveAssets`).
- Left as refusals, because the company does not report the line: operating income (JNJ, PFE, XOM, JPM), R&D (WMT, COST, KO, VZ, JPM), total liabilities (WMT, KO, VZ), and JPMorgan's cash and capital spending. Total liabilities could be derived from other lines, but a derived figure is not a reported one, so it is not shown at launch.

## Consequences
- Metrics outside the list are refused rather than guessed.
- Adding a metric or fallback needs a code change and a test.
- A rule can pick a different figure from the one a company headlines. Naming the concept and showing alternates makes that visible.
- "Latest filing wins" means a restated figure can differ from what a company first announced, so answers name the filing a number came from.