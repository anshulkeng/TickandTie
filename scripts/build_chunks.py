"""Task 3, step 1: cut every saved 10-K into chunks and write them to data/chunks.jsonl."""
import json
import random
from collections import defaultdict
from statistics import mean

from tickandtie import config
from tickandtie.index.chunker import MAX_CHARS, chunk_filing

FILINGS_DIR = config.DATA_DIR / "filings"
CHUNKS_PATH = config.DATA_DIR / "chunks.jsonl"


def main():
    paths = sorted(FILINGS_DIR.glob("*/*.json"))
    all_chunks, skipped = [], []
    for path in paths:
        record = json.loads(path.read_text(encoding="utf-8"))
        chunks, skipped_items = chunk_filing(record)
        all_chunks += chunks
        skipped += [f"{record['ticker']} {record['period_end']} {item}" for item in skipped_items]

    ids = [chunk["chunk_id"] for chunk in all_chunks]
    assert len(ids) == len(set(ids)), "duplicate chunk ids"
    with CHUNKS_PATH.open("w", encoding="utf-8") as out:
        for chunk in all_chunks:
            out.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    sizes = defaultdict(list)
    for chunk in all_chunks:
        sizes[chunk["item"]].append(len(chunk["text"]))
    print(f"{len(all_chunks)} chunks from {len(paths)} filings -> {CHUNKS_PATH}")
    print(f"{'item':<8} {'chunks':>7} {'avg chars':>10} {'max chars':>10}")
    for item in sorted(sizes):
        print(f"{item:<8} {len(sizes[item]):>7} {mean(sizes[item]):>10.0f} {max(sizes[item]):>10}")
    over = [chunk["chunk_id"] for chunk in all_chunks if len(chunk["text"]) > MAX_CHARS]
    print(f"chunks over {MAX_CHARS} chars: {len(over)}")
    print(f"skipped pointer Items ({len(skipped)}): {', '.join(skipped)}")

    pool = [c for c in all_chunks if c["ticker"] == "AAPL" and c["item"] == "Item 1A"]
    sample = random.Random(7).choice(pool)
    print(f"\nSample chunk {sample['chunk_id']}:\n{sample['text']}")


if __name__ == "__main__":
    main()