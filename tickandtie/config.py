"""Settings loaded once from .env, so every module reads the same values."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = (ROOT / os.getenv("DATA_DIR", "./data")).resolve()

EDGAR_IDENTITY = os.getenv("EDGAR_IDENTITY", "")
SEC_MAX_RPS = float(os.getenv("SEC_MAX_RPS", "5"))

LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "llama3.2:3b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")

# Picked to include awkward cases on purpose: non-December fiscal years
# (AAPL, MSFT, NVDA, WMT, COST, JNJ) and a bank with no plain revenue line (JPM).
COMPANIES = ["AAPL", "MSFT", "NVDA", "WMT", "COST", "JPM",
             "JNJ", "PFE", "XOM", "CAT", "KO", "VZ"]
YEARS_PER_COMPANY = 3

# A ticker can outlive the legal entity behind it. On 1 July 2026 ExxonMobil
# moved under a new Texas parent with a new CIK; its earlier 10-Ks stay under
# the old one, so both are searched.
PREDECESSOR_CIKS = {"XOM": ["0000034088"]}