import { messages } from "@/content/copy";
import { parse, splitGaps } from "@/lib/answer";
import type { Result } from "@/lib/api";

/** Answer text with clickable citations and risk-diff edits (strike-through and underline, not colour alone). */
function Rich({ text }: { text: string }) {
  return (
    <>
      {parse(text).map((piece, index) => {
        if (piece.kind === "cite") {
          return (
            <a
              key={index}
              href={`#source-${piece.id}`}
              aria-label={messages.citationLabel(piece.id)}
              className="mx-0.5 font-mono text-xs text-tick underline underline-offset-2"
            >
              [{piece.id}]
            </a>
          );
        }
        if (piece.kind === "removed") {
          return <del key={index} className="bg-refuse/10 text-refuse">{piece.text}</del>;
        }
        if (piece.kind === "added") {
          return <ins key={index} className="bg-tick/10 text-tick">{piece.text}</ins>;
        }
        return <span key={index}>{piece.text}</span>;
      })}
    </>
  );
}

export function AnswerView({ result, onPick }: { result: Result; onPick: (question: string) => void }) {
  const refused = result.answer === null;
  const label =
    result.mode === "demo"
      ? result.saved
        ? messages.labelSaved
        : messages.labelDemo
      : refused
        ? messages.labelRefused
        : messages.labelVerified;
  const { found, gaps } = splitGaps(result.answer ?? "");
  const sources = Object.entries(result.sources ?? {});
  const periods = result.periods ?? [];
  const notes = result.notes ?? [];

  return (
    <article className={`space-y-5 border-l-4 bg-white px-5 py-4 ${refused ? "border-refuse" : "border-tick"}`}>
      <p className="font-mono text-xs uppercase tracking-wide text-muted">{label}</p>
      {result.saved && <p className="text-sm text-demo">{messages.savedExplainer}</p>}

      {refused ? (
        <p className="whitespace-pre-line">{result.refusal}</p>
      ) : (
        <>
          <p className="whitespace-pre-line leading-relaxed">
            <Rich text={found} />
          </p>
          {gaps && (
            <p className="whitespace-pre-line text-sm text-muted">
              <span className="font-medium">{messages.notCovered}</span> <Rich text={gaps} />
            </p>
          )}
        </>
      )}

      {result.removed > 0 && <p className="text-sm text-muted">{messages.removed(result.removed)}</p>}

      {result.suggestions && result.suggestions.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium">{messages.trySaved}</p>
          <ul className="divide-y divide-rule border-y border-rule">
            {result.suggestions.map((question) => (
              <li key={question}>
                <button
                  type="button"
                  onClick={() => onPick(question)}
                  className="w-full py-2 text-left font-mono text-sm underline-offset-4 hover:underline"
                >
                  {question}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {sources.length > 0 && (
        <section aria-labelledby="sources-heading" className="space-y-2">
          <h3 id="sources-heading" className="font-serif text-base font-semibold">{messages.sources}</h3>
          <ol className="space-y-2 text-sm">
            {sources.map(([id, text]) => (
              <li
                key={id}
                id={`source-${id}`}
                className="scroll-mt-24 border-l-2 border-rule pl-3 target:border-tick target:bg-tick/5"
              >
                <span className="font-mono text-xs text-tick">[{id}]</span> {text}
              </li>
            ))}
          </ol>
        </section>
      )}

      {periods.length > 0 && (
        <section aria-labelledby="periods-heading" className="space-y-1">
          <h3 id="periods-heading" className="font-serif text-base font-semibold">{messages.periods}</h3>
          <ul className="font-mono text-xs text-muted">
            {periods.map((period) => (
              <li key={period}>{period}</li>
            ))}
          </ul>
        </section>
      )}

      {(notes.length > 0 || result.seconds > 0) && (
        <details className="text-sm text-muted">
          <summary className="cursor-pointer">{messages.checkedDetails}</summary>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            {notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
            {result.seconds > 0 && <li>{messages.seconds(result.seconds)}</li>}
          </ul>
        </details>
      )}
    </article>
  );
}