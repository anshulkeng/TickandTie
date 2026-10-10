"""Task 3, step 2: embed every chunk into ChromaDB, build the word index, and sanity-check both."""
import time

from tickandtie.index.search_indexes import (BM25Index, build_vector_index, load_chunks,
                                             load_embedder, vector_search)

PROBES = [
    ("Which components does Apple rely on single or limited sources for?", {"ticker": "AAPL"}),
    ("How does JPMorgan manage liquidity risk?", {"ticker": "JPM"}),
]


def main():
    chunks = load_chunks()
    by_id = {chunk["chunk_id"]: chunk for chunk in chunks}
    print(f"{len(chunks)} chunks loaded")

    model = load_embedder()
    start = time.perf_counter()
    collection = build_vector_index(chunks, model)
    print(f"Meaning index: {collection.count()} chunks in {time.perf_counter() - start:.0f}s")

    start = time.perf_counter()
    bm25 = BM25Index(chunks)
    print(f"Word index built in {time.perf_counter() - start:.1f}s")

    for question, filters in PROBES:
        print(f"\nQ: {question}  {filters}")
        results = (("meaning", vector_search(collection, model, question, k=3, **filters)),
                   ("words", bm25.search(question, k=3, **filters)))
        for name, ids in results:
            for chunk_id in ids:
                print(f"  {name:<8} {chunk_id}  {by_id[chunk_id]['text'][:80]!r}")


if __name__ == "__main__":
    main()