/** The Tick & Tie mark: an auditor's tick. Decorative, so hidden from screen readers. */
export function TickMark({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className={className}>
      <path d="M4 13 L10 19 L20 5" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="square" />
    </svg>
  );
}