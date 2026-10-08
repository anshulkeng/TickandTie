"""Unit tests for flattening XBRL company facts. No network needed."""
from tickandtie.ingest.xbrl_facts import COLUMNS, flatten

SAMPLE = {"facts": {"us-gaap": {
    "Revenues": {"label": "Revenues", "units": {"USD": [
        {"start": "2024-10-01", "end": "2025-09-30", "val": 100, "accn": "a",
         "fy": 2025, "fp": "FY", "form": "10-K", "filed": "2025-11-01"},
        {"start": "2023-10-01", "end": "2024-09-30", "val": 90, "accn": "a",
         "fy": 2025, "fp": "FY", "form": "10-K", "filed": "2025-11-01"},
        {"start": "2025-01-01", "end": "2025-03-31", "val": 25, "accn": "q",
         "fy": 2025, "fp": "Q2", "form": "10-Q", "filed": "2025-05-01"},
    ]}},
    "Assets": {"label": "Assets", "units": {"USD": [
        {"end": "2025-09-30", "val": 500, "accn": "a",
         "fy": 2025, "fp": "FY", "form": "10-K", "filed": "2025-11-01"},
    ]}},
}}}


def rows_as_dicts():
    return [dict(zip(COLUMNS, row)) for row in flatten("TEST", "0000000001", SAMPLE)]


def test_only_annual_filings_are_kept():
    rows = rows_as_dicts()
    assert len(rows) == 3
    assert all(row["form"] == "10-K" for row in rows)


def test_prior_year_value_keeps_its_own_period_not_the_filing_year():
    revenue = {row["period_end"]: row for row in rows_as_dicts() if row["concept"] == "Revenues"}
    prior = revenue["2024-09-30"]
    assert prior["filing_fy"] == 2025
    assert prior["period_start"] == "2023-10-01"
    assert prior["duration_days"] == 365


def test_balance_sheet_value_has_no_duration():
    assets = next(row for row in rows_as_dicts() if row["concept"] == "Assets")
    assert assets["period_start"] is None
    assert assets["duration_days"] is None