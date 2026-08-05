import { DecisionCard } from "@/components/decisions/DecisionCard";
import { StatusPill } from "@/components/ui/StatusPill";
import type { RankedInvestmentCaseViewModel } from "@/lib/view-models/investment-case";

interface TopInvestmentCasesProps {
  cases: readonly RankedInvestmentCaseViewModel[];
}

function ReasonList({
  title,
  reasons,
}: {
  title: string;
  reasons: readonly string[];
}) {
  if (reasons.length === 0) {
    return null;
  }

  return (
    <div className="mt-6">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
        {title}
      </p>
      <ul className="mt-3 space-y-2.5">
        {reasons.map((reason) => (
          <li
            key={reason}
            className="flex gap-3 text-sm leading-5 text-zinc-700"
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
  );
}

function InvestmentCaseCard({
  investmentCase,
}: {
  investmentCase: RankedInvestmentCaseViewModel;
}) {
  return (
    <DecisionCard
      rank={investmentCase.rank}
      symbol={investmentCase.symbol}
      decisionState={investmentCase.recommendation}
      conviction={investmentCase.conviction}
      convictionLabel={investmentCase.convictionLevel}
      previousDecisions={investmentCase.previousDecisions}
      reviewHref={investmentCase.dossierHref}
    >
      <dl className="mt-7 grid grid-cols-2 gap-3 border-y border-slate-100 py-5">
        <div>
          <dt className="text-xs leading-4 text-slate-500">
            Committee agreement
          </dt>
          <dd className="mt-1 text-lg font-semibold text-slate-950">
            {investmentCase.committeeAgreement}%
          </dd>
        </div>
        <div>
          <dt className="text-xs leading-4 text-slate-500">Risk</dt>
          <dd className="mt-1 text-lg font-semibold text-slate-950">
            {investmentCase.riskLevel}
          </dd>
        </div>
      </dl>

      <p className="mt-6 text-sm leading-6 text-slate-600">
        {investmentCase.summary}
      </p>

      <p className="mt-3 text-sm text-slate-500">
        Horizon: {investmentCase.expectedHoldingPeriod}
      </p>

      <ReasonList title="Why now" reasons={investmentCase.whyNow} />
      <ReasonList title="Risks" reasons={investmentCase.risks} />
    </DecisionCard>
  );
}

export function TopInvestmentCases({ cases }: TopInvestmentCasesProps) {
  return (
    <section aria-labelledby="top-investment-cases-heading">
      <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-zinc-500">
            Executive Committee
          </p>

          <div className="mt-3 flex flex-wrap items-center gap-3">
            <h2
              id="top-investment-cases-heading"
              className="max-w-3xl text-4xl font-semibold tracking-[-0.045em] text-zinc-950 sm:text-5xl"
            >
              {cases.length === 0
                ? "No holdings to review."
                : `Your ${cases.length} holdings, reviewed.`}
            </h2>

            {/* Real decisions on real holdings, and each decision is now
                recorded, so a case can say what it decided before. Price
                targets are still missing. */}
            {cases.length === 0 ? (
              <StatusPill status="placeholder" label="No data" />
            ) : (
              <StatusPill
                status="partial"
                label="Artificial CIO"
                explanation="Partial, honestly: real decisions on your real holdings, each with its recorded history — but price targets are not measured, so no target or expected upside appears here."
              />
            )}
          </div>
        </div>

        <p className="max-w-md text-sm leading-6 text-zinc-600">
          Ranked by the conviction the Artificial CIO assigned each holding.
          The ranking expresses priority—not certainty.
        </p>
      </div>

      {cases.length > 0 ? (
        <div className="mt-10 grid gap-5 xl:grid-cols-3">
          {cases.map((investmentCase) => (
            <InvestmentCaseCard
              key={investmentCase.symbol}
              investmentCase={investmentCase}
            />
          ))}
        </div>
      ) : null}
    </section>
  );
}
