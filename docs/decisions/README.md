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
| [0010](0010-hybrid-search.md) | Hybrid search with reciprocal rank fusion |
| [0011](0011-fiscal-years-from-filings.md) | Fiscal years come from the filings |
| [0012](0012-metric-concept-rules.md) | Everyday metrics map to SEC concepts by written rules |
| [0013](0013-router-rules-first.md) | The Router uses rules first and the model for one decision |
| [0014](0014-plain-code-verifier.md) | A plain-code Verifier checks every answer |
| [0015](0015-filing-text-is-data.md) | Filing text is data, never instructions |
| [0016](0016-partial-answers-and-pipeline.md) | Keep verified sentences, remove failed ones, and say so |
| [0017](0017-evaluation-method.md) | How Tick & Tie is evaluated |
| [0018](0018-risk-factor-diff.md) | The risk-factor diff is plain code with exact quotes |
| [0019](0019-hosted-model-with-demo-fallback.md) | Hosted model with a spending cap, and demo mode as the fallback |