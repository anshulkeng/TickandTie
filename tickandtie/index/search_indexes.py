"""The two search indexes over 10-K chunks: meaning (embeddings in ChromaDB) and words (BM25)."""
import json
import re

import chromadb
from rank_bm25 import BM25Okapi

from tickandtie import config

CHUNKS_PATH = config.DATA_DIR / "chunks.jsonl"
CHROMA_DIR = config.DATA_DIR / "chroma"
COLLECTION = "chunks"

# bge v1.5 models are trained to expect this prefix on short search queries, not on passages.
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

ITEM_TITLES = {
    "Item 1": "Business",
    "Item 1A": "Risk Factors",
    "Item 7": "Management's Discussion and Analysis",
    "Item 7A": "Market Risk",
    "Item 8": "Financial Statements",
}
WORD = re.compile(r"[a-z0-9]+")
METADATA_KEYS = ("ticker", "period_end", "item", "accession", "source_item")


def load_chunks(path=CHUNKS_PATH):
    with open(path, encoding="utf-8") as lines:
        return [json.loads(line) for line in lines]


def header(chunk):
    """Context line put in front of a chunk, because most chunks never name their company or section."""
    name = config.COMPANY_NAMES.get(chunk["ticker"], chunk["ticker"])
    title = ITEM_TITLES.get(chunk["item"], "")
    return f"{name} ({chunk['ticker']}) 10-K, period ending {chunk['period_end']}, {chunk['item']} {title}".strip()


def indexed_text(chunk):
    return f"{header(chunk)}\n\n{chunk['text']}"


def tokenize(text):
    return WORD.findall(text.lower())


def where_filter(ticker=None, period_end=None, items=None):
    """Chroma metadata filter for the optional company, period and Item restrictions."""
    clauses = []
    if ticker:
        clauses.append({"ticker": ticker})
    if period_end:
        clauses.append({"period_end": period_end})
    if items:
        clauses.append({"item": {"$in": list(items)}})
    if not clauses:
        return None
    return clauses[0] if len(clauses) == 1 else {"$and": clauses}


def load_embedder():
    from sentence_transformers import SentenceTransformer  # heavy import, only when needed
    return SentenceTransformer(config.EMBED_MODEL)


def embed_query(model, question):
    return model.encode([QUERY_PREFIX + question], normalize_embeddings=True)[0]


def build_vector_index(chunks, model, batch_size=1000):
    """Rebuild the Chroma collection from scratch. Embeddings are normalised, so Chroma's
    default L2 distance ranks results exactly as cosine similarity would."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass  # first build: there is nothing to delete yet
    collection = client.create_collection(COLLECTION)
    vectors = model.encode([indexed_text(c) for c in chunks], batch_size=64,
                           normalize_embeddings=True, show_progress_bar=True)
    for start in range(0, len(chunks), batch_size):
        part = chunks[start:start + batch_size]
        collection.add(
            ids=[c["chunk_id"] for c in part],
            embeddings=vectors[start:start + batch_size].tolist(),
            documents=[c["text"] for c in part],
            metadatas=[{key: c[key] for key in METADATA_KEYS} for c in part],
        )
    return collection


def open_vector_index():
    return chromadb.PersistentClient(path=str(CHROMA_DIR)).get_collection(COLLECTION)


def vector_search(collection, model, question, k=30, **filters):
    result = collection.query(query_embeddings=[embed_query(model, question).tolist()],
                              n_results=k, where=where_filter(**filters))
    return result["ids"][0]


class BM25Index:
    """Keyword index, rebuilt in memory from the chunks in a few seconds."""

    def __init__(self, chunks):
        self.chunks = chunks
        tokenized = [tokenize(indexed_text(c)) for c in chunks]
        self.token_sets = [set(tokens) for tokens in tokenized]
        self.bm25 = BM25Okapi(tokenized)

    def search(self, question, k=30, ticker=None, period_end=None, items=None):
        """A chunk counts as a match only if it contains at least one of the question's words.
        BM25 scores can go negative for words found in most chunks, so the score's sign
        cannot be used to decide what matched."""
        terms = tokenize(question)
        wanted = set(terms)
        scores = self.bm25.get_scores(terms)
        matches = [i for i, words in enumerate(self.token_sets) if words & wanted]
        hits = []
        for i in sorted(matches, key=lambda i: scores[i], reverse=True):
            chunk = self.chunks[i]
            if ticker and chunk["ticker"] != ticker:
                continue
            if period_end and chunk["period_end"] != period_end:
                continue
            if items and chunk["item"] not in items:
                continue
            hits.append(chunk["chunk_id"])
            if len(hits) == k:
                break
        return hits