import { Copy } from "./Copy";

type Section = { heading: string; body: string };

export function LegalPage({ heading, intro, sections, updatedLabel, updated }: {
  heading: string;
  intro: string;
  sections: Section[];
  updatedLabel: string;
  updated: string;
}) {
  return (
    <div className="max-w-prose space-y-8">
      <section className="space-y-3">
        <h1 className="font-serif text-3xl font-semibold leading-tight sm:text-4xl">{heading}</h1>
        <p className="text-sm text-muted">
          {updatedLabel} <Copy text={updated} />
        </p>
        <p className="text-lg text-muted">
          <Copy text={intro} />
        </p>
      </section>
      {sections.map((section) => (
        <section key={section.heading} className="space-y-2 border-t border-rule pt-5">
          <h2 className="font-serif text-xl font-semibold">{section.heading}</h2>
          <p className="leading-relaxed">
            <Copy text={section.body} />
          </p>
        </section>
      ))}
    </div>
  );
}