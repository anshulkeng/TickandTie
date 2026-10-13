import Link from "next/link";

import { TickMark } from "./TickMark";

export function SiteHeader() {
  return (
    <header className="border-b border-rule">
      <div className="mx-auto flex max-w-3xl items-center justify-between gap-4 px-4 py-4">
        <Link href="/" className="flex items-center gap-2 font-serif text-xl font-semibold">
          <TickMark className="h-5 w-5 text-tick" />
          Tick &amp; Tie
        </Link>
        <nav aria-label="Main" className="flex gap-5 text-sm">
          <Link href="/" className="underline-offset-4 hover:underline">Ask</Link>
          <Link href="/how-it-works" className="underline-offset-4 hover:underline">How it works</Link>
          <a href="https://github.com/anshulkeng/TickandTie" className="underline-offset-4 hover:underline">Code</a>
        </nav>
      </div>
    </header>
  );
}