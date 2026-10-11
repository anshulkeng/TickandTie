# Tick & Tie

![tests](https://github.com/anshulkeng/TickandTie/actions/workflows/tests.yml/badge.svg)

Answers questions about US public companies' 10-K filings. Every number is checked against the SEC's own XBRL data before it is shown, and every claim cites the filing and section it came from.

Work in progress.
## Results

Evaluated against a plain RAG baseline using the same model (qwen2.5:7b) and the same search, on 81 questions frozen before either system ran. Full method, numbers and limits: [eval/RESULTS.md](eval/RESULTS.md).

| | Tick & Tie | Plain RAG |
| --- | --- | --- |
| Numeric questions answered with the correct figure | **48 of 48** | 28 of 48 |
| Wrong figures stated (pre-set rule; 7 confidently wrong on hand reading) | **0** | 12 |
| Questions it should decline, declined | **10 of 10** | 8 of 10 |
| Answerable narrative questions refused | 6 of 20 | 0 of 20 |
| Narrative sentences supported by their evidence (blind hand labels) | 8 of 10 | 10 of 10 |

Verifying every figure removes wrong numbers; it does not make narrative text more faithful, and its strictness costs some refusals, most of which traced to one citation-style bug. An AI judge was tried for faithfulness and failed a calibration fixed in advance, so faithfulness was hand-labelled.