type ExecutiveBriefProps = {
  symbol: string;
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
  symbol,
}: ExecutiveBriefProps) {
  return (
    <main className="mx-auto max-w-5xl px-8 py-12">
      <header className="border-b border-slate-200 pb-10">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">
          Executive Brief
        </p>

        <h1 className="mt-4 text-4xl font-semibold tracking-tight text-slate-900">
          {symbol}
        </h1>

        <p className="mt-2 text-lg text-slate-500">
          Investment Opportunity
        </p>

        <div className="mt-10">
          <p className="text-sm uppercase tracking-wide text-slate-500">
            Executive Score
          </p>

          <p className="mt-2 text-6xl font-semibold tracking-tight text-slate-900">
            92
          </p>

          <p className="mt-3 text-base text-slate-600">
            Worth your attention this week
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
