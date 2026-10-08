"""Task 2, step 1: resolve each ticker to its CIK(s) and cache its SEC metadata and XBRL facts."""
from tickandtie import config
from tickandtie.ingest.edgar_client import EdgarClient


def main():
    client = EdgarClient()
    print(f"{'ticker':<6} {'FY end':<6} {'10-Ks':>5} {'latest 10-K':<11} {'concepts':>8}  CIKs")
    for ticker in config.COMPANIES:
        ciks = [client.ticker_to_cik(ticker)] + config.PREDECESSOR_CIKS.get(ticker, [])
        fy_end = str(client.submissions(ciks[0]).get("fiscalYearEnd") or "?")
        tenk_dates = [row["filingDate"] for cik in ciks
                      for row in client.filings(cik) if row["form"] == "10-K"]
        concepts = max(len(client.company_facts(cik).get("facts", {}).get("us-gaap", {}))
                       for cik in ciks)
        latest = max(tenk_dates) if tenk_dates else "none"
        print(f"{ticker:<6} {fy_end:<6} {len(tenk_dates):>5} {latest:<11} {concepts:>8}  {' + '.join(ciks)}")


if __name__ == "__main__":
    main()