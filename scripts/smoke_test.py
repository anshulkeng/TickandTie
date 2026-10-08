"""Checks every external piece Tick & Tie depends on before I write any real code."""
import os
import sys
import time

import httpx
from dotenv import load_dotenv

load_dotenv()
UA = os.getenv("EDGAR_IDENTITY", "")
AAPL = "0000320193"
all_ok = True


def check(name, fn):
    global all_ok
    start = time.perf_counter()
    try:
        detail = fn()
        print(f"[PASS] {name} ({time.perf_counter() - start:.1f}s) {detail}")
    except Exception as exc:
        all_ok = False
        print(f"[FAIL] {name}: {exc!r}")


def env_loaded():
    assert "@" in UA, "EDGAR_IDENTITY missing or has no email"
    return UA


def sec_submissions():
    r = httpx.get(f"https://data.sec.gov/submissions/CIK{AAPL}.json",
                  headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    return r.json()["name"]


def sec_xbrl_facts():
    r = httpx.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{AAPL}.json",
                  headers={"User-Agent": UA}, timeout=60)
    r.raise_for_status()
    return f"{len(r.json()['facts']['us-gaap'])} us-gaap concepts"


def edgartools_filing():
    from edgar import Company
    filing = Company("AAPL").get_filings(form="10-K").latest()
    return f"{filing.form} filed {filing.filing_date}"


def ollama_chat():
    import ollama
    out = ollama.chat(model=os.getenv("LLM_MODEL"),
                      messages=[{"role": "user", "content": "Reply with one word: ready"}],
                      options={"temperature": 0})
    return out["message"]["content"].strip()[:40]


def embeddings():
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(os.getenv("EMBED_MODEL"))
    return f"dim={model.encode(['test']).shape[1]}"


for name, fn in [("env", env_loaded), ("SEC submissions", sec_submissions),
                 ("SEC XBRL facts", sec_xbrl_facts), ("edgartools", edgartools_filing),
                 ("Ollama", ollama_chat), ("embeddings", embeddings)]:
    check(name, fn)

sys.exit(0 if all_ok else 1)