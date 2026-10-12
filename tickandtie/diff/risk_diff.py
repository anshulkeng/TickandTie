"""Risk-factor diff (Task 6): what changed in a company's Item 1A between two annual reports.

Plain code, no language model. Changes are found at sentence level across the whole Item, so text
that only moved between paragraphs is not reported. Paragraphs are matched one to one by word overlap
only to group the changes for display. Every reported sentence is quoted exactly from a filing."""
import json
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from tickandtie import config

FILINGS = config.DATA_DIR / "filings"
MIN_MATCH = 0.5          # provisional: paragraphs less similar than this are grouped as different risks
QUICK_REJECT = 0.4       # speed filter: pairs sharing fewer distinct words than this are not compared
EDIT_MATCH = 0.6         # an added and a removed sentence this similar are shown as one edited sentence
MIN_SENTENCE_WORDS = 4   # shorter fragments, such as "See below.", are not reported
MIN_ITEM_CHARS = 2000    # a shorter Item 1A only points elsewhere and holds no risk factors
HEADING_MAX = 120
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z\u201c\"(])")
QUOTES = str.maketrans({"\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"'})


@dataclass
class Paragraph:
    index: int
    heading: str
    text: str
    words: list = field(repr=False)


@dataclass
class Change:
    kind: str  # "new", "removed" or "changed"
    heading: str
    old: Paragraph = None
    new: Paragraph = None
    similarity: float = 0.0
    added: list = field(default_factory=list)    # sentences found nowhere in the older filing
    removed: list = field(default_factory=list)  # sentences found nowhere in the newer filing
    edits: list = field(default_factory=list)    # (older sentence, newer sentence) pairs


@dataclass
class RiskDiff:
    ticker: str = ""
    older: str = ""
    newer: str = ""
    older_accession: str = ""
    newer_accession: str = ""
    unchanged: int = 0
    reorganised: int = 0  # unmatched paragraphs whose sentences all appear elsewhere
    changes: list = field(default_factory=list)

    def count(self, kind):
        return sum(change.kind == kind for change in self.changes)


def words_of(text):
    return re.findall(r"[a-z0-9]+", text.translate(QUOTES).lower())


def key(sentence):
    return " ".join(words_of(sentence))


def ratio(a, b):
    return SequenceMatcher(None, words_of(a), words_of(b), autojunk=False).ratio()


def paragraphs(text):
    """Item 1A as paragraphs, each with the category heading it sits under."""
    found, heading = [], ""
    for block in (part.strip() for part in text.split("\n\n")):
        if not block or (re.match(r"item\s+1a\b", block, re.IGNORECASE) and len(block) < HEADING_MAX):
            continue
        if found and block[0].islower():  # the source broke a paragraph mid-sentence: join it back
            found[-1].text += " " + block
            found[-1].words = words_of(found[-1].text)
            continue
        if len(block) < HEADING_MAX and not block.endswith((".", ":", ";", "?", "!")):
            heading = block
            continue
        found.append(Paragraph(len(found), heading, block, words_of(block)))
    return found


def sentences(text):
    return [part.strip() for part in SENTENCE_END.split(text) if part.strip()]


def keys_of(paragraph_list):
    return {key(s) for p in paragraph_list for s in sentences(p.text)}


def unseen(text, other_keys):
    """Sentences of a text that appear nowhere in the other filing."""
    return [s for s in sentences(text) if len(words_of(s)) >= MIN_SENTENCE_WORDS and key(s) not in other_keys]


def similarity(a, b):
    if not a.words or not b.words:
        return 0.0
    set_a, set_b = set(a.words), set(b.words)
    if 2 * len(set_a & set_b) / (len(set_a) + len(set_b)) < QUICK_REJECT:
        return 0.0
    return SequenceMatcher(None, a.words, b.words, autojunk=False).ratio()


def match(old, new):
    """One-to-one matches, best pairs first: [(similarity, old paragraph, new paragraph)]."""
    pairs = sorted(((similarity(o, n), o.index, n.index) for o in old for n in new), reverse=True)
    used_old, used_new, matched = set(), set(), []
    for score, old_index, new_index in pairs:
        if score < MIN_MATCH:
            break
        if old_index in used_old or new_index in used_new:
            continue
        used_old.add(old_index)
        used_new.add(new_index)
        matched.append((score, old[old_index], new[new_index]))
    return matched, used_old, used_new


def pair_edits(added, removed):
    """Pair each added sentence with its most similar removed sentence, if similar enough."""
    edits, rest_added, rest_removed = [], [], list(removed)
    for sentence in added:
        best = max(rest_removed, key=lambda r: ratio(r, sentence), default=None)
        if best is not None and ratio(best, sentence) >= EDIT_MATCH:
            edits.append((best, sentence))
            rest_removed.remove(best)
        else:
            rest_added.append(sentence)
    return edits, rest_added, rest_removed


def word_diff(old, new):
    """An edited sentence word by word: [-removed words-] {+added words+}."""
    a, b = old.split(), new.split()
    out = []
    for op, i1, i2, j1, j2 in SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            out.append(" ".join(a[i1:i2]))
        if op in ("delete", "replace"):
            out.append("[-" + " ".join(a[i1:i2]) + "-]")
        if op in ("insert", "replace"):
            out.append("{+" + " ".join(b[j1:j2]) + "+}")
    return " ".join(out)


def diff_texts(old_text, new_text):
    old, new = paragraphs(old_text), paragraphs(new_text)
    old_keys, new_keys = keys_of(old), keys_of(new)
    matched, used_old, used_new = match(old, new)
    result = RiskDiff()
    for score, old_paragraph, new_paragraph in sorted(matched, key=lambda m: m[2].index):
        added, removed = unseen(new_paragraph.text, old_keys), unseen(old_paragraph.text, new_keys)
        if not added and not removed:
            result.unchanged += 1
            continue
        edits, added, removed = pair_edits(added, removed)
        result.changes.append(Change("changed", new_paragraph.heading, old_paragraph, new_paragraph,
                                     score, added, removed, edits))
    for paragraph in new:
        if paragraph.index not in used_new:
            added = unseen(paragraph.text, old_keys)
            if added:
                result.changes.append(Change("new", paragraph.heading, new=paragraph, added=added))
            else:
                result.reorganised += 1
    for paragraph in old:
        if paragraph.index not in used_old:
            removed = unseen(paragraph.text, new_keys)
            if removed:
                result.changes.append(Change("removed", paragraph.heading, old=paragraph, removed=removed))
            else:
                result.reorganised += 1
    return result


def filings(ticker):
    """The ticker's filings that hold a real Item 1A, oldest first: [(period_end, accession, text)]."""
    found = []
    for path in sorted((FILINGS / ticker).glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        text = data["items"].get("Item 1A", "")
        if len(text) >= MIN_ITEM_CHARS:
            found.append((data["period_end"], data["accession"], text))
    return found


def compare(ticker, older=None, newer=None):
    """Diff two years of Item 1A, by default the latest against the one before. None if either is missing."""
    available = filings(ticker)
    by_period = {period: (accession, text) for period, accession, text in available}
    if newer is None and available:
        newer = available[-1][0]
    if older is None and newer:
        earlier = [period for period, _, _ in available if period < newer]
        older = earlier[-1] if earlier else None
    if older not in by_period or newer not in by_period:
        return None
    result = diff_texts(by_period[older][1], by_period[newer][1])
    result.ticker, result.older, result.newer = ticker, older, newer
    result.older_accession, result.newer_accession = by_period[older][0], by_period[newer][0]
    return result