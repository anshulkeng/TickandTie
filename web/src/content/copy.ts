/**
 * Every piece of visitor-facing text lives here, so all of it can be written by hand.
 * Design rule: no AI-written copy. Each TODO is shown on the page in a dashed box until it is replaced.
 */
export const copy = {
  siteDescription: "TODO (Anshul): one sentence for search results saying what Tick & Tie does.",
  heroHeading: "TODO (Anshul): a specific heading saying what a visitor can do here.",
  heroIntro:
    "TODO (Anshul): one or two sentences on what it answers and how every figure is checked against SEC filings.",
  examplesHeading: "TODO (Anshul): a short heading for the example questions.",
  footerNote: "TODO (Anshul): one line, for example who built it and that it is not investment advice.",
} as const;

/** Example questions. All were evaluated or need no model, so they also work in demo mode. */
export const examples = [
  "What was Apple's revenue in fiscal 2023?",
  "What diluted EPS did NVIDIA report for fiscal 2026?",
  "How does JPMorgan describe its credit risk management?",
  "What changed in Pfizer's risk factors?",
];