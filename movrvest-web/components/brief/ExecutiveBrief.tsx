import type { ExecutiveBriefViewModel } from "@/types/executive-brief";

type ExecutiveBriefProps = {
  brief: ExecutiveBriefViewModel;
};

const sections = [
  "Executive Summary",
  "Why This Brief",
  "Committee Consensus",
  "Portfolio Impact",
  "Evidence",
  "Risks",
  "Executive Assessment",
];

export function ExecutiveBrief({
  brief,
}: ExecutiveBriefProps) {
  return (
    <main className="mx-auto max-w-5xl px-8 py-12">
      <header className="border-b border-slate-200 pb-10">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">
          Executive Brief
        </p>

        <h1 className="mt-4 text-4xl font-semibold tracking-tight text-slate-900">
          {brief.companyName}
        </h1>

        <p className="mt-2 text-lg text-slate-500">
          {brief.symbol} • {brief.sector}
        </p>

        <div className="mt-10">
          <p className="text-sm uppercase tracking-wide text-slate-500">
            Executive Score
          </p>

          <p className="mt-2 text-6xl font-semibold tracking-tight text-slate-900">
            {brief.executiveScore}
          </p>

          <p className="mt-3 text-base text-slate-600">
            {brief.attentionLabel}
          </p>

          <p className="mt-2 text-sm text-slate-500">
            {brief.readingTime} • {brief.generatedAt}
          </p>
        </div>
      </header>

      <div className="divide-y divide-slate-200">
        {sections.map((section) => (
          <section key={section} className="py-10">
            <h2 className="text-2xl font-semibold tracking-tight text-slate-900">
              {section}
            </h2>

            <p className="mt-4 text-base leading-7 text-slate-500">
              Content coming in the next commit...
            </p>
          </section>
        ))}
      </div>
    </main>
  );
}
