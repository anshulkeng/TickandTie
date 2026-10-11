"""Show which of the launch metrics each company reports in its latest fiscal year."""
from tickandtie import config
from tickandtie.agents.numbers import METRICS, connect, fiscal_years, lookup


def main():
    with connect() as con:
        names = list(METRICS)
        print(f"{'ticker':<6} {'FY':<6} " + " ".join(f"{name[:9]:>9}" for name in names))
        missing = []
        for ticker in config.COMPANIES:
            year = max(fiscal_years(con, ticker))
            cells = []
            for name in names:
                found = lookup(con, ticker, name, year) is not None
                cells.append(f"{'ok' if found else '--':>9}")
                if not found:
                    missing.append(f"{ticker} FY{year} {name}")
            print(f"{ticker:<6} {year:<6} " + " ".join(cells))
        print(f"\nNot found ({len(missing)}): " + ", ".join(missing))


if __name__ == "__main__":
    main()