"""Small SEC EDGAR client: identifies itself, stays under the rate limit, caches to disk."""
import json
import threading
import time

import httpx

from tickandtie import config

CACHE_DIR = config.DATA_DIR / "cache" / "sec"
RETRY_STATUSES = (429, 500, 502, 503, 504)


class EdgarClient:
    def __init__(self, identity=config.EDGAR_IDENTITY, max_rps=config.SEC_MAX_RPS):
        if "@" not in identity:
            raise ValueError("EDGAR_IDENTITY needs a contact email (SEC fair-access rule)")
        self._http = httpx.Client(
            headers={"User-Agent": identity, "Accept-Encoding": "gzip, deflate"},
            timeout=60,
            follow_redirects=True,
        )
        self._min_gap = 1.0 / max_rps
        self._last_request = 0.0
        self._lock = threading.Lock()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _wait_turn(self):
        with self._lock:
            elapsed = time.monotonic() - self._last_request
            if elapsed < self._min_gap:
                time.sleep(self._min_gap - elapsed)
            self._last_request = time.monotonic()

    def _get(self, url, attempts=4):
        for attempt in range(attempts):
            self._wait_turn()
            response = self._http.get(url)
            if response.status_code in RETRY_STATUSES and attempt < attempts - 1:
                time.sleep(2 ** attempt)
                continue
            response.raise_for_status()
            return response

    def get_json(self, url, cache_name, refresh=False):
        path = CACHE_DIR / cache_name
        if path.exists() and not refresh:
            return json.loads(path.read_text(encoding="utf-8"))
        data = self._get(url).json()
        path.write_text(json.dumps(data), encoding="utf-8")
        return data

    def ticker_to_cik(self, ticker):
        rows = self.get_json("https://www.sec.gov/files/company_tickers.json", "company_tickers.json")
        for row in rows.values():
            if row["ticker"].upper() == ticker.upper():
                return f"{int(row['cik_str']):010d}"
        raise KeyError(f"{ticker} is not in the SEC ticker file")

    def submissions(self, cik):
        return self.get_json(f"https://data.sec.gov/submissions/CIK{cik}.json",
                             f"submissions_{cik}.json")

    def filings(self, cik):
        """Every filing for a CIK. The 'recent' block stops at 1,000 filings, so heavy
        filers like banks need the older pages it points to as well."""
        subs = self.submissions(cik)
        blocks = [subs["filings"]["recent"]]
        for page in subs["filings"].get("files", []):
            blocks.append(self.get_json(f"https://data.sec.gov/submissions/{page['name']}",
                                        page["name"]))
        rows = []
        for block in blocks:
            keys = list(block.keys())
            for values in zip(*(block[key] for key in keys)):
                rows.append(dict(zip(keys, values)))
        return rows

    def company_facts(self, cik):
        return self.get_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
                             f"companyfacts_{cik}.json")