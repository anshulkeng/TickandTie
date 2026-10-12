"""Turn a risk-factor diff into an answer. Built by code from exact quotes; no language model writes it."""
from difflib import SequenceMatcher

from tickandtie.diff.risk_diff import word_diff

LIMIT = 5


def changed_words(old, new):
    a, b = old.split(), new.split()
    return sum(max(i2 - i1, j2 - j1) for op, i1, i2, j1, j2
               in SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if op != "equal")


def bullets(items, limit):
    lines = [f'- "{item}"' for item in items[:limit]]
    if len(items) > limit:
        lines.append(f"- ...and {len(items) - limit} more.")
    return lines


def render_diff(result, name, limit=LIMIT):
    added = [s for c in sorted(result.changes, key=lambda c: c.kind != "new") for s in c.added]
    removed = [s for c in sorted(result.changes, key=lambda c: c.kind != "removed") for s in c.removed]
    edits = sorted((e for c in result.changes for e in c.edits), key=lambda e: -changed_words(*e))
    lines = [
        f"{name}'s risk factors (Item 1A): the 10-K for the period ending {result.older} "
        f"(filing {result.older_accession}) compared with the 10-K for the period ending {result.newer} "
        f"(filing {result.newer_accession}).",
        f"Compared by plain text matching: {len(added)} sentences added, {len(removed)} removed and "
        f"{len(edits)} reworded; {result.unchanged} paragraphs unchanged. Every quote below is exact.",
    ]
    if not (added or removed or edits):
        lines.append("No differences were found in the risk factor text.")
        return "\n".join(lines)
    if added:
        lines += ["", f"New in the {result.newer} filing:"] + bullets(added, limit)
    if removed:
        lines += ["", f"No longer in the {result.newer} filing:"] + bullets(removed, limit)
    if edits:
        lines += ["", "Reworded, largest changes first ([-removed-] {+added+}):"]
        lines += [f"- {word_diff(old, new)}" for old, new in edits[:limit]]
        if len(edits) > limit:
            lines.append(f"- ...and {len(edits) - limit} more.")
    return "\n".join(lines)