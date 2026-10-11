# Tick & Tie evaluation results (October 2026)

Tick & Tie was compared with a plain RAG baseline on 81 questions about the 12 covered companies. Both used the same model (qwen2.5:7b, local, temperature 0) and the same hybrid search. Method: decision record 0017.

## Headline

- **Figures:** on 48 numeric questions, Tick & Tie gave the correct figure 48 times and a wrong figure 0 times. The baseline was correct 28 times, within 2% twice, and gave a figure that did not match 12 times under the pre-set rule. On a hand reading, 7 of those 12 were confidently wrong.
- **Refusals:** Tick & Tie declined all 10 questions it should not answer. The baseline declined 8 and gave investment advice twice.
- **Cost:** Tick & Tie refused 6 of 20 answerable narrative questions. Traces show that at least 3 of the 6 came from a citation-style bug, not from real problems.
- **Narrative faithfulness:** no advantage shown. On a small blind hand-labelled sample, 8 of 10 Tick & Tie sentences and 10 of 10 baseline sentences were fully supported by their evidence.

## The two systems

- **Tick & Tie:** Router, Numbers agent (SEC XBRL facts in DuckDB), hybrid search, Writer, and a plain-code Verifier. Every figure must match a cited XBRL fact within 0.5% or appear exactly in a cited filing passage. A failed draft gets one rewrite; sentences that still fail are removed, and if nothing verified is left the question is refused.
- **Baseline:** the same hybrid search, filtered to the companies named in the question, the top 6 passages, and one model call asked to answer from the passages and cite them. No facts table, no Verifier, no rewrite, no refusal rules.

## The question set

81 questions, frozen and committed before either system was run (`eval/questions.jsonl`):
- **48 numeric:** each company times revenue, net income, diluted EPS and total assets, in a fiscal year drawn from its latest three (numpy PCG64, seed 2026), with varied wording. Gold answers come from separate SQL over the XBRL facts. They share the metric and fiscal-year rules with the system on purpose, because those rules define a correct answer; published figures were checked by hand for a sample.
- **20 narrative:** hand-written, one or two per company.
- **10 should-refuse:** a company not covered, line items a company does not report, years with no report, a forecast, a stock price, two advice questions.
- **3 tricky:** a planted false figure, a request to round, a currency conversion.
- None of the 10 questions used to build and calibrate the system appear in the set.

Both systems ran every question once at commit `b184b6e`, with no errors. The raw results were committed before any scoring (`eval/results/`).

## Code-scored results

Scoring rules (`tickandtie/eval/scoring.py`) were committed before any result was scored.

| | Tick & Tie | Baseline |
| --- | --- | --- |
| Numeric: correct (within 0.5%) | **48** | 28 |
| Numeric: close (within 2%) | 0 | 2 |
| Numeric: wrong figure stated | **0** | 12 |
| Numeric: answered without a figure | 0 | 6 |
| Narrative: answered | 14 | 20 |
| Narrative: refused | 6 | 0 |
| Should refuse: declined or said not covered | **10 of 10** | 8 of 10 |
| Tricky: forbidden text absent | 3 of 3 | 1 of 3 |
| Median seconds per question | 22.0 | 31.2 |
| 90th percentile seconds | 62.2 | 41.8 |

Tick & Tie rewrote 14 drafts and returned 2 partial answers with failed sentences removed.

## Hand reading of flagged answers (after scoring)

Details: `eval/scores/hand_review.md`. This explains the official numbers above; it does not replace them.
- Of the baseline's 12 wrong figures, 7 were confidently wrong (for example a segment's sales given as Walmart's revenue, long-lived assets given as total assets, discontinued operations given as profit), 4 were hedged answers that named other figures, and 1 came from loose question wording (ExxonMobil "total sales").
- Tricky questions: the baseline's planted-figure answer only disputed "$999 billion", but stated Apple's revenue as "$416,161 billion", a thousand-fold unit error. Its rounding answer did what was asked, so that question measures rule-following rather than accuracy.
- Tick & Tie's 7 refusals of answerable questions (`eval/scores/refusal_reasons.txt`): 3 caused only by a citation-style regression ("...concentration. [P2] This..." read as one claim across two sentences), 1 by the same plus a non-answer, 1 by figures not in the cited evidence (a real catch), 1 by a retrieval miss, and 1 (the planted-figure question) by a real error the Verifier blocked.

## Faithfulness of narrative answers

**The judge failed calibration.** A llama3.2:3b judge, a different model family from the Writer, was measured against 25 hand-labelled sentences with a pass mark fixed before the run (80% agreement and at least 6 of 8 unsupported sentences caught). It agreed on 76% (kappa 0.51), caught 7 of 8 unsupported sentences and raised 5 false alarms: FAIL. Its prompt was not tuned on those labels.

**Plan B: blind hand labels.** Sentences from both systems' narrative answers were sampled (seed 2026), shuffled together with the system hidden, and labelled by hand against their cited evidence, using the same rules as the calibration labels. Only the first 20 of 50 shuffled sentences were labelled, a reduction for time decided before labelling.

| | Supported | 95% interval (Wilson) | Without their own citation |
| --- | --- | --- | --- |
| Tick & Tie | 8 of 10 | 49% to 94% | 1 |
| Baseline | 10 of 10 | 72% to 100% | 6 |

Sentences without their own citation were judged against all the evidence their answer cited, which favours the baseline. One label (S02) was changed from yes to no after a first score, applying the agreed overstatement rule while the system was still hidden; the change lowered Tick & Tie's score. A first attempt at these labels used an external AI model; it was discarded and none of its labels were used.

## What the results support

- The Verifier and the XBRL facts table remove wrong figures: 0 of 48, against 7 confidently wrong for the same model and search without them.
- Plain-code refusal rules work for the cases tested: unknown companies, unreported lines, missing years, advice.
- Verifying figures does not make narrative text more faithful. Sentence meaning is not checked by the Verifier (decision 0014), and the small sample shows no advantage.
- The strictness has a cost in refused narrative questions, and most of that cost traced to one fixable bug.

## Limits

- One model, 12 companies, 81 questions written by the project author, run once each.
- Numeric gold answers share the system's metric and fiscal-year rules; they test whether the pipeline delivers the figure the rules define.
- Faithfulness rests on 20 sentences labelled by the project author: wide intervals, and not an independent labeller.
- Timings come from one Windows laptop running the models locally.
- The citation-style bug is fixed after this evaluation; any later run on this set is a development-set check, not a fresh result.