# 0009: Paragraph-aware chunks of about 1,200 characters, pointers skipped

Status: Accepted, October 2026

## Context
The embedding model (bge-small) reads at most 512 tokens and silently drops anything after that. Answers quote chunks as citations, so a chunk should read like a real passage. Some Items are only pointers such as "see Item 7".

## Decision
- Aim for about 1,200 characters per chunk and never exceed 1,600.
- Split at paragraphs first, then sentences. Hard-cut only text with no sentence ends, which in practice means number tables.
- Skip Items under 1,000 characters, so a pointer is never cited as evidence.
- Give every chunk an id of ticker, period end, Item and position, so a citation can always be traced back.

## Alternatives considered
- Fixed-size windows with overlap: simpler, but they cut sentences in half and make worse citations.
- Whole paragraphs regardless of length: some paragraphs run past the model's limit and would be truncated.
- Larger chunks of about 3,000 characters: the model would drop the second half.

## Consequences
- 17 pointer Items are skipped (the Item 7A pointers plus XOM fiscal 2023 Items 7 and 8).
- Chunks do not overlap, so an answer that straddles a boundary may need two chunks. Returning several results per question covers this.
- The size is revisited only if the retrieval check in Task 3c shows a problem.