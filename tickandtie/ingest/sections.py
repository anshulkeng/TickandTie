"""Pull the 10-K Items Tick & Tie uses and clean the text enough to index it."""
import re

from edgar import find, set_identity

from tickandtie import config

set_identity(config.EDGAR_IDENTITY)

KEEP_ITEMS = ["Item 1", "Item 1A", "Item 7", "Item 7A", "Item 8"]

# Under this many characters an Item is almost always a pointer such as
# "see the Financial Section", not the content itself.
CROSS_REF_CHARS = 1000

# Some filers (NVIDIA, for one) leave Item 8 as a one-line pointer and print the
# statements and notes under Item 15 instead.
FALLBACKS = {"Item 8": "Item 15"}
FALLBACK_MIN_CHARS = 20000

# Short lines such as "Apple Inc. | 2025 Form 10-K | 20" are page footers, not content.
# The lookbehind stops a year like "fiscal 2025" being read as a page number.
FOOTER = re.compile(r"^[^\n]{0,80}Form 10-K[^\n]{0,20}?(?<!\d)\d{1,3}[ \t]*$", re.MULTILINE)
SPACES = re.compile(r"[ \t]+")
BLANK_LINES = re.compile(r"\n{3,}")


def clean(text):
    text = text.replace("\xa0", " ")
    text = FOOTER.sub("", text)
    text = SPACES.sub(" ", text)
    text = BLANK_LINES.sub("\n\n", text)
    return text.strip()


def latest_10ks(client, ticker, count):
    """Newest 10-Ks for a ticker, looking under predecessor CIKs too."""
    ciks = [client.ticker_to_cik(ticker)] + config.PREDECESSOR_CIKS.get(ticker, [])
    seen, rows = set(), []
    for cik in ciks:
        for row in client.filings(cik):
            if row["form"] == "10-K" and row["accessionNumber"] not in seen:
                seen.add(row["accessionNumber"])
                rows.append({**row, "cik": cik})
    rows.sort(key=lambda row: row["filingDate"], reverse=True)
    return rows[:count]


def pick_items(raw):
    """Choose the text for each kept Item, falling back when an Item is only a pointer."""
    items, sources = {}, {}
    for item in KEEP_ITEMS:
        text, source = raw.get(item, ""), item
        fallback = FALLBACKS.get(item)
        if (len(text) < CROSS_REF_CHARS and fallback
                and len(raw.get(fallback, "")) >= FALLBACK_MIN_CHARS):
            text, source = raw[fallback], fallback
        items[item], sources[item] = text, source
    return items, sources


def extract_items(accession):
    """Return the kept Items, where each one's text really came from, and every Item's size."""
    tenk = find(accession).obj()
    raw = {item: clean(tenk[item] or "") for item in tenk.items}
    items, sources = pick_items(raw)
    return items, sources, {item: len(text) for item, text in raw.items()}