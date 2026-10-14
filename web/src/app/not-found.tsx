import Link from "next/link";

import { messages } from "@/content/copy";

export default function NotFound() {
  return (
    <div className="space-y-4">
      <h1 className="font-serif text-3xl font-semibold leading-tight">{messages.notFoundHeading}</h1>
      <p className="text-muted">{messages.notFoundBody}</p>
      <Link href="/" className="underline underline-offset-4">{messages.notFoundLink}</Link>
    </div>
  );
}