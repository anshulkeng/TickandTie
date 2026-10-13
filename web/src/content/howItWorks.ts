/**
 * Text for the How it works page. Every TODO is for Anshul to write (design rule: no AI-written copy).
 * Each TODO is shown on the page in a dashed box until it is replaced.
 */
export const howItWorks = {
  heading: "How It Works",
  intro: "Every answer goes through a four-step process, with no AI used for the checks. The results of a blind test are shown below.",
  steps: [
    {
      title: "Receiving the question",
      body: "Simple request: the user asks a question, and the system checks that it is a valid question.",
    },
    {
      title: "Collecting the evidence",
      body: "Figures comes straight from the SEC filings, and text is extracted from the filings and other sources. The AI is given only that evidence to work with.",
    },
    {
      title: "Writing the answer",
      body: "AI writes a draft answer, using only the evidence it was given. It cannot make up any new information.",
    },
    {
      title: "Checking the answer",
      body: "Plain code checks the draft. every figure is checked against its source, and any sentence that cannot be verified is removed.",
    },
  ],
  riskDiff: "Questions about risk factor changes are answered by comparing the text of the latest report with the previous year's report. The AI is given only the two texts to work with, and it cannot make up any new information.",
  resultsIntro: "Before launch, the system was tested on 81 questions. The results are shown in the table below, with a comparison to the same AI without any checks.",
  limits: [
    "It can answer only questions about the 12 companies it knows about, and only about the years for which it has filings.",
    "The checks confirm that the answer is faithful to the source, but they cannot confirm that the source itself is correct.",
    "In a small number of cases, the AI may refuse to answer a question even though it could have answered it correctly. This is a design choice to avoid giving wrong answers.",
    "Some features were added after testing, so the results do not reflect the current capabilities of the system.",
  ],
  sourceNote: "The full results and method are on GitHub, including the 81 questions and their answers, the code that checks the answers, and the evaluation",
};

/** Section headings and table labels. DRAFTED BY CLAUDE as working text; rewrite any before launch. */
export const howItWorksLabels = {
  stepsHeading: "How a question is answered",
  diffHeading: "Risk-factor changes",
  resultsHeading: "Results",
  limitsHeading: "Limits",
  tableCaption: "81 questions, frozen before any run, October 2026. Run on the local model.",
  colMeasure: "Measure",
  colTickAndTie: "Tick & Tie",
  colBaseline: "Same AI without checks",
  otherChecks: "Other checks",
  sourceLink: "Full results and method on GitHub",
};

/**
 * Evaluation results, copied exactly from eval/RESULTS.md. These are numbers, not copy:
 * change them only if the results file changes.
 */
export const results = {
  rows: [
    { label: "Figure questions answered correctly", tickAndTie: "48 of 48", baseline: "28 of 48" },
    { label: "Figure questions answered wrongly", tickAndTie: "0", baseline: "12" },
    { label: "Questions it should decline, declined", tickAndTie: "10 of 10", baseline: "8 of 10" },
    { label: "Trick questions handled", tickAndTie: "3 of 3", baseline: "1 of 3" },
    { label: "Text questions answered", tickAndTie: "14 of 20", baseline: "20 of 20" },
    { label: "Text sentences supported by their source (blind check, 10 each)", tickAndTie: "8 of 10", baseline: "10 of 10" },
    { label: "Median seconds per question", tickAndTie: "22", baseline: "31" },
  ],
  otherChecks: [
    "Risk-factor changes, checked by hand: 10 of 10 correct.",
    "Same tests on the hosted model the website uses: 48 of 48 figures correct, none wrong, 10 of 10 declined, 3 of 3 trick questions.",
    "After fixing a citation-format bug: 18 of 20 text questions answered (a development check, not a fresh test).",
  ],
};