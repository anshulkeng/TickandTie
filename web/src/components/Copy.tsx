/** Visitor-facing text. A TODO placeholder is drawn in a dashed box, so none can slip through to launch. */
export function Copy({ text, className = "" }: { text: string; className?: string }) {
  const placeholder = text.startsWith("TODO");
  return (
    <span className={placeholder ? `${className} border border-dashed border-demo px-1 text-demo` : className}>
      {text}
    </span>
  );
}