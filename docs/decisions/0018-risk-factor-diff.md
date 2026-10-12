# 0018: The risk-factor diff is plain code with exact quotes

Status: Accepted, October 2026

## Context
Users want to know how a company's risk factors (Item 1A) changed from one annual report to the next. A model summary could invent or leave out changes, and nothing could check it. Filing text is also messy: the same text can be split into paragraphs differently from year to year, and some paragraphs break mid-sentence.

## Decision
- No language model. Two years of Item 1A are compared in plain code.
- Changes are found at sentence level across the whole Item: a sentence is new only if it appears nowhere in the older filing, and removed only if it appears nowhere in the newer one. Text that only moved is not reported.
- A block starting with a lowercase letter is joined to the paragraph before it; fragments under 4 words are ignored.
- An added and a removed sentence at least 60% similar are shown as one edit, word by word. Paragraphs are matched (50% similarity) only to group changes for display.
- The answer is built by code: both filings with their period ends and filing numbers, the counts, then up to 5 new, 5 removed and 5 reworded sentences (largest changes first). Every quote is exact.
- The Router sends a question here only if it pairs "changed", "compare" or "differ" with "risk factors", or "new", "added", "removed" or "dropped" with "risks". One company at a time; the latest filing is compared with the one before unless years are asked for, and a year without a report is refused.

## How it was checked
Ten reported items were drawn at random (seed 2026) from five companies not looked at while building (Microsoft, Walmart, JPMorgan, Coca-Cola, Caterpillar), with a pass mark of 8 fixed before drawing. The author labelled all 10 as real differences between the filings (95% interval roughly 72% to 100%). The first version matched whole paragraphs and reported text that had only been split differently; it was replaced before the check.

## Alternatives considered
- A model-written summary: easier to read, but not verifiable.
- Paragraph-level matching only: reported regrouped text as new and removed.
- Embedding similarity for matching: not needed so far; kept in reserve if missed links matter.

## Consequences
- The check measures precision, not recall. A heavily rewritten sentence (under 60% similar) appears as one removed and one added sentence rather than an edit.
- Answers can be long: a year can bring well over 100 changed sentences, so the answer shows the first 5 of each kind and says how many more there are.
- The sentence splitter can split at abbreviations; it does so the same way in both years, so this does not create false changes.