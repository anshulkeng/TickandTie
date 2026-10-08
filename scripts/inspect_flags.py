"""Look inside the flagged 10-K sections before deciding how to fix them."""
from edgar import find, set_identity

from tickandtie import config

set_identity(config.EDGAR_IDENTITY)

CASES = [
    ("NVDA", "0001045810-26-000021", ["Item 8", "Item 15"]),
    ("WMT", "0000104169-24-000056", ["Item 8"]),
    ("XOM", "0000034088-24-000018", ["Item 7", "Item 8"]),
]

for ticker, accession, items in CASES:
    tenk = find(accession).obj()
    print(f"\n===== {ticker} {accession} | items found: {tenk.items}")
    for item in items:
        text = (tenk[item] or "").replace("\xa0", " ")
        print(f"\n--- {item}: {len(text)} chars | START:")
        print(text[:400])
        if len(text) > 800:
            print("--- END:")
            print(text[-300:])