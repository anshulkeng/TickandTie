"""Flatten SEC XBRL company facts into one DuckDB table the Numbers agent can query."""
from datetime import date

import duckdb
import pandas as pd

from tickandtie import config

DB_PATH = config.DATA_DIR / "facts.duckdb"
KEEP_FORMS = {"10-K", "10-K/A"}

COLUMNS = ["ticker", "cik", "taxonomy", "concept", "label", "unit", "period_start",
           "period_end", "duration_days", "value", "accession", "filing_fy",
           "filing_fp", "form", "filed", "frame"]

CREATE = """
CREATE TABLE facts (
    ticker VARCHAR, cik VARCHAR, taxonomy VARCHAR, concept VARCHAR, label VARCHAR,
    unit VARCHAR, period_start DATE, period_end DATE, duration_days INTEGER,
    value DOUBLE, accession VARCHAR, filing_fy INTEGER, filing_fp VARCHAR,
    form VARCHAR, filed DATE, frame VARCHAR
)
"""

INSERT = """
INSERT INTO facts
SELECT ticker, cik, taxonomy, concept, label, unit,
       CAST(period_start AS DATE), CAST(period_end AS DATE), duration_days,
       value, accession, filing_fy, filing_fp, form, CAST(filed AS DATE), frame
FROM incoming
"""


def flatten(ticker, cik, company_facts):
    """One row per value reported in an annual filing.

    The SEC's 'fy' field is the fiscal year of the filing that reported a value, not
    the year the value belongs to: a FY2025 10-K also reports FY2024 and FY2023 revenue,
    all tagged fy=2025. So it is kept as filing_fy, and the period dates decide the year.
    """
    rows = []
    for taxonomy, concepts in company_facts.get("facts", {}).items():
        for concept, body in concepts.items():
            for unit, entries in body.get("units", {}).items():
                for entry in entries:
                    if entry.get("form") not in KEEP_FORMS:
                        continue
                    try:
                        value = float(entry["val"])
                    except (TypeError, ValueError):
                        continue
                    start, end = entry.get("start"), entry["end"]
                    duration = ((date.fromisoformat(end) - date.fromisoformat(start)).days
                                if start else None)
                    rows.append((ticker, cik, taxonomy, concept, body.get("label"), unit,
                                 start, end, duration, value, entry.get("accn"),
                                 entry.get("fy"), entry.get("fp"), entry.get("form"),
                                 entry.get("filed"), entry.get("frame")))
    return rows


def load(rows):
    """Replace the facts table with these rows and return how many were loaded."""
    incoming = pd.DataFrame(rows, columns=COLUMNS)
    incoming["duration_days"] = incoming["duration_days"].astype("Int64")
    incoming["filing_fy"] = incoming["filing_fy"].astype("Int64")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(DB_PATH)) as con:
        con.execute("DROP TABLE IF EXISTS facts")
        con.execute(CREATE)
        con.register("incoming", incoming)
        con.execute(INSERT)
        return con.execute("SELECT count(*) FROM facts").fetchone()[0]