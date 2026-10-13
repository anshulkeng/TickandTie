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

/**
 * Short functional messages for the question flow: labels, states and errors.
 * DRAFTED BY CLAUDE as working text so the flow can be built and tested. Review and rewrite any of them
 * in your own words before launch.
 */
export const messages = {
  questionLabel: "Your question",
  ask: "Ask",
  working: "Working...",
  questionLength: "Please write a question between 3 and 300 characters.",
  queued: (position: number) => `Waiting for an answer. Your question is number ${position} in the queue.`,
  checking: "Checking the filings and verifying every figure...",
  slow: "This is taking longer than usual. You can keep waiting.",
  tooLong: "This took too long and was stopped. Please try again.",
  unreachable: "Tick & Tie cannot be reached right now. Please try again in a moment.",
  unexpected: "Something went wrong. Please try again.",
  statusLive: "Live answers",
  statusDemo: "Demo mode: live answers are paused, so some questions use saved answers.",
  labelVerified: "Verified answer",
  labelRefused: "Not answered",
  labelSaved: "Saved answer",
  labelDemo: "Demo mode",
};