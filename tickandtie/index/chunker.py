"""Cut 10-K Items into paragraph-aware chunks small enough for the embedding model."""
import re

from tickandtie.ingest.sections import CROSS_REF_CHARS

# bge-small reads at most 512 tokens. Filing text with numbers and tables runs about
# 4 characters a token, so 1,600 characters keeps a chunk safely under the limit.
TARGET_CHARS = 1200
MAX_CHARS = 1600
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def split_long(paragraph):
    """Break an over-long paragraph at sentence ends, hard-cutting runs with none (tables)."""
    if len(paragraph) <= MAX_CHARS:
        return [paragraph]
    pieces, current = [], ""
    for sentence in SENTENCE_END.split(paragraph):
        while len(sentence) > MAX_CHARS:
            if current:
                pieces.append(current)
                current = ""
            pieces.append(sentence[:MAX_CHARS])
            sentence = sentence[MAX_CHARS:]
        if current and len(current) + 1 + len(sentence) > MAX_CHARS:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}" if current else sentence
    if current:
        pieces.append(current)
    return pieces


def chunk_text(text):
    """Group paragraphs into chunks of about TARGET_CHARS, never more than MAX_CHARS."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    units = [piece for paragraph in paragraphs for piece in split_long(paragraph)]
    chunks, current = [], ""
    for unit in units:
        if current and len(current) + 2 + len(unit) > TARGET_CHARS:
            chunks.append(current)
            current = unit
        else:
            current = f"{current}\n\n{unit}" if current else unit
    if current:
        chunks.append(current)
    return chunks


def chunk_filing(record):
    """All chunks for one saved 10-K record, skipping Items that are only pointers."""
    chunks, skipped = [], []
    for item, text in record["items"].items():
        if len(text) < CROSS_REF_CHARS:
            skipped.append(item)
            continue
        for number, piece in enumerate(chunk_text(text)):
            chunks.append({
                "chunk_id": f"{record['ticker']}|{record['period_end']}|{item}|{number:04d}",
                "ticker": record["ticker"],
                "cik": record["cik"],
                "accession": record["accession"],
                "period_end": record["period_end"],
                "filing_date": record["filing_date"],
                "item": item,
                "source_item": record["sources"][item],
                "text": piece,
            })
    return chunks, skipped