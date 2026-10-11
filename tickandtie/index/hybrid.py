"""Hybrid search: combine the meaning and word rankings with reciprocal rank fusion."""
from tickandtie.index.search_indexes import (BM25Index, load_chunks, load_embedder,
                                             open_vector_index, vector_search)

RRF_K = 60  # standard constant from the original RRF paper; it softens the pull of rank 1


def reciprocal_rank_fusion(rankings, k=RRF_K):
    """Merge ranked lists of ids. Each list adds 1 / (k + rank) for every id it contains.
    Ties are broken by id so the result is the same on every run."""
    scores = {}
    for ranking in rankings:
        for rank, item_id in enumerate(ranking, start=1):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores, key=lambda item_id: (-scores[item_id], item_id))


class HybridSearcher:
    def __init__(self, chunks=None, model=None, collection=None):
        self.chunks = load_chunks() if chunks is None else chunks
        self.by_id = {chunk["chunk_id"]: chunk for chunk in self.chunks}
        self.model = load_embedder() if model is None else model
        self.collection = open_vector_index() if collection is None else collection
        self.bm25 = BM25Index(self.chunks)

    def rankings(self, question, pool=30, **filters):
        return {
            "meaning": vector_search(self.collection, self.model, question, k=pool, **filters),
            "words": self.bm25.search(question, k=pool, **filters),
        }

    def search(self, question, k=8, pool=30, **filters):
        ranked = self.rankings(question, pool, **filters)
        ids = reciprocal_rank_fusion([ranked["meaning"], ranked["words"]])[:k]
        return [self.by_id[chunk_id] for chunk_id in ids]