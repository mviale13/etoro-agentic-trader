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

export function ExecutiveBrief({ symbol }: ExecutiveBriefProps) {
  return (
    <main className="mx-auto w-full max-w-4xl px-6 py-12 sm:px-8 lg:px-10">
      <header className="border-b border-slate-200 pb-10">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-slate-500">
          Executive Brief
        </p>

        <h1 className="mt-4 text-4xl font-semibold tracking-tight text-slate-950">
          Microsoft Corporation
        </h1>

        <p className="mt-2 text-base text-slate-500">{symbol} · Technology</p>

        <div className="mt-8">
          <p className="text-sm font-medium text-slate-500">Executive Score</p>
          <p className="mt-1 text-5xl font-semibold tracking-tight text-slate-950">
            92
          </p>
        </div>
      </header>

      <div className="divide-y divide-slate-200">
        {sections.map((section) => (
          <section key={section} className="py-10">
            <h2 className="text-xl font-semibold tracking-tight text-slate-950">
              {section}
            </h2>

            <p className="mt-4 text-sm leading-6 text-slate-500">
              Content coming in the next commit.
            </p>
          </section>
        ))}
      </div>
    </main>
  );
}
