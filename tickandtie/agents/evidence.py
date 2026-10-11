"""Evidence given to the Writer: numbered facts (F1, F2...) and passages (P1, P2...).

The Verifier checks the answer against exactly this evidence, so both see the same ids and numbers."""
import re
from dataclasses import dataclass, field

from tickandtie import config
from tickandtie.agents.numbers import change, format_value
from tickandtie.index.search_indexes import ITEM_TITLES

NUMBER = re.compile(r"(?<![\w.\-/])\$?(\d[\d,]*(?:\.\d+)?)")


def numbers_in(text):
    """Every number written in a piece of text, as floats ("$391,035 million" gives 391035.0)."""
    values = []
    for raw in NUMBER.findall(text):
        digits = raw.replace(",", "")
        if digits:
            values.append(float(digits))
    return values


@dataclass
class EvidenceItem:
    id: str
    kind: str  # "fact" or "passage"
    text: str
    numbers: list  # for facts: only the figure itself, so dates and filing numbers are never "allowed"


@dataclass
class Evidence:
    items: dict = field(default_factory=dict)

    def add(self, kind, text, numbers):
        prefix = "F" if kind == "fact" else "P"
        item_id = f"{prefix}{sum(1 for item in self.items.values() if item.kind == kind) + 1}"
        self.items[item_id] = EvidenceItem(item_id, kind, text, numbers)
        return item_id

    def add_fact(self, fact):
        """The fact, plus any other figure the company reported for the same metric and year."""
        ids = [self.add("fact", describe_fact(fact), numbers_in(fact.display))]
        for alternate in fact.alternates:
            ids.append(self.add("fact", "Also reported: " + describe_fact(alternate), numbers_in(alternate.display)))
        return ids

    def add_change(self, older, newer):
        """A change between two years, computed in Python so the Writer never does arithmetic."""
        result = change(newer.value, older.value)
        sign = "+" if result["difference"] > 0 else ""
        difference = sign + format_value(result["difference"], newer.unit)
        percent = f"{result['percent']:+.1f}%" if result["percent"] is not None else "percentage not defined"
        name = config.COMPANY_NAMES.get(newer.ticker, newer.ticker)
        text = (f"Change in {name} {newer.label.lower()} from fiscal {older.fiscal_year} "
                f"to fiscal {newer.fiscal_year}: {difference} ({percent}), computed from the two reported figures.")
        return self.add("fact", text, numbers_in(f"{difference} {percent}"))

    def add_passage(self, chunk):
        name = config.COMPANY_NAMES.get(chunk["ticker"], chunk["ticker"])
        title = ITEM_TITLES.get(chunk["item"], "")
        source = (f"{name} 10-K for the period ending {chunk['period_end']}, "
                  f"{chunk['item']} {title}, filing {chunk['accession']}")
        return self.add("passage", f"{source}:\n{chunk['text']}", numbers_in(chunk["text"]))

    def render(self):
        """Evidence as the Writer sees it. A passage can never close the evidence block early."""
        return "\n\n".join(f"[{item.id}] {item.text.replace('</evidence>', '')}" for item in self.items.values())


def describe_fact(fact):
    name = config.COMPANY_NAMES.get(fact.ticker, fact.ticker)
    if fact.period_start:
        period = f"fiscal {fact.fiscal_year}, {fact.period_start} to {fact.period_end}"
    else:
        period = f"at the end of fiscal {fact.fiscal_year} ({fact.period_end})"
    return (f"{name} {fact.label.lower()}, {period}: {fact.display}. "
            f"Reported as {fact.concept} in filing {fact.accession}.")