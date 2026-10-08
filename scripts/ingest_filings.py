"""Task 2, step 2: download the latest 10-Ks for every company and save their key Items."""
import json
from statistics import median

from tickandtie import config
from tickandtie.ingest.edgar_client import EdgarClient
from tickandtie.ingest.sections import CROSS_REF_CHARS, KEEP_ITEMS, extract_items, latest_10ks

OUT_DIR = config.DATA_DIR / "filings"
SCHEMA = 2
# An Item far smaller than the same company's other years usually means the split stopped early.
SMALL_VS_PEERS = 0.4


def record_path(ticker, period_end, accession):
    return OUT_DIR / ticker / f"{period_end}_{accession}.json"


def load_or_extract(ticker, row):
    path = record_path(ticker, row["reportDate"], row["accessionNumber"])
    if path.exists():
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("schema") == SCHEMA:
            return record
    items, sources, sizes = extract_items(row["accessionNumber"])
    return {
        "schema": SCHEMA,
        "ticker": ticker,
        "cik": row["cik"],
        "accession": row["accessionNumber"],
        "form": row["form"],
        "filing_date": row["filingDate"],
        "period_end": row["reportDate"],
        "items": items,
        "sources": sources,
        "all_item_sizes": sizes,
    }


def warnings_for(record, peers):
    notes = []
    for item in KEEP_ITEMS:
        size = len(record["items"][item])
        typical = median(len(peer["items"][item]) for peer in peers)
        if record["sources"][item] != item:
            notes.append(f"{item} taken from {record['sources'][item]}")
        if size < CROSS_REF_CHARS:
            notes.append(f"{item} is a cross-reference ({size} chars)")
        elif typical and size < SMALL_VS_PEERS * typical:
            notes.append(f"{item} is {size / typical:.0%} of this company's usual size")
    return notes


def main():
    client = EdgarClient()
    header = " ".join(f"{item.replace('Item ', ''):>7}" for item in KEEP_ITEMS)
    print(f"{'ticker':<6} {'period':<10} {header}")
    all_notes = []
    for ticker in config.COMPANIES:
        records = []
        for row in latest_10ks(client, ticker, config.YEARS_PER_COMPANY):
            try:
                records.append(load_or_extract(ticker, row))
            except Exception as exc:
                all_notes.append(f"{ticker} {row['reportDate']}: ERROR {exc!r}")
        for record in records:
            record["warnings"] = warnings_for(record, records)
            path = record_path(ticker, record["period_end"], record["accession"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
            cells = " ".join(f"{len(record['items'][item]):>7}" for item in KEEP_ITEMS)
            print(f"{ticker:<6} {record['period_end']:<10} {cells}")
            all_notes += [f"{ticker} {record['period_end']}: {note}" for note in record["warnings"]]
            if any("usual size" in note for note in record["warnings"]):
                largest = sorted(record["all_item_sizes"].items(), key=lambda kv: kv[1], reverse=True)[:4]
                all_notes.append(f"{ticker} {record['period_end']}: largest Items were {largest}")
    print("\nWarnings:")
    for note in all_notes:
        print(" -", note)


if __name__ == "__main__":
    main()