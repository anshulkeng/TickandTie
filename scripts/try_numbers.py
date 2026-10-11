"""Task 4, step 1: exercise the Numbers agent on real data and tie out known figures."""
from tickandtie import config
from tickandtie.agents.numbers import change, connect, fiscal_years, lookup

# Apple's published revenue, USD millions: the same tie-out as Task 2.
TIE_OUTS = [("AAPL", "revenue", 2023, 383_285), ("AAPL", "revenue", 2022, 394_328)]


def main():
    with connect() as con:
        print("Tie-out checks:")
        for ticker, metric, year, expected in TIE_OUTS:
            fact = lookup(con, ticker, metric, year)
            got = round(fact.value / 1e6) if fact else None
            print(f"  {'PASS' if got == expected else 'FAIL'}  {ticker} {metric} FY{year}: got {got}, expected {expected}")

        print("\nLatest three fiscal years, as each company labels them:")
        latest = {}
        for ticker in config.COMPANIES:
            years = sorted(fiscal_years(con, ticker).items(), reverse=True)[:3]
            latest[ticker] = [year for year, _ in years]
            print(f"  {ticker:<5} " + "   ".join(f"FY{year} ends {end}" for year, end in years))

        print("\nRevenue and net income (concept used; other figures found):")
        for ticker in config.COMPANIES:
            for year in latest[ticker]:
                for metric in ("revenue", "net_income"):
                    fact = lookup(con, ticker, metric, year)
                    if fact is None:
                        print(f"  {ticker:<5} FY{year} {metric:<10} NOT FOUND")
                        continue
                    others = "; ".join(f"{a.concept} {a.display}" for a in fact.alternates)
                    print(f"  {ticker:<5} FY{year} {metric:<10} {fact.display:>18}  {fact.concept}"
                          + (f"  | also: {others}" if others else ""))

        current, previous = lookup(con, "AAPL", "revenue", 2025), lookup(con, "AAPL", "revenue", 2024)
        if current and previous:
            growth = change(current.value, previous.value)
            print(f"\nApple revenue FY2025 vs FY2024: {growth['percent']:+.1f}%")


if __name__ == "__main__":
    main()