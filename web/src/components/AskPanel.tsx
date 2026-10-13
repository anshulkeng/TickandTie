"use client";

import { type FormEvent, useEffect, useRef, useState } from "react";

import { copy, examples, messages } from "@/content/copy";
import { ApiError, getJob, getStatus, submitQuestion, type Result, type Status } from "@/lib/api";
import { GIVE_UP_AFTER_MS, nextDelay, SLOW_AFTER_MS } from "@/lib/polling";

import { Copy } from "./Copy";

type Phase =
  | { kind: "idle" }
  | { kind: "waiting"; position: number | null; slow: boolean }
  | { kind: "done"; result: Result }
  | { kind: "error"; message: string };

const pause = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export function AskPanel() {
  const [question, setQuestion] = useState("");
  const [phase, setPhase] = useState<Phase>({ kind: "idle" });
  const [status, setStatus] = useState<Status | "unreachable" | null>(null);
  const textarea = useRef<HTMLTextAreaElement>(null);
  const stopped = useRef(false);

  useEffect(() => {
    stopped.current = false;
    getStatus().then(setStatus).catch(() => setStatus("unreachable"));
    return () => {
      stopped.current = true;
    };
  }, []);

  async function ask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = question.trim();
    if (text.length < 3 || text.length > 300) {
      setPhase({ kind: "error", message: messages.questionLength });
      return;
    }
    setPhase({ kind: "waiting", position: null, slow: false });
    try {
      const job = await submitQuestion(text);
      const started = Date.now();
      for (let checks = 0; !stopped.current; checks++) {
        await pause(nextDelay(checks));
        const current = await getJob(job.id);
        if (current.status === "done" && current.result) {
          setPhase({ kind: "done", result: current.result });
          getStatus().then(setStatus).catch(() => setStatus("unreachable"));
          return;
        }
        if (current.status === "failed") {
          setPhase({ kind: "error", message: current.error ?? messages.unexpected });
          return;
        }
        const elapsed = Date.now() - started;
        if (elapsed > GIVE_UP_AFTER_MS) {
          setPhase({ kind: "error", message: messages.tooLong });
          return;
        }
        setPhase({
          kind: "waiting",
          position: current.status === "queued" ? (current.position ?? null) : null,
          slow: elapsed > SLOW_AFTER_MS,
        });
      }
    } catch (error) {
      setPhase({ kind: "error", message: error instanceof ApiError ? error.message : messages.unexpected });
    }
  }

  const busy = phase.kind === "waiting";
  const demo = status !== null && status !== "unreachable" && status.mode === "demo";

  return (
    <div className="space-y-10">
      <section aria-labelledby="ask-heading" className="space-y-4">
        <h2 id="ask-heading" className="sr-only">Ask a question</h2>
        {status !== null && (
          <p className="flex items-center gap-2 text-sm text-muted">
            <span aria-hidden="true" className={`inline-block h-2 w-2 ${demo ? "bg-demo" : "bg-tick"}`} />
            {status === "unreachable" ? messages.unreachable : demo ? messages.statusDemo : messages.statusLive}
          </p>
        )}
        <form onSubmit={ask} className="space-y-3">
          <label htmlFor="question" className="block text-sm font-medium">{messages.questionLabel}</label>
          <textarea
            ref={textarea}
            id="question"
            name="question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            rows={3}
            maxLength={300}
            className="w-full rounded-sm border border-rule bg-white p-3 focus:border-ink"
          />
          <div className="flex items-center justify-between gap-3">
            <button
              type="submit"
              disabled={busy}
              className="rounded-sm bg-ink px-5 py-2.5 text-sm font-medium text-paper disabled:opacity-60"
            >
              {busy ? messages.working : messages.ask}
            </button>
            <span className="font-mono text-xs text-muted">{question.length}/300</span>
          </div>
        </form>

        <div aria-live="polite" className="min-h-6">
          {phase.kind === "waiting" && (
            <p className="text-sm">
              {phase.slow
                ? messages.slow
                : phase.position && phase.position > 1
                  ? messages.queued(phase.position)
                  : messages.checking}
            </p>
          )}
          {phase.kind === "error" && (
            <p role="alert" className="border-l-4 border-refuse bg-white px-4 py-3 text-sm">{phase.message}</p>
          )}
          {phase.kind === "done" && <AnswerView result={phase.result} />}
        </div>
      </section>

      <section aria-labelledby="examples-heading" className="space-y-3">
        <h2 id="examples-heading" className="font-serif text-xl font-semibold">
          <Copy text={copy.examplesHeading} />
        </h2>
        <ul className="divide-y divide-rule border-y border-rule">
          {examples.map((example) => (
            <li key={example}>
              <button
                type="button"
                onClick={() => {
                  setQuestion(example);
                  textarea.current?.focus();
                }}
                className="w-full py-2.5 text-left font-mono text-sm underline-offset-4 hover:underline"
              >
                {example}
              </button>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

/** A basic answer display; step 8c replaces it with clickable citations and the sources panel. */
function AnswerView({ result }: { result: Result }) {
  const refused = result.answer === null;
  const label =
    result.mode === "demo"
      ? result.saved
        ? messages.labelSaved
        : messages.labelDemo
      : refused
        ? messages.labelRefused
        : messages.labelVerified;
  return (
    <article className={`border-l-4 bg-white px-5 py-4 ${refused ? "border-refuse" : "border-tick"}`}>
      <p className="mb-2 font-mono text-xs uppercase tracking-wide text-muted">{label}</p>
      <p className="whitespace-pre-line">{result.answer ?? result.refusal}</p>
    </article>
  );
}