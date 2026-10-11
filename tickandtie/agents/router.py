"""Router: work out which companies, years and metrics a question is about, and whether it needs report text.

Companies, years and metrics are found with plain rules, because they must be exact. The language
model makes one small, structured decision: whether text is needed and which 10-K sections to
search (decision 0013).
"""
import re
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel

from tickandtie import config

SECTIONS = ("Item 1", "Item 1A", "Item 7", "Item 7A", "Item 8")
DEFAULT_SECTIONS = ["Item 1", "Item 1A", "Item 7"]

ALIASES = {
    "AAPL": ["Apple"],
    "MSFT": ["Microsoft"],
    "NVDA": ["NVIDIA"],
    "WMT": ["Walmart", "Wal-Mart"],
    "COST": ["Costco"],
    "JPM": ["JPMorgan Chase", "JPMorgan", "JP Morgan", "J.P. Morgan"],
    "JNJ": ["Johnson & Johnson", "Johnson and Johnson", "J&J"],
    "PFE": ["Pfizer"],
    "XOM": ["ExxonMobil", "Exxon Mobil", "Exxon"],
    "CAT": ["Caterpillar"],
    "KO": ["Coca-Cola", "Coca Cola", "Coke"],
    "VZ": ["Verizon"],
}

FULL_YEAR = re.compile(r"(?<!\d)((?:19|20)\d{2})(?!\d)")
SHORT_FY = re.compile(r"\bFY\s?'?(\d{2})(?!\d)", re.IGNORECASE)

# (phrase, metric). Longer phrases are matched first and then blanked out, so
# "earnings per share" is never also read as "earnings".
METRIC_PHRASES = [
    ("diluted earnings per share", "eps_diluted"), ("earnings per share", "eps_diluted"),
    ("diluted eps", "eps_diluted"), ("eps", "eps_diluted"),
    ("cash provided by operating activities", "operating_cash_flow"),
    ("cash from operating activities", "operating_cash_flow"),
    ("cash flow from operations", "operating_cash_flow"), ("cash from operations", "operating_cash_flow"),
    ("operating cash flow", "operating_cash_flow"), ("cash and cash equivalents", "cash"),
    ("capital expenditures", "capex"), ("capital expenditure", "capex"),
    ("capital spending", "capex"), ("capex", "capex"),
    ("research and development", "rnd"), ("r&d", "rnd"),
    ("operating income", "operating_income"), ("operating profit", "operating_income"),
    ("net income", "net_income"), ("net profit", "net_income"), ("net earnings", "net_income"),
    ("total liabilities", "total_liabilities"), ("total assets", "total_assets"),
    ("long-term debt", "long_term_debt"), ("long term debt", "long_term_debt"),
    ("shareholders' equity", "equity"), ("stockholders' equity", "equity"),
    ("shareholders equity", "equity"), ("stockholders equity", "equity"),
    ("net sales", "revenue"), ("top line", "revenue"), ("revenues", "revenue"), ("revenue", "revenue"),
    ("turnover", "revenue"), ("sales", "revenue"),
    ("profit", "net_income"), ("earnings", "net_income"),
    ("liabilities", "total_liabilities"), ("assets", "total_assets"), ("debt", "long_term_debt"),
    ("equity", "equity"), ("cash", "cash"),
]

# Words that mean the answer needs explanation, not just a figure. "How much" and "how many" do not count.
EXPLAINS = re.compile(
    r"\b(why|explain\w*|describe\w*|discuss\w*|reasons?|risks?|strateg\w*|compet\w*|outlook|plans?|says?|said)\b"
    r"|\bhow\b(?!\s+(?:much|many)\b)",
    re.IGNORECASE,
)

# Tick & Tie reports what companies filed; it never says whether to trade their shares. Narrow on
# purpose, so questions such as "How much did Apple invest in R&D?" are still answered.
ADVICE = re.compile(
    r"\bshould\s+(?:i|we|you|one)\s+(?:buy|sell|hold|short|invest)\b"
    r"|\b(?:good|bad|smart|safe)\s+(?:investment|stock|buy)\b"
    r"|\bworth\s+(?:buying|investing|owning)\b"
    r"|\b(?:buy|sell)\s+or\s+(?:sell|hold|buy)\b"
    r"|\bprice\s+target\b",
    re.IGNORECASE,
)
ADVICE_REFUSAL = ("I don't give investment advice. I can tell you what a company reported, such as its revenue "
                  "or the risks it describes, but not whether to buy, sell or hold its shares.")

ROUTER_PROMPT = """You route questions about US companies' annual reports (Form 10-K).
Decide two things:
1. needs_text: true if answering needs passages of report text (reasons, explanations, risks, strategy, descriptions); false if reported figures alone answer it.
2. sections: the 10-K sections most likely to hold the answer, chosen only from:
- Item 1: Business (what the company does, products, customers, competition, employees)
- Item 1A: Risk Factors
- Item 7: Management's Discussion and Analysis (results, reasons for changes, liquidity, outlook)
- Item 7A: Market Risk (interest rates, currencies, commodity prices)
- Item 8: Financial Statements and notes (accounting policies, segments, debt terms, litigation, taxes)
Reply with JSON only."""


class RouteDecision(BaseModel):
    needs_text: bool
    sections: list[Literal["Item 1", "Item 1A", "Item 7", "Item 7A", "Item 8"]]


@dataclass
class Plan:
    question: str
    tickers: list
    fiscal_years: list  # empty means the latest fiscal year
    metrics: list
    needs_numbers: bool
    needs_text: bool
    sections: list
    refusal: str = None
    notes: list = field(default_factory=list)


def find_companies(question):
    """Covered companies in the order they are first mentioned."""
    found = []
    for ticker, aliases in ALIASES.items():
        positions = [m.start() for alias in aliases
                     for m in re.finditer(rf"(?<![\w&.]){re.escape(alias)}(?![\w&])", question, re.IGNORECASE)]
        positions += [m.start() for m in re.finditer(rf"(?<![A-Za-z]){ticker}(?![A-Za-z])", question)]
        if positions:
            found.append((min(positions), ticker))
    return [ticker for _, ticker in sorted(found)]


def find_years(question):
    years = {int(year) for year in FULL_YEAR.findall(question)}
    years |= {2000 + int(year) for year in SHORT_FY.findall(question)}
    return sorted(years)


def find_metrics(question):
    text = question.lower().replace("\u2019", "'")
    found = []
    for phrase, metric in sorted(METRIC_PHRASES, key=lambda pair: -len(pair[0])):
        for match in re.finditer(rf"(?<![a-z&]){re.escape(phrase)}(?![a-z])", text):
            text = text[:match.start()] + " " * len(phrase) + text[match.end():]
            if metric not in found:
                found.append(metric)
    return found


def ask_model(question):
    """One structured call: does the question need text, and which sections? Returns (decision, error)."""
    import ollama
    try:
        response = ollama.chat(
            model=config.LLM_MODEL,
            messages=[{"role": "system", "content": ROUTER_PROMPT}, {"role": "user", "content": question}],
            format=RouteDecision.model_json_schema(),
            options={"temperature": 0, "seed": 7},
        )
        return RouteDecision.model_validate_json(response["message"]["content"]), None
    except Exception as exc:  # a bad model reply must never crash routing; the caller falls back
        return None, repr(exc)


def route(question, decide=None):
    decide = decide or ask_model
    if ADVICE.search(question):
        return Plan(question, [], [], [], False, False, [], refusal=ADVICE_REFUSAL)
    tickers = find_companies(question)
    years = find_years(question)
    metrics = find_metrics(question)
    if not tickers:
        covered = ", ".join(config.COMPANY_NAMES[ticker] for ticker in config.COMPANIES)
        return Plan(question, [], years, metrics, False, False, [],
                    refusal=f"I can only answer questions about these companies: {covered}.")
    decision, error = decide(question)
    notes = [] if decision else [f"routing model failed ({error}); used the default sections"]
    needs_text = (not metrics) or bool(EXPLAINS.search(question)) or bool(decision and decision.needs_text)
    chosen = [section for section in SECTIONS if decision and section in decision.sections]
    sections = (chosen or DEFAULT_SECTIONS) if needs_text else []
    return Plan(question, tickers, years, metrics, bool(metrics), needs_text, sections, notes=notes)