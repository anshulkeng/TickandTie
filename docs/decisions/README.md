# Decision records

One file per decision: context, decision, alternatives considered, consequences. New decisions take the next number. When a decision changes, a new record supersedes the old one; old records are not rewritten.

| # | Decision |
| --- | --- |
| [0001](0001-local-free-model-stack.md) | Free, local model stack |
| [0002](0002-xbrl-is-ground-truth.md) | XBRL facts are the ground truth for numbers |
| [0003](0003-period-dates-not-fy.md) | Decide the year from period dates, not the SEC fy field |
| [0004](0004-company-identity-and-history.md) | A ticker is not a company identity; read the full filing history |
| [0005](0005-item-splitting-with-fallbacks.md) | Split 10-Ks with edgartools, add fallbacks, record gaps |
| [0006](0006-nextjs-website.md) | Next.js for the website, not Streamlit |
| [0007](0007-free-public-no-accounts.md) | A free public tool with no accounts or payments |
| [0008](0008-data-not-committed.md) | Data is rebuilt, never committed |
| [0009](0009-chunking.md) | Paragraph-aware chunks of about 1,200 characters, pointers skipped |