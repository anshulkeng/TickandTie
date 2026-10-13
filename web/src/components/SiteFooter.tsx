import Link from "next/link";

import { copy } from "@/content/copy";

import { Copy } from "./Copy";

export function SiteFooter() {
  return (
    <footer className="mt-16 border-t border-rule">
      <div className="mx-auto flex max-w-3xl flex-col gap-3 px-4 py-6 text-sm text-muted sm:flex-row sm:justify-between">
        <Copy text={copy.footerNote} />
        <nav aria-label="Legal" className="flex gap-5">
          <Link href="/privacy" className="underline-offset-4 hover:underline">Privacy</Link>
          <Link href="/terms" className="underline-offset-4 hover:underline">Terms</Link>
        </nav>
      </div>
    </footer>
  );
}