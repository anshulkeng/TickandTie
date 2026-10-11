"""Unit tests for the Numbers agent, on a real in-memory DuckDB (never faked, see docs/testing.md)."""
from datetime import date

import duckdb

from tickandtie.agents.numbers import change, fiscal_years, format_value, lookup
from tickandtie.ingest.xbrl_facts import CREATE


def row(ticker, concept, value, start, end, fiscal_year, accession, filed, unit="USD"):
    start_date = date.fromisoformat(start) if start else None
    end_date = date.fromisoformat(end)
    duration = (end_date - start_date).days if start_date else None
    return (ticker, "0000000001", "us-gaap", concept, concept, unit, start_date, end_date, duration,
            float(value), accession, fiscal_year, "FY", "10-K", date.fromisoformat(filed), None)


def database(rows):
    con = duckdb.connect()
    con.execute(CREATE)
    con.executemany("INSERT INTO facts VALUES (" + ", ".join(["?"] * 16) + ")", rows)
    return con


# A Walmart-style company whose fiscal years end on 31 January.
RETAILER = [
    row("WMT", "Revenues", 650e9, "2024-02-01", "2025-01-31", 2025, "fy25", "2025-03-14"),
    row("WMT", "Revenues", 681e9, "2025-02-01", "2026-01-31", 2026, "fy26", "2026-03-13"),
    row("WMT", "Revenues", 651e9, "2024-02-01", "2025-01-31", 2026, "fy26", "2026-03-13"),
    row("WMT", "RevenueFromContractWithCustomerExcludingAssessedTax", 675e9,
        "2025-02-01", "2026-01-31", 2026, "fy26", "2026-03-13"),
    row("WMT", "Assets", 260e9, None, "2026-01-31", 2026, "fy26", "2026-03-13"),
]


def test_fiscal_year_labels_come_from_the_filings():
    con = database(RETAILER)
    assert fiscal_years(con, "WMT") == {2025: date(2025, 1, 31), 2026: date(2026, 1, 31)}


def test_prior_year_value_belongs_to_its_own_year_and_latest_filing_wins():
    con = database(RETAILER)
    fact = lookup(con, "WMT", "revenue", 2025)
    assert fact.value == 651e9          # the restated figure from the later filing
    assert fact.accession == "fy26"
    assert fact.period_end == date(2025, 1, 31)


def test_total_revenue_is_preferred_and_the_other_figure_is_kept():
    fact = lookup(database(RETAILER), "WMT", "revenue", 2026)
    assert fact.concept == "Revenues"
    assert [alt.concept for alt in fact.alternates] == ["RevenueFromContractWithCustomerExcludingAssessedTax"]


def test_bank_revenue_uses_net_revenue():
    con = database([
        row("JPM", "Revenues", 280e9, "2025-01-01", "2025-12-31", 2025, "j25", "2026-02-13"),
        row("JPM", "RevenuesNetOfInterestExpense", 180e9, "2025-01-01", "2025-12-31", 2025, "j25", "2026-02-13"),
    ])
    assert lookup(con, "JPM", "revenue", 2025).concept == "RevenuesNetOfInterestExpense"


def test_balance_sheet_metric_uses_the_year_end_balance():
    fact = lookup(database(RETAILER), "WMT", "total_assets", 2026)
    assert fact.value == 260e9 and fact.period_start is None


def test_unknown_year_or_unreported_metric_returns_none():
    con = database(RETAILER)
    assert lookup(con, "WMT", "revenue", 2019) is None
    assert lookup(con, "WMT", "rnd", 2026) is None


def test_format_value_and_change():
    assert format_value(391_035e6, "USD") == "$391,035 million"
    assert format_value(-1_250e6, "USD") == "-$1,250 million"
    assert format_value(6.08, "USD/shares") == "$6.08 per share"
    assert change(110.0, 100.0) == {"difference": 10.0, "percent": 10.0}
    assert change(5.0, 0.0)["percent"] is None

def test_net_income_falls_back_to_profit_attributable_to_shareholders():
    con = database([
        row("CAT", "NetIncomeLossAvailableToCommonStockholdersBasic", 8_884e6,
            "2025-01-01", "2025-12-31", 2025, "c25", "2026-02-13"),
        row("CAT", "ProfitLoss", 8_882e6, "2025-01-01", "2025-12-31", 2025, "c25", "2026-02-13"),
    ])
    fact = lookup(con, "CAT", "net_income", 2025)
    assert fact.concept == "NetIncomeLossAvailableToCommonStockholdersBasic"
    assert [alt.concept for alt in fact.alternates] == ["ProfitLoss"]


def test_long_term_debt_prefers_the_non_current_figure_and_accepts_bank_totals():
    con = database([
        row("KO", "Revenues", 47e9, "2025-01-01", "2025-12-31", 2025, "k25", "2026-02-20"),
        row("KO", "LongTermDebtAndCapitalLeaseObligations", 42_119e6, None, "2025-12-31", 2025, "k25", "2026-02-20"),
        row("KO", "LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities", 43_941e6,
            None, "2025-12-31", 2025, "k25", "2026-02-20"),
        row("JPM", "Revenues", 180e9, "2025-01-01", "2025-12-31", 2025, "j25", "2026-02-13"),
        row("JPM", "LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities", 435_206e6,
            None, "2025-12-31", 2025, "j25", "2026-02-13"),
    ])
    assert lookup(con, "KO", "long_term_debt", 2025).concept == "LongTermDebtAndCapitalLeaseObligations"
    assert lookup(con, "JPM", "long_term_debt", 2025).value == 435_206e6


def test_capital_spending_falls_back_to_other_productive_assets():
    con = database([
        row("VZ", "PaymentsToAcquireOtherProductiveAssets", 17_011e6,
            "2025-01-01", "2025-12-31", 2025, "v25", "2026-02-17"),
    ])
    assert lookup(con, "VZ", "capex", 2025).value == 17_011e6