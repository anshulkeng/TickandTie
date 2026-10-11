# 0010: Hybrid search with reciprocal rank fusion

Status: Accepted, October 2026

## Context
There are two indexes over the 10-K chunks: meaning (bge-small embeddings in ChromaDB) and words (BM25). The agents need one ranking, and the choice should come from measurement, not assumption.

## How it was measured
- 12 questions, one per company, each asked twice: as written, using the filing's own terms, and paraphrased without them. That makes 24 searches, each filtered to the right company.
- A chunk counts as correct if it is from the right company, sits in an allowed Item, and contains a key phrase. Script: `scripts/check_retrieval.py`. Questions: `eval/retrieval_questions.json`.
- The decision rule was fixed before the final run: highest recall@5, then highest MRR, then hybrid on a full tie.

## Results
First run (12 questions as written, original answer key): words 12/12 (MRR 0.89), hybrid 11/12 (0.88), meaning 11/12 (0.85).

Two answer keys turned out too narrow and were corrected openly, with the reason recorded in the question file: Apple repeats its supply passage in Item 8, and Exxon discusses climate rules in Item 7.

Final run (recall@5, MRR@10):

| Method | As written | Paraphrased | Both (24) |
| --- | --- | --- | --- |
| Meaning only | 11/12, 0.89 | 10/12, 0.66 | 21/24, 0.77 |
| Words only | 12/12, 0.96 | 10/12, 0.60 | 22/24, 0.78 |
| Hybrid | 12/12, 1.00 | 11/12, 0.76 | 23/24, 0.88 |

## Decision
Use hybrid search: the top 30 from each index, merged with reciprocal rank fusion (k = 60). Each chunk is embedded with a header naming its company, period and Item, and questions get the search prefix bge models are trained with.

## Alternatives considered
- Words only: as good when a question uses the filing's own terms, clearly worse on paraphrases (MRR 0.60).
- Meaning only: weakest on exact terms such as product names.
- Weighted fusion or a tuned k: not tried. 24 questions are too few to tune on without overfitting.

## Consequences
- One miss remains: the Exxon paraphrase, with the correct chunk at rank 8. Word search found nothing, and fusion favours chunks both lists agree on, which pushed meaning search's rank-3 hit down. When only one method finds the answer, fusion can lose it.
- The correctness check is a phrase match. It can mark a good answer wrong (Exxon's top result discusses the energy transition without the word "climate") and can accept a passage that only mentions the phrase.
- The question set is small and written by me. Task 5 replaces it with a larger evaluation.
- Rebuilding the meaning index takes about 30 minutes on CPU. Searching reuses the saved index.