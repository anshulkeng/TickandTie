"""List the SEC concepts a company used for one period, to fix metric lookups from evidence.

Usage: python -m scripts.find_concepts CAT 2025-12-31 profit netincome
"""
import sys

from tickandtie.agents.numbers import connect


def main():
    ticker, period_end, *words = sys.argv[1:]
    match = " OR ".join("concept ILIKE ?" for _ in words)
    with connect() as con:
        table = con.execute(f"""
            SELECT taxonomy, concept, unit,
                   CASE WHEN period_start IS NULL THEN 'year end' ELSE 'full year' END AS kind,
                   round(value / 1e6, 1) AS usd_millions, label
            FROM facts
            WHERE ticker = ? AND period_end = ? AND ({match})
              AND (period_start IS NULL OR duration_days BETWEEN 350 AND 380)
            QUALIFY row_number() OVER (PARTITION BY taxonomy, concept, unit, kind ORDER BY filed DESC) = 1
            ORDER BY taxonomy, concept""", [ticker, period_end, *[f"%{word}%" for word in words]]).df()
    print(table.to_string(index=False) if len(table) else "No matching concepts.")


if __name__ == "__main__":
    main()