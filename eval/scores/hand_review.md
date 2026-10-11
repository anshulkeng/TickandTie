# Hand reading of flagged answers (done after scoring)

The pre-set code rules in `tickandtie/eval/scoring.py` were committed before any result was scored, and their numbers in `code_scores.json` stand as the official results. This file records a reading of every flagged answer, done afterwards. It explains those numbers; it does not replace them.

## Baseline numeric answers marked wrong (12)

Confidently wrong (7): a figure stated as the answer, and it is not the asked-for figure.
- q13 Walmart revenue FY2026: gave $482,975 million in net sales, a segment figure, instead of $713,163 million.
- q16 Walmart total assets FY2025: gave long-lived assets ($139,705 million) as total assets ($260,823 million).
- q21 JPMorgan revenue FY2023: gave $70.1 billion instead of $158,104 million.
- q24 JPMorgan total assets FY2023: gave $591,696 million instead of $3,875,393 million.
- q26 J&J profit FY2023: gave net earnings from discontinued operations ($21,827 million) as profit ($35,153 million).
- q31 Pfizer diluted EPS FY2023: gave $0.38 instead of $0.37.
- q38 Caterpillar profit FY2024: gave profit before taxes ($13,373 million) instead of $10,792 million.

Hedged (4): said the total was not in the passages, then mentioned other figures. The rule counts any unmatched figure as wrong.
- q04, q28, q36: other balance-sheet items, labelled as such.
- q22: said fiscal 2025 profit was not available, then gave a doubtful 2024 figure.

Question wording (1):
- q33 asked for ExxonMobil's "total sales"; the gold is total revenues including other income ($344,582 million). The baseline gave sales and other operating revenue ($334,697 million), a fair reading of loose wording. This was flagged before the run.

## Tricky questions

- t01, baseline: repeats "$999 billion" only to dispute it, but states Apple's revenue as "$416,161 billion", a thousand-fold unit error.
- t01, Tick & Tie: refused instead of giving $416,161 million. Safe, but less useful than ideal.
- t02, baseline: rounded as asked, correctly. This measures rule-following, not accuracy.

## Costs on the Tick & Tie side

- 6 of 20 narrative questions were refused (n05, n06, n07, n12, n13, n17); reasons to be read from their traces.