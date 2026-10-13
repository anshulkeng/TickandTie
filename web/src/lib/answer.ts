/** Reading an answer's markup: citations like [F1] or [P2], and risk-diff edits like [-removed-] and {+added+}. */

export type Piece =
  | { kind: "text"; text: string }
  | { kind: "cite"; id: string }
  | { kind: "removed"; text: string }
  | { kind: "added"; text: string };

const TOKENS = /\[([FP]\d+)\]|\[-([\s\S]*?)-\]|\{\+([\s\S]*?)\+\}/g;

export function parse(text: string): Piece[] {
  const pieces: Piece[] = [];
  let last = 0;
  for (const match of text.matchAll(TOKENS)) {
    const start = match.index ?? 0;
    if (start > last) pieces.push({ kind: "text", text: text.slice(last, start) });
    if (match[1]) pieces.push({ kind: "cite", id: match[1] });
    else if (match[2] !== undefined) pieces.push({ kind: "removed", text: match[2] });
    else pieces.push({ kind: "added", text: match[3] ?? "" });
    last = start + match[0].length;
  }
  if (last < text.length) pieces.push({ kind: "text", text: text.slice(last) });
  return pieces;
}

/** Splits an answer into what was found and the "Not covered" part the Verifier allows. */
export function splitGaps(answer: string): { found: string; gaps: string | null } {
  const at = answer.indexOf("Not covered:");
  if (at === -1) return { found: answer, gaps: null };
  return { found: answer.slice(0, at).trim(), gaps: answer.slice(at + "Not covered:".length).trim() };
}