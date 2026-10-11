"""Numbers agent: look up reported figures in the XBRL facts table and do the arithmetic in Python.

The language model never produces a number (decision 0002). Everything here is plain code.
"""
from dataclasses import dataclass, field

import duckdb

from tickandtie.ingest.xbrl_facts import DB_PATH

ANNUAL = "duration_days BETWEEN 350 AND 380"


@dataclass(frozen=True)
class Metric:
    label: str
    kind: str  # "duration": flows over the year; "instant": balance on the last day of the year
    unit: str
    concepts: tuple  # SEC concepts in order of preference (decision 0012)


METRICS = {
    "revenue": Metric("Revenue", "duration", "USD",
                      ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet")),
    # Caterpillar reports "profit" under the two fallbacks rather than NetIncomeLoss.
    "net_income": Metric("Net income", "duration", "USD",
                         ("NetIncomeLoss", "NetIncomeLossAvailableToCommonStockholdersBasic", "ProfitLoss")),
    "operating_income": Metric("Operating income", "duration", "USD", ("OperatingIncomeLoss",)),
    "eps_diluted": Metric("Diluted earnings per share", "duration", "USD/shares", ("EarningsPerShareDiluted",)),
    "operating_cash_flow": Metric("Cash from operating activities", "duration", "USD",
                                  ("NetCashProvidedByUsedInOperatingActivities",)),
    # Verizon reports capital expenditure as payments for "other productive assets".
    "capex": Metric("Capital spending", "duration", "USD",
                    ("PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets",
                     "PaymentsToAcquireOtherProductiveAssets")),
    "rnd": Metric("Research and development expense", "duration", "USD",
                  ("ResearchAndDevelopmentExpense", "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost")),
    "total_assets": Metric("Total assets", "instant", "USD", ("Assets",)),
    "total_liabilities": Metric("Total liabilities", "instant", "USD", ("Liabilities",)),
    "cash": Metric("Cash and cash equivalents", "instant", "USD", ("CashAndCashEquivalentsAtCarryingValue",)),
    # Prefer debt excluding the part due within a year. Banks such as JPMorgan only report
    # the total including it, so that comes last.
    "long_term_debt": Metric("Long-term debt", "instant", "USD",
                             ("LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations", "LongTermDebt",
                              "LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities")),
    "equity": Metric("Shareholders' equity", "instant", "USD",
                     ("StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest")),
}

# A bank's meaningful revenue is net of interest expense, so it goes first for JPMorgan.
CONCEPT_OVERRIDES = {("JPM", "revenue"): ("RevenuesNetOfInterestExpense", "Revenues")}


@dataclass
class Fact:
    ticker: str
    metric: str
    label: str
    concept: str
    value: float
    unit: str
    fiscal_year: int
    period_start: object  # None for balance-sheet values
    period_end: object
    accession: str
    filed: object
    alternates: list = field(default_factory=list)

    @property
    def display(self):
        return format_value(self.value, self.unit)


def connect():
    return duckdb.connect(str(DB_PATH), read_only=True)


def fiscal_years(con, ticker):
    """Map each fiscal year, as the company labels it, to the date that year ended.

    A 10-K's fiscal year (filing_fy) names its own latest annual period, so the label
    is the company's, not a calendar guess (decision 0011)."""
    rows = con.execute(f"""
        SELECT filing_fy, max(period_end)
        FROM facts
        WHERE ticker = ? AND form = '10-K' AND filing_fp = 'FY' AND taxonomy = 'us-gaap' AND {ANNUAL}
        GROUP BY filing_fy""", [ticker]).fetchall()
    return {fiscal_year: year_end for fiscal_year, year_end in rows if fiscal_year is not None}


def lookup(con, ticker, metric_key, fiscal_year):
    """The reported value of one metric for one company and fiscal year, or None if not reported."""
    metric = METRICS[metric_key]
    year_end = fiscal_years(con, ticker).get(fiscal_year)
    if year_end is None:
        return None
    concepts = CONCEPT_OVERRIDES.get((ticker, metric_key), metric.concepts)
    period_rule = ANNUAL if metric.kind == "duration" else "period_start IS NULL"
    found = []
    for concept in concepts:
        row = con.execute(f"""
            SELECT value, period_start, accession, filed
            FROM facts
            WHERE ticker = ? AND taxonomy = 'us-gaap' AND concept = ? AND unit = ?
              AND period_end = ? AND {period_rule}
            ORDER BY filed DESC, accession DESC
            LIMIT 1""", [ticker, concept, metric.unit, year_end]).fetchone()
        if row:
            value, period_start, accession, filed = row
            found.append(Fact(ticker, metric_key, metric.label, concept, value, metric.unit,
                              fiscal_year, period_start, year_end, accession, filed))
    if not found:
        return None
    primary = found[0]
    primary.alternates = found[1:]
    return primary


def format_value(value, unit):
    """The exact text the Writer must copy. Money in millions, per-share amounts in dollars and cents."""
    sign = "-" if value < 0 else ""
    amount = abs(value)
    if unit == "USD/shares":
        return f"{sign}${amount:,.2f} per share"
    if amount >= 1_000_000:
        return f"{sign}${amount / 1_000_000:,.0f} million"
    return f"{sign}${amount:,.0f}"


def change(current, previous):
    """Difference and percentage change, computed here so the model never does arithmetic."""
    difference = current - previous
    percent = None if previous == 0 else round(difference / abs(previous) * 100, 1)
    return {"difference": difference, "percent": percent}