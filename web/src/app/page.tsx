import { Copy } from "@/components/Copy";
import { copy, examples } from "@/content/copy";

export default function Home() {
  return (
    <div className="space-y-10">
      <section className="space-y-3">
        <h1 className="font-serif text-3xl font-semibold leading-tight sm:text-4xl">
          <Copy text={copy.heroHeading} />
        </h1>
        <p className="max-w-prose text-lg text-muted">
          <Copy text={copy.heroIntro} />
        </p>
      </section>

      <section aria-labelledby="ask-heading" className="space-y-3">
        <h2 id="ask-heading" className="sr-only">Ask a question</h2>
        <form className="space-y-3">
          <label htmlFor="question" className="block text-sm font-medium">Your question</label>
          <textarea
            id="question"
            name="question"
            rows={3}
            maxLength={300}
            className="w-full rounded-sm border border-rule bg-white p-3 focus:border-ink"
          />
          <button
            type="submit"
            disabled
            className="rounded-sm bg-ink px-5 py-2.5 text-sm font-medium text-paper disabled:opacity-60"
          >
            Ask
          </button>
        </form>
      </section>

      <section aria-labelledby="examples-heading" className="space-y-3">
        <h2 id="examples-heading" className="font-serif text-xl font-semibold">
          <Copy text={copy.examplesHeading} />
        </h2>
        <ul className="divide-y divide-rule border-y border-rule">
          {examples.map((example) => (
            <li key={example} className="py-2.5 font-mono text-sm">{example}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}