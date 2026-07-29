import Link from "next/link";

import type { RankedInvestmentCaseViewModel } from "@/lib/view-models/investment-case";

interface TopInvestmentCasesProps {
  cases: readonly RankedInvestmentCaseViewModel[];
}

const rankLabels = {
  1: "Highest conviction",
  2: "Second-highest conviction",
  3: "Third-highest conviction",
} as const;

function signedPercentage(value: number): string {
  return `${value > 0 ? "+" : ""}${value}%`;
}

function rankMarker(rank: 1 | 2 | 3): string {
  return rank === 1 ? "01" : rank === 2 ? "02" : "03";
}

function InvestmentCaseCard({
  investmentCase,
}: {
  investmentCase: RankedInvestmentCaseViewModel;
}) {
  const convictionChangeIsPositive = investmentCase.convictionChange >= 0;

  return (
    <article className="group relative overflow-hidden rounded-[28px] border border-zinc-200/80 bg-white p-6 shadow-[0_18px_60px_-36px_rgba(24,24,27,0.45)] transition duration-300 hover:-translate-y-1 hover:shadow-[0_24px_70px_-34px_rgba(24,24,27,0.5)] dark:border-zinc-800 dark:bg-zinc-950">
      <div className="flex items-start justify-between gap-5">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">
            {rankLabels[investmentCase.rank]}
          </p>

          <div className="mt-4 flex items-center gap-3">
            <span className="flex size-10 items-center justify-center rounded-full border border-zinc-200 text-sm font-semibold text-zinc-700 dark:border-zinc-800 dark:text-zinc-300">
              {rankMarker(investmentCase.rank)}
            </span>

            <div>
              <h2 className="text-2xl font-semibold tracking-tight text-zinc-950 dark:text-white">
                {investmentCase.companyName}
              </h2>
              <p className="mt-0.5 text-sm text-zinc-500">
                {investmentCase.exchange}: {investmentCase.symbol}
              </p>
            </div>
          </div>
        </div>

        <span className="rounded-full border border-zinc-200 px-3 py-1.5 text-xs font-semibold text-zinc-700 dark:border-zinc-800 dark:text-zinc-300">
          {investmentCase.recommendation}
        </span>
      </div>

      <div className="mt-8">
        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-zinc-500">Executive conviction</p>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-5xl font-semibold tracking-[-0.06em] text-zinc-950 dark:text-white">
                {investmentCase.conviction}%
              </span>
              <span
                className={`text-sm font-semibold ${
                  convictionChangeIsPositive
                    ? "text-emerald-600 dark:text-emerald-400"
                    : "text-amber-600 dark:text-amber-400"
                }`}
              >
                {signedPercentage(investmentCase.convictionChange)}
              </span>
            </div>
          </div>

          <p className="max-w-32 text-right text-sm font-medium leading-5 text-zinc-600 dark:text-zinc-400">
            {investmentCase.convictionLevel}
          </p>
        </div>

        <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-900">
          <div
            className="h-full rounded-full bg-zinc-950 dark:bg-white"
            style={{ width: `${investmentCase.conviction}%` }}
          />
        </div>
      </div>

      <dl className="mt-7 grid grid-cols-3 gap-3 border-y border-zinc-100 py-5 dark:border-zinc-900">
        <div>
          <dt className="text-xs leading-4 text-zinc-500">Potential upside</dt>
          <dd className="mt-1 text-lg font-semibold text-zinc-950 dark:text-white">
            {signedPercentage(investmentCase.expectedUpside)}
          </dd>
        </div>
        <div>
          <dt className="text-xs leading-4 text-zinc-500">Potential downside</dt>
          <dd className="mt-1 text-lg font-semibold text-zinc-950 dark:text-white">
            {signedPercentage(investmentCase.potentialDownside)}
          </dd>
        </div>
        <div>
          <dt className="text-xs leading-4 text-zinc-500">Agreement</dt>
          <dd className="mt-1 text-lg font-semibold text-zinc-950 dark:text-white">
            {investmentCase.committeeAgreement}%
          </dd>
        </div>
      </dl>

      <p className="mt-6 text-sm leading-6 text-zinc-600 dark:text-zinc-400">
        {investmentCase.summary}
      </p>

      <div className="mt-6">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
          Why now
        </p>
        <ul className="mt-3 space-y-2.5">
          {investmentCase.whyNow.map((reason) => (
            <li
              key={reason}
              className="flex gap-3 text-sm leading-5 text-zinc-700 dark:text-zinc-300"
            >
              <span
                aria-hidden="true"
                className="mt-2 size-1.5 shrink-0 rounded-full bg-zinc-400"
              />
              <span>{reason}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-7 flex items-center justify-between gap-4">
        <span className="text-xs font-medium text-zinc-500">
          Risk: {investmentCase.riskLevel}
        </span>

        <Link
          href={investmentCase.dossierHref}
          className="inline-flex items-center gap-2 text-sm font-semibold text-zinc-950 transition group-hover:gap-3 dark:text-white"
        >
          Open investment case
          <span aria-hidden="true">→</span>
        </Link>
      </div>
    </article>
  );
}

export function TopInvestmentCases({ cases }: TopInvestmentCasesProps) {
  if (cases.length !== 3) {
    throw new Error(
      `TopInvestmentCases requires exactly three ranked cases; received ${cases.length}.`,
    );
  }

  return (
    <section aria-labelledby="top-investment-cases-heading">
      <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-zinc-500">
            Executive Committee
          </p>
          <h1
            id="top-investment-cases-heading"
            className="mt-3 max-w-3xl text-4xl font-semibold tracking-[-0.045em] text-zinc-950 sm:text-5xl dark:text-white"
          >
            Three investment cases deserve your attention.
          </h1>
        </div>

        <p className="max-w-md text-sm leading-6 text-zinc-600 dark:text-zinc-400">
          Ranked by conviction, expected reward, downside risk and committee
          agreement. The ranking expresses priority—not certainty.
        </p>
      </div>

      <div className="mt-10 grid gap-5 xl:grid-cols-3">
        {cases.map((investmentCase) => (
          <InvestmentCaseCard
            key={investmentCase.symbol}
            investmentCase={investmentCase}
          />
        ))}
      </div>
    </section>
  );
}
