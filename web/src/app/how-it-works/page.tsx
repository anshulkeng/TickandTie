import type { Metadata } from "next";

import { Copy } from "@/components/Copy";
import { howItWorks, howItWorksLabels as labels, results } from "@/content/howItWorks";

export const metadata: Metadata = { title: "How it works | Tick & Tie" };

const RESULTS_URL = "https://github.com/anshulkeng/TickandTie/blob/main/eval/RESULTS.md";

export default function HowItWorks() {
  return (
    <div className="space-y-12">
      <section className="space-y-3">
        <h1 className="font-serif text-3xl font-semibold leading-tight sm:text-4xl">
          <Copy text={howItWorks.heading} />
        </h1>
        <p className="max-w-prose text-lg text-muted">
          <Copy text={howItWorks.intro} />
        </p>
      </section>

      <section aria-labelledby="steps-heading" className="space-y-4">
        <h2 id="steps-heading" className="font-serif text-xl font-semibold">{labels.stepsHeading}</h2>
        <ol className="space-y-4">
          {howItWorks.steps.map((step, index) => (
            <li key={step.title} className="grid grid-cols-[2.5rem_1fr] gap-3 border-t border-rule pt-4">
              <span className="font-mono text-sm text-tick">{String(index + 1).padStart(2, "0")}</span>
              <div className="space-y-1">
                <h3 className="font-medium">
                  <Copy text={step.title} />
                </h3>
                <p className="text-muted">
                  <Copy text={step.body} />
                </p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section aria-labelledby="diff-heading" className="space-y-3">
        <h2 id="diff-heading" className="font-serif text-xl font-semibold">{labels.diffHeading}</h2>
        <p className="max-w-prose text-muted">
          <Copy text={howItWorks.riskDiff} />
        </p>
      </section>

      <section aria-labelledby="results-heading" className="space-y-4">
        <h2 id="results-heading" className="font-serif text-xl font-semibold">{labels.resultsHeading}</h2>
        <p className="max-w-prose text-muted">
          <Copy text={howItWorks.resultsIntro} />
        </p>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[32rem] border-collapse text-sm">
            <caption className="pb-2 text-left text-xs text-muted">{labels.tableCaption}</caption>
            <thead>
              <tr className="border-b border-ink text-left">
                <th scope="col" className="py-2 pr-4 font-medium">{labels.colMeasure}</th>
                <th scope="col" className="py-2 pr-4 font-medium">{labels.colTickAndTie}</th>
                <th scope="col" className="py-2 font-medium">{labels.colBaseline}</th>
              </tr>
            </thead>
            <tbody>
              {results.rows.map((row) => (
                <tr key={row.label} className="border-b border-rule">
                  <th scope="row" className="py-2 pr-4 text-left font-normal">{row.label}</th>
                  <td className="py-2 pr-4 font-mono">{row.tickAndTie}</td>
                  <td className="py-2 font-mono text-muted">{row.baseline}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <h3 className="font-medium">{labels.otherChecks}</h3>
        <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
          {results.otherChecks.map((check) => (
            <li key={check}>{check}</li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="limits-heading" className="space-y-3">
        <h2 id="limits-heading" className="font-serif text-xl font-semibold">{labels.limitsHeading}</h2>
        <ul className="list-disc space-y-2 pl-5 text-muted">
          {howItWorks.limits.map((limit) => (
            <li key={limit}>
              <Copy text={limit} />
            </li>
          ))}
        </ul>
      </section>

      <p className="text-sm">
        <Copy text={howItWorks.sourceNote} />{" "}
        <a href={RESULTS_URL} className="underline underline-offset-4">{labels.sourceLink}</a>
      </p>
    </div>
  );
}