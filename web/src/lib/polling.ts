/** Checking back for an answer: less often as the wait grows, to keep traffic and logs down (decision 0020). */

/** Wait before the next check: 1 s, 1 s, 2 s, 2 s, then 3 s. */
export function nextDelay(checks: number): number {
  if (checks < 2) return 1_000;
  if (checks < 4) return 2_000;
  return 3_000;
}

/** After this long, the visitor is told the answer is taking longer than usual. */
export const SLOW_AFTER_MS = 20_000;

/** After this long, checking stops and the visitor is asked to try again. */
export const GIVE_UP_AFTER_MS = 180_000;