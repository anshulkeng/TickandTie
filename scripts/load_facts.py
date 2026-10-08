"""Task 2, step 3: load XBRL facts for every company into DuckDB, then run tie-out checks."""
import duckdb

from tickandtie import config
from tickandtie.ingest.edgar_client import EdgarClient
from tickandtie.ingest.xbrl_facts import DB_PATH, flatten, load

ANNUAL = "duration_days BETWEEN 350 AND 380"
REVENUE_CONCEPTS = ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
                    "RevenuesNetOfInterestExpense", "SalesRevenueNet")

CHECKS = {
    "Apple annual revenue, latest filing per year (tie these to the 10-Ks)": f"""
        SELECT period_start, period_end, round(value / 1e6) AS usd_millions, accession, filed
        FROM facts
        WHERE ticker = 'AAPL' AND unit = 'USD' AND {ANNUAL}
          AND concept = 'RevenueFromContractWithCustomerExcludingAssessedTax'
          AND period_end >= DATE '2022-09-01'
        QUALIFY row_number() OVER (PARTITION BY period_end ORDER BY filed DESC) = 1
        ORDER BY period_end DESC""",
    "Why filing_fy is not the year: periods inside each Apple filing": f"""
        SELECT filing_fy, count(DISTINCT period_end) AS periods,
               min(period_end) AS earliest, max(period_end) AS latest
        FROM facts
        WHERE ticker = 'AAPL' AND unit = 'USD' AND {ANNUAL}
          AND concept = 'RevenueFromContractWithCustomerExcludingAssessedTax'
          AND filing_fy >= 2023
        GROUP BY filing_fy ORDER BY filing_fy""",
    "Which revenue concept each company uses (annual, since 2023)": f"""
        SELECT ticker, concept, count(DISTINCT period_end) AS years, max(period_end) AS latest
        FROM facts
        WHERE concept IN {REVENUE_CONCEPTS} AND unit = 'USD' AND {ANNUAL}
          AND period_end >= DATE '2023-01-01'
        GROUP BY ticker, concept ORDER BY ticker, concept""",
}


def main():
    client = EdgarClient()
    rows = []
    for ticker in config.COMPANIES:
        ciks = [client.ticker_to_cik(ticker)] + config.PREDECESSOR_CIKS.get(ticker, [])
        company_rows = [row for cik in ciks
                        for row in flatten(ticker, cik, client.company_facts(cik))]
        print(f"{ticker:<6} {len(company_rows):>8} rows")
        rows += company_rows
    total = load(rows)
    print(f"\nLoaded {total} rows into {DB_PATH}")
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        for title, sql in CHECKS.items():
            print(f"\n== {title}")
            print(con.execute(sql).df().to_string(index=False))


if __name__ == "__main__":
    main()