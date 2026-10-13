import { AskPanel } from "@/components/AskPanel";
import { Copy } from "@/components/Copy";
import { copy } from "@/content/copy";

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
      <AskPanel />
    </div>
  );
}