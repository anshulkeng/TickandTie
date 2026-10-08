"""Look at how edgartools splits one 10-K before building the full pipeline on it."""
from edgar import find, set_identity

from tickandtie import config
from tickandtie.ingest.edgar_client import EdgarClient

set_identity(config.EDGAR_IDENTITY)
client = EdgarClient()

cik = client.ticker_to_cik("AAPL")
tenks = sorted((row for row in client.filings(cik) if row["form"] == "10-K"),
               key=lambda row: row["filingDate"], reverse=True)
latest = tenks[0]
print("accession:", latest["accessionNumber"], "| filed:", latest["filingDate"],
      "| period:", latest["reportDate"])

tenk = find(latest["accessionNumber"]).obj()
print("object type:", type(tenk).__name__)
print("items found:", tenk.items)
for item in tenk.items:
    text = tenk[item] or ""
    print(f"{item:<10} {len(text):>8} chars | {text[:70]!r}")