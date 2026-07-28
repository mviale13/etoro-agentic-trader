import Link from "next/link";

import type {
  ExecutivePriority,
  ExecutiveWorkspaceViewModel,
} from "@/types/executive-workspace";

type ExecutiveWorkspaceProps = {
  workspace: ExecutiveWorkspaceViewModel;
};

function SectionHeading({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description?: string;
}) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
        {eyebrow}
      </p>
      <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">
        {title}
      </h2>
      {description ? (
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          {description}
        </p>
      ) : null}
    </div>
  );
}

function PriorityRow({
  priority,
  isLast,
}: {
  priority: ExecutivePriority;
  isLast: boolean;
}) {
  return (
    <article className={isLast ? "pt-6" : "border-b border-slate-200 pb-6"}>
      <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-start">
        <div className="min-w-0">
          <div className="flex items-baseline gap-3">
            <h3 className="text-lg font-semibold text-slate-950">
              {priority.name}
            </h3>
            <span className="text-sm font-medium text-slate-500">
              {priority.symbol}
            </span>
          </div>
          <p className="mt-3 max-w-2xl text-base leading-7 text-slate-700">
            {priority.summary}
          </p>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
            {priority.rationale}
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-5 sm:flex-col sm:items-end sm:gap-3">
          <div className="text-left sm:text-right">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              Executive score
            </p>
            <p className="mt-1 text-3xl font-semibold tracking-tight text-slate-950">
              {priority.executiveScore}
            </p>
          </div>
          <Link
            className="text-sm font-semibold text-slate-950 underline decoration-slate-300 underline-offset-4 transition hover:decoration-slate-950"
            href={priority.href}
          >
            Open dossier
          </Link>
        </div>
      </div>
    </article>
  );
}

export function ExecutiveWorkspace({
  workspace,
}: ExecutiveWorkspaceProps) {
  return (
    <main className="mx-auto w-full max-w-6xl px-5 py-10 sm:px-8 sm:py-14 lg:px-10">
      <header className="border-b border-slate-200 pb-10">
        <p className="text-sm font-medium text-slate-500">
          {workspace.dateLabel}
        </p>
        <h1 className="mt-4 text-4xl font-semibold tracking-[-0.035em] text-slate-950 sm:text-5xl">
          {workspace.greeting}
        </h1>
        <p className="mt-5 max-w-3xl text-lg leading-8 text-slate-600">
          {workspace.briefing}
        </p>
      </header>

      <div className="mt-10 grid gap-6 lg:grid-cols-12">
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8 lg:col-span-8">
          <SectionHeading
            eyebrow="Today"
            title="Investment dossiers"
            description={`${workspace.priorities.length} opportunities deserve closer attention.`}
          />

          <div className="mt-8">
            {workspace.priorities.map((priority, index) => (
              <PriorityRow
                key={priority.symbol}
                priority={priority}
                isLast={index === workspace.priorities.length - 1}
              />
            ))}
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8 lg:col-span-4">
          <SectionHeading eyebrow="Portfolio" title="Portfolio health" />

          <div className="mt-8 flex items-end justify-between gap-4">
            <div>
              <p className="text-5xl font-semibold tracking-[-0.04em] text-slate-950">
                {workspace.portfolio.grade}
              </p>
              <p className="mt-2 text-sm font-semibold text-slate-700">
                {workspace.portfolio.status}
              </p>
            </div>
            <div className="text-right text-sm text-slate-500">
              <p>Risk · {workspace.portfolio.riskLevel}</p>
              <p className="mt-1">
                Cash · {workspace.portfolio.cashAllocation}%
              </p>
            </div>
          </div>

          <p className="mt-7 text-sm leading-6 text-slate-600">
            {workspace.portfolio.summary}
          </p>

          <Link
            className="mt-7 inline-block text-sm font-semibold text-slate-950 underline decoration-slate-300 underline-offset-4 transition hover:decoration-slate-950"
            href="/portfolio"
          >
            Review portfolio
          </Link>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8 lg:col-span-7">
          <SectionHeading
            eyebrow="Markets"
            title="Market intelligence"
            description={workspace.market.headline}
          />

          <p className="mt-6 text-sm leading-6 text-slate-600">
            {workspace.market.summary}
          </p>

          <ul className="mt-6 divide-y divide-slate-200 border-y border-slate-200">
            {workspace.market.signals.map((signal) => (
              <li
                key={signal}
                className="flex items-center gap-3 py-3 text-sm text-slate-700"
              >
                <span
                  aria-hidden="true"
                  className="h-1.5 w-1.5 rounded-full bg-slate-400"
                />
                {signal}
              </li>
            ))}
          </ul>
        </section>

        {workspace.importantEvent ? (
          <section className="rounded-2xl border border-slate-200 bg-slate-950 p-6 text-white shadow-sm sm:p-8 lg:col-span-5">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
              Important event
            </p>
            <h2 className="mt-3 text-2xl font-semibold tracking-tight">
              {workspace.importantEvent.title}
            </h2>
            <p className="mt-2 text-sm font-medium text-slate-300">
              {workspace.importantEvent.timing}
            </p>
            <p className="mt-6 text-sm leading-6 text-slate-300">
              {workspace.importantEvent.summary}
            </p>
            <Link
              className="mt-7 inline-block text-sm font-semibold text-white underline decoration-slate-600 underline-offset-4 transition hover:decoration-white"
              href={workspace.importantEvent.href}
            >
              Why it matters
            </Link>
          </section>
        ) : null}
      </div>
    </main>
  );
}
