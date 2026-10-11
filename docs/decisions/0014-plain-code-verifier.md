# 0014: A plain-code Verifier checks every answer

Status: Accepted, October 2026

## Context
A 7B Writer can copy a number wrongly, attach it to the wrong source, or invent one. Asking a second model to check the first is weak evidence: it can make the same mistakes and its verdicts are not reproducible.

## Decision
The Verifier is plain code.
- The answer is split into claims, each running up to its citation.
- Every sentence must carry its own citation, and the evidence it cites must exist. Abbreviations such as Inc. and initials such as U.S. do not count as sentence ends.
- Every number must match the evidence cited right after it: a fact within 0.5%, or a passage that contains it exactly. Years, dates, form names, Item numbers and citation ids are not treated as figures.
- A sentence starting "Not covered:" needs no citation but may not state numbers.
- A failed answer gets one rewrite with the list of problems. A second failure becomes a refusal that gives the reasons.

## Alternatives considered
- A model as judge: self-grading and not reproducible.
- Checking only XBRL figures: would either forbid useful figures that appear only in filing text, such as employee counts, or let them through unchecked.

## Consequences
- A correct number cited to the wrong source fails. The first live run showed why this matters: the Writer put the total revenue change [F3] after a 59% that came from passage P2. The first version of the check only required the number to appear somewhere in the sentence's citations and let it through; it was tightened, and a test reproduces the case.
- The same run showed the limit of any plain-code check: the passage said Data Center computing revenue grew 59%, and the answer said Data Center revenue. The number was right but what it measured was widened. The Writer has a prompt rule against this, but it did not stop the same widening on the next run, so it stays a known limitation that the Task 5 judge measures.
- The second live run also showed the Writer putting one citation after three sentences. The first version of the check treated everything up to a citation as one claim and let that through; it now requires a citation on every sentence, and a test reproduces the case.
- A figure taken from filing text is checked for being in the filing, not against XBRL. It is what the filing says.
- Rounding within 0.5% is accepted.
- Hand-labelling for the Task 5 judge found the claim splitter cutting a sentence at a mid-sentence citation ("...fiscal 2025 [F1] to $21,893 million..."). Claims now end only at a citation followed by a full stop, and a test reproduces the case.
- The Verifier cannot judge whether a sentence's meaning matches its passage. Faithfulness is measured separately in Task 5.