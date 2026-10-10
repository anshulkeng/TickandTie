# 0005: Split 10-Ks with edgartools, add fallbacks, record gaps

Status: Accepted, October 2026

## Context
I need Items 1, 1A, 7, 7A and 8 as separate text. edgartools splits 10-Ks into Items, but across 36 reports it is not always right.

## Decision
Use edgartools, then:
- clean non-breaking spaces and page footers;
- when Item 8 is only a pointer and Item 15 holds the statements (as with NVIDIA), use Item 15 and record that it did;
- flag any Item under 1,000 characters as a cross-reference, and any Item under 40% of the same company's usual size as a likely bad split.

The warnings are saved inside each report record.

## Alternatives considered
- Write my own HTML parser: weeks of work for layouts edgartools already handles.
- Drop flagged reports: would hide the failures instead of measuring them.

## Consequences
Known gaps, recorded rather than hidden:
- XOM fiscal 2023: Items 7 and 8 only point to a separate Financial Section.
- WMT fiscal 2024: Item 8 is missing the notes to the financial statements.
- Item 7A only points to Item 7 for JPM, JNJ, PFE, XOM and CAT.
- Some text has words glued together. The effect on search is measured in Task 3.

Numbers are unaffected, because they come from XBRL (0002).