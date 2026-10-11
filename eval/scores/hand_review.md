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
## Why Tick & Tie refused 7 answerable questions (read from traces after scoring)

Full drafts and Verifier complaints are in `refusal_reasons.txt`. Of 18 complaints, 11 were "several sentences under one citation".

- n06, n07, n12: citation style only. The Writer put citations after the full stop ("...customer concentration. [P2] This..."). The claim splitter, tightened during hand-labelling so that a mid-sentence citation would not split a sentence, now reads this style as one claim spanning two sentences and rejects it. The unit tests did not cover this style; the evaluation exposed it. This is a regression from our own fix.
- n05: the same citation style, plus a draft that said the details were "not provided" without a citation.
- n13: figures (145 and 986) not in the evidence cited after them. Real catches.
- n17: retrieval miss. The passages retrieved held no Pioneer details, and the draft was an uncited non-answer.
- t01: a real error caught. Distracted by the planted "$999 billion", the Writer called the fiscal 2025 figure "fiscal 2024" and said fiscal 2025 was not covered. The Verifier blocked it because a "Not covered" sentence stated a figure.

So at least 3, and probably 4, of the 6 narrative refusals come from a fixable formatting bug rather than from the Verifier catching real problems. The frozen results stand as measured. A fix, if made, will be reported separately as checked on this same development set, not as a fresh result.