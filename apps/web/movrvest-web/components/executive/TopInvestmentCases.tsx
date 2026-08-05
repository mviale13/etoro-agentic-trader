import Link from "next/link";
import { ArrowRight, ChevronDown } from "lucide-react";

import { StatusPill } from "@/components/ui/StatusPill";
import type { RankedInvestmentCaseViewModel } from "@/lib/view-models/investment-case";

interface TopInvestmentCasesProps {
  cases: readonly RankedInvestmentCaseViewModel[];
}

/** Direction as a mark, so the eye reads it before the sentence. */
const TREND_MARK: Record<string, string> = {
  stable: "→",
  improving: "↑",
  deteriorating: "↓",
};

const TREND_TONE: Record<string, string> = {
  stable: "text-slate-400",
  improving: "text-emerald-600",
  deteriorating: "text-amber-600",
};

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
    <div>
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
        {title}
      </p>

      <ul className="mt-2 space-y-1.5">
        {reasons.map((reason) => (
          <li key={reason} className="flex gap-2.5 text-sm leading-6 text-slate-700">
            <span
              aria-hidden="true"
              className="mt-2.5 size-1 shrink-0 rounded-full bg-slate-400"
            />

            <span>{reason}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Figure({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs leading-4 text-slate-500">{label}</dt>
      <dd className="mt-1 text-lg font-semibold text-slate-950">{value}</dd>
    </div>
  );
}

/**
 * One holding in the ranking: what to do about it, and how sure the CIO is.
 *
 * The row carries only what a Chief Investment Officer scans — the
 * decision, the action, the conviction and which way the case is moving.
 * Ten identical reports asked the reader to read ten of everything to
 * find the one that mattered; the rest of each case is a click away and
 * unchanged.
 */
function CaseRow({
  investmentCase,
}: {
  investmentCase: RankedInvestmentCaseViewModel;
}) {
  const trend = investmentCase.trend;

  return (
    <details className="group">
      <summary className="grid cursor-pointer grid-cols-[2.5rem_1fr_auto] items-center gap-x-4 gap-y-1 px-5 py-4 hover:bg-slate-50 sm:grid-cols-[2.5rem_7rem_1fr_auto]">
        <span className="text-sm font-semibold tabular-nums text-slate-400">
          {String(investmentCase.rank).padStart(2, "0")}
        </span>

        <span className="flex flex-col">
          <span className="flex items-center gap-2">
            <span className="font-semibold text-slate-950">
              {investmentCase.symbol}
            </span>

            {trend ? (
              <span
                aria-label={trend.stated}
                title={trend.stated}
                className={`text-sm ${TREND_TONE[trend.direction] ?? "text-slate-400"}`}
              >
                {TREND_MARK[trend.direction] ?? "•"}
              </span>
            ) : null}
          </span>

          {/* What kind of investment this is read as — the thing that
              determines how it was analysed. */}
          {investmentCase.playbookName ? (
            <span className="text-xs text-slate-500">
              {investmentCase.playbookName}
            </span>
          ) : null}
        </span>

        {/* The action, not the decision state: it is what the row is for.
            The state is beside the conviction, where it belongs. */}
        <span className="col-span-2 text-sm leading-6 text-slate-700 sm:col-span-1">
          {investmentCase.action?.statement ?? investmentCase.summary}
        </span>

        <span className="col-start-3 flex items-center justify-end gap-3 sm:col-start-4">
          <span className="hidden text-xs font-medium uppercase tracking-wide text-slate-500 sm:inline">
            {investmentCase.recommendation}
          </span>

          <span className="flex items-baseline gap-1.5">
            {/* The move, where there was one. Arithmetic on two recorded
                convictions — nothing here is estimated. */}
            {investmentCase.convictionChange ? (
              <span
                className={`text-xs font-semibold tabular-nums ${
                  investmentCase.convictionChange.delta > 0
                    ? "text-emerald-600"
                    : "text-amber-600"
                }`}
              >
                {investmentCase.convictionChange.delta > 0 ? "↑" : "↓"}
                {Math.abs(investmentCase.convictionChange.delta)}
              </span>
            ) : null}

            <span className="text-sm font-semibold tabular-nums text-slate-950">
              {investmentCase.conviction}
            </span>
          </span>

          <ChevronDown
            aria-hidden
            className="size-4 text-slate-400 transition-transform group-open:rotate-180"
          />

          <span className="sr-only">Open this case</span>
        </span>
      </summary>

      <div className="space-y-5 border-t border-slate-100 bg-slate-50/60 px-5 py-5">
        <p className="text-sm leading-6 text-slate-700">
          {investmentCase.summary}
        </p>

        {/* Only where the action rests on something the summary does not
            already say — for a case short of evidence, the CIO names the
            missing figure. Printing the rationale twice is the repetition
            this list exists to remove. The checkpoint is not repeated at
            all: it is the first line of "Why now" below. */}
        {investmentCase.action &&
        investmentCase.action.because !== investmentCase.summary ? (
          <p className="text-sm leading-6 text-slate-600">
            {investmentCase.action.because}
          </p>
        ) : null}

        <dl className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <Figure
            label="Conviction"
            value={`${investmentCase.conviction} / 100`}
          />

          <Figure
            label="Committee agreement"
            value={`${investmentCase.committeeAgreement}%`}
          />

          {/* This security's own, not the account's — and higher is safer,
              the way every score on this platform now runs. */}
          <Figure
            label="Safety"
            value={
              investmentCase.safetyScore === null
                ? "Not measured"
                : `${investmentCase.safetyScore} / 100`
            }
          />

          <Figure label="Horizon" value={investmentCase.expectedHoldingPeriod} />
        </dl>

        {/* Why the conviction moved: each line is a score that measurably
            differed between the two decisions. A decision recorded before
            the platform kept its scores says so, rather than showing an
            empty list as though nothing had moved. */}
        {investmentCase.convictionChange ? (
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              {investmentCase.convictionChange.stated}, from{" "}
              {investmentCase.convictionChange.previous}
            </p>

            {investmentCase.convictionChange.unexplained ? (
              <p className="mt-2 text-sm leading-6 text-slate-500">
                The earlier decision was recorded before this platform kept
                its scores, so what moved underneath cannot be said.
              </p>
            ) : investmentCase.convictionChange.because.length > 0 ? (
              <ul className="mt-2 space-y-1.5">
                {investmentCase.convictionChange.because.map((line) => (
                  <li
                    key={line}
                    className="flex gap-2.5 text-sm leading-6 text-slate-700"
                  >
                    <span
                      aria-hidden="true"
                      className="mt-2.5 size-1 shrink-0 rounded-full bg-slate-400"
                    />

                    <span>{line}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-2 text-sm leading-6 text-slate-500">
                No individual score moved; the conviction reflects the case
                as a whole.
              </p>
            )}
          </div>
        ) : null}

        <ReasonList title="Why now" reasons={investmentCase.whyNow} />
        <ReasonList title="Risks" reasons={investmentCase.risks} />

        {trend ? (
          <p className="text-sm font-medium text-slate-600">{trend.stated}</p>
        ) : null}

        <Link
          href={investmentCase.dossierHref}
          className="inline-flex items-center gap-2 text-sm font-semibold text-slate-950 hover:gap-3"
        >
          Review the full case
          <ArrowRight aria-hidden="true" className="size-4" />
        </Link>
      </div>
    </details>
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
                : `Your ${cases.length} holdings, ranked.`}
            </h2>

            {/* Real decisions on real holdings, and each decision is now
                recorded, so a case can say which way it is moving. Price
                targets are still missing. */}
            {cases.length === 0 ? (
              <StatusPill status="placeholder" label="No data" />
            ) : (
              <StatusPill
                status="partial"
                label="Artificial CIO"
                explanation="Partial, honestly: real decisions on your real holdings, each with its recorded trend — but price targets are not measured, so no target or expected upside appears here."
              />
            )}
          </div>
        </div>

        <p className="max-w-md text-sm leading-6 text-zinc-600">
          Ranked by the conviction the Artificial CIO assigned each holding.
          The ranking expresses priority—not certainty. Open a row for the
          case behind it.
        </p>
      </div>

      {cases.length > 0 ? (
        <div className="mt-8 overflow-hidden rounded-[28px] border border-slate-200 bg-white">
          <div className="divide-y divide-slate-100">
            {cases.map((investmentCase) => (
              <CaseRow
                key={investmentCase.symbol}
                investmentCase={investmentCase}
              />
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
