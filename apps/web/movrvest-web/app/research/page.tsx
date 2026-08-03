import Link from "next/link";
import {
  ArrowRight,
  Binoculars,
  CircleAlert,
  Search,
  Sparkles,
  TrendingUp,
} from "lucide-react";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { StatusPill } from "@/components/ui/StatusPill";
import { PageIntegrity } from "@/components/system-integrity/PageIntegrity";
import { getResearchPipeline } from "@/lib/api/research";
import type {
  ResearchCandidateViewModel,
  ResearchFunnelViewModel,
} from "@/lib/view-models/research";

export const dynamic = "force-dynamic";

/**
 * The investment-case lifecycle the Artificial CIO moves a security through.
 *
 * This is the real gate. There is no conviction percentage that makes a case
 * buy-ready, so no threshold line is drawn on one.
 */
const LIFECYCLE = [
  "REJECT",
  "MONITOR",
  "INVESTIGATE",
  "PREPARE",
  "RECOMMEND",
] as const;

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-neutral-200 bg-neutral-50 p-4">
      <span className="block text-xs text-neutral-500">{label}</span>
      <strong className="mt-2 block font-serif text-2xl font-normal text-neutral-950">
        {value}
      </strong>
    </div>
  );
}

/**
 * A score the Artificial CIO may not have been able to measure.
 *
 * An unmeasured score says so. It is never rendered as a zero, and never
 * filled in from a number measured about something else.
 */
function Score({ label, value }: { label: string; value: number | null }) {
  if (value === null) {
    return (
      <div className="rounded-2xl border border-dashed border-neutral-300 bg-white p-4">
        <span className="block text-xs text-neutral-500">{label}</span>
        <strong className="mt-2 block font-serif text-base font-normal italic text-neutral-400">
          Not measured
        </strong>
      </div>
    );
  }

  return <Metric label={label} value={String(value)} />;
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
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-500">
        {title}
      </p>

      <ul className="mt-3 space-y-2">
        {reasons.map((reason) => (
          <li
            className="flex gap-3 text-sm leading-6 text-neutral-700"
            key={reason}
          >
            <span
              aria-hidden="true"
              className="mt-2 size-1.5 shrink-0 rounded-full bg-neutral-400"
            />
            <span>{reason}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Lifecycle({ state }: { state: string }) {
  const current: number = LIFECYCLE.indexOf(
    state as (typeof LIFECYCLE)[number],
  );

  return (
    <ol className="mt-6 flex flex-wrap gap-1.5">
      {LIFECYCLE.map((stage, index) => (
        <li
          className={
            index === current
              ? "rounded-full bg-emerald-950 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-white"
              : index < current
                ? "rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-emerald-800"
                : "rounded-full border border-neutral-200 px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-neutral-400"
          }
          key={stage}
        >
          {stage}
        </li>
      ))}
    </ol>
  );
}

function Funnel({ funnel }: { funnel: ResearchFunnelViewModel }) {
  const steps: readonly (readonly [number, string])[] = [
    [funnel.candidates, "Watched, not held"],
    [funnel.reviewed, "Reviewed this cycle"],
    [funnel.evidenced, "Described on their own evidence"],
    [funnel.judged, "Judged by the Artificial CIO"],
    [funnel.actionable, "Ask for your attention"],
  ];

  return (
    <div className="grid overflow-hidden rounded-2xl border border-neutral-200 bg-white md:grid-cols-5">
      {steps.map(([value, label], index) => (
        <div
          className={
            index === steps.length - 1
              ? "bg-emerald-950 p-6 text-white"
              : "border-b border-neutral-200 p-6 md:border-b-0 md:border-r"
          }
          key={label}
        >
          <strong className="block font-serif text-3xl font-normal">
            {value}
          </strong>

          <span
            className={
              index === steps.length - 1
                ? "mt-2 block text-xs leading-5 text-emerald-100"
                : "mt-2 block text-xs leading-5 text-neutral-500"
            }
          >
            {label}
          </span>
        </div>
      ))}
    </div>
  );
}

function CandidateCard({
  candidate,
}: {
  candidate: ResearchCandidateViewModel;
}) {
  return (
    <article className="overflow-hidden rounded-3xl border border-neutral-200 bg-white shadow-sm">
      <div className="grid lg:grid-cols-[92px_1fr]">
        <div className="border-b border-neutral-200 bg-neutral-50 p-6 lg:border-b-0 lg:border-r">
          <span className="block text-xs uppercase tracking-widest text-neutral-400">
            Rank
          </span>

          <strong className="mt-2 block font-serif text-3xl font-normal text-emerald-950">
            {String(candidate.rank).padStart(2, "0")}
          </strong>
        </div>

        <div className="p-6 md:p-8">
          <div className="flex flex-col justify-between gap-5 md:flex-row">
            <div>
              <div className="flex flex-wrap items-baseline gap-3">
                <h3 className="font-serif text-3xl tracking-[-0.03em] text-neutral-950">
                  {candidate.name}
                </h3>

                <span className="text-xs font-bold tracking-wider text-neutral-500">
                  {candidate.symbol}
                </span>
              </div>

              <div className="mt-3 flex flex-wrap gap-2">
                {[candidate.source, candidate.recommendation].map((tag) => (
                  <span
                    className="rounded-full border border-neutral-200 px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-neutral-500"
                    key={tag}
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            <div className="md:text-right">
              <strong className="block font-serif text-4xl font-normal text-neutral-950">
                {candidate.conviction}%
              </strong>

              <span className="text-xs text-neutral-500">
                executive conviction
              </span>
            </div>
          </div>

          <Lifecycle state={candidate.recommendation} />

          <div className="mt-7 grid gap-4 border-y border-neutral-200 py-6 lg:grid-cols-2">
            {candidate.evidenceWeighed.length > 0 ? (
              <div className="rounded-2xl border border-emerald-200 bg-emerald-50/70 p-5">
                <h4 className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.15em] text-emerald-900">
                  <TrendingUp className="h-4 w-4" />
                  Evidence weighed
                </h4>

                <ul className="mt-3 space-y-2">
                  {candidate.evidenceWeighed.map((line) => (
                    <li
                      className="text-sm font-medium leading-6 text-emerald-950"
                      key={line}
                    >
                      {line}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            <div className="rounded-2xl border border-amber-200 bg-amber-50/80 p-5">
              <h4 className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.15em] text-amber-900">
                <CircleAlert className="h-4 w-4" />
                Why not buy yet
              </h4>

              <p className="mt-3 text-sm font-medium leading-6 text-amber-950">
                {candidate.whyNotYet}
              </p>
            </div>
          </div>

          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            <Score label="Quality" value={candidate.qualityScore} />
            <Score label="Valuation" value={candidate.valuationScore} />
            <Metric label="Evidence" value={String(candidate.evidenceScore)} />
          </div>

          {/* Risk and fit are measured about the account, not this company,
              so they are labelled as such and kept out of the per-company
              row above, where they read as properties of the business. */}
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            <Score
              label="Your portfolio's risk"
              value={candidate.portfolioRiskScore}
            />
            <Metric
              label="Fit with your portfolio"
              value={String(candidate.portfolioFitScore)}
            />
          </div>

          <ReasonList title="Still missing" reasons={candidate.missingEvidence} />
          <ReasonList title="Catalysts" reasons={candidate.catalysts} />

          {candidate.previousDecisions ? (
            <div className="mt-6">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-500">
                Previously
              </p>

              <p className="mt-2 text-sm leading-6 text-neutral-700">
                {candidate.previousDecisions}
              </p>
            </div>
          ) : null}

          {candidate.nextTrigger ? (
            <p className="mt-6 text-sm leading-6 text-neutral-700">
              <span className="font-semibold">Next trigger:</span>{" "}
              {candidate.nextTrigger}
            </p>
          ) : null}

          <div className="mt-7 flex flex-col justify-between gap-4 md:flex-row md:items-center">
            <p className="text-xs text-neutral-500">
              Research candidate only. No capital deployment is currently
              recommended.
            </p>

            <Link
              className="inline-flex items-center justify-center gap-3 rounded-xl bg-emerald-950 px-5 py-3 text-sm font-semibold !text-white shadow-sm transition hover:bg-emerald-800 hover:!text-white"
              href={candidate.dossierHref}
            >
              Open investment dossier
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </div>
    </article>
  );
}

export default async function ResearchPage() {
  const result = await getResearchPipeline();

  const pipeline = result.pipeline;
  const funnel = pipeline?.funnel;
  const candidates = pipeline?.candidates ?? [];

  const highestConviction = candidates.reduce(
    (highest, candidate) => Math.max(highest, candidate.conviction),
    0,
  );

  return (
    <DashboardLayout>
      <main className="mx-auto w-[90%] max-w-[1700px] py-10">
        <PageIntegrity
          status={pipeline ? "partial" : "placeholder"}
          endpoint={pipeline ? "/research/candidates" : undefined}
          description={
            pipeline
              ? "Candidates are the investor's own watchlists, judged by the Artificial CIO on per-security evidence. Each cycle reviews a capped number of them; no upside, price target or sector is estimated."
              : `Backend unreachable, so no candidates are shown. ${result.error ?? ""}`
          }
        />

        <section className="grid gap-8 border-b border-neutral-200 pb-12 xl:grid-cols-[1.2fr_0.8fr]">
          <div>
            <div className="mb-5 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-emerald-800">
              <Sparkles className="h-4 w-4" />
              Opportunity pipeline
            </div>

            <div className="flex flex-wrap items-center gap-4">
              <h1 className="max-w-5xl font-serif text-5xl leading-[0.98] tracking-[-0.05em] text-neutral-950 md:text-7xl">
                {!pipeline
                  ? "The research pipeline is unavailable."
                  : candidates.length === 0
                    ? "No watched security could be researched this cycle."
                    : `${candidates.length} watched ${
                        candidates.length === 1 ? "security" : "securities"
                      }, researched.`}
              </h1>

              {pipeline ? (
                <StatusPill status="partial" label="Artificial CIO" />
              ) : (
                <StatusPill status="placeholder" label="Not connected" />
              )}
            </div>

            <p className="mt-7 max-w-3xl text-base leading-7 text-neutral-600 md:text-lg">
              Every candidate comes from your own watchlists and is judged on
              evidence about the security itself. Nothing that was judged is
              hidden, and nothing that could not be evidenced is invented.
            </p>
          </div>

          <aside className="rounded-3xl border border-neutral-200 bg-white p-7 shadow-sm">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-500">
                Artificial CIO
              </p>

              <h2 className="mt-2 font-serif text-3xl text-neutral-950">
                Research, not buy-ready
              </h2>
            </div>

            <p className="mt-5 text-sm leading-6 text-neutral-600">
              {funnel && funnel.actionable > 0
                ? `${funnel.actionable} of these reached a decision that asks for your attention.`
                : "None of these reached a decision that asks you to act."}
            </p>

            <div className="mt-7 grid grid-cols-2 gap-3">
              <Metric
                label="Watched, not held"
                value={String(funnel?.candidates ?? 0)}
              />
              <Metric
                label="Reviewed this cycle"
                value={String(funnel?.reviewed ?? 0)}
              />
              <Metric label="Judged" value={String(funnel?.judged ?? 0)} />
              <Metric
                label="Highest conviction"
                value={candidates.length > 0 ? `${highestConviction}%` : "—"}
              />
            </div>
          </aside>
        </section>

        {funnel ? (
          <section className="border-b border-neutral-200 py-12">
            <div className="mb-7">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-800">
                Screening funnel
              </p>

              <h2 className="mt-2 font-serif text-4xl tracking-[-0.04em] text-neutral-950">
                How this cycle narrowed the list
              </h2>
            </div>

            <Funnel funnel={funnel} />

            <p className="mt-5 max-w-4xl text-sm leading-6 text-neutral-600">
              {funnel.notReviewed > 0
                ? `${funnel.notReviewed} watched ${
                    funnel.notReviewed === 1 ? "security was" : "securities were"
                  } not reviewed this cycle: each review costs a fundamentals request against a rate-limited provider, so the pipeline covers a capped number at a time and says so. `
                : "Every watched security was reviewed this cycle. "}

              {funnel.unevidenced > 0
                ? `${funnel.unevidenced} could not be described on ${
                    funnel.unevidenced === 1 ? "its" : "their"
                  } own evidence, and ${
                    funnel.unevidenced === 1 ? "was" : "were"
                  } therefore not judged — a verdict without security-level evidence would only be describing your portfolio.`
                : ""}
            </p>
          </section>
        ) : null}

        <section className="py-12">
          <div className="mb-8 flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
            <div>
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-800">
                <Binoculars className="h-4 w-4" />
                Ranked by conviction
              </div>

              <h2 className="mt-2 font-serif text-4xl tracking-[-0.04em] text-neutral-950">
                All research candidates
              </h2>
            </div>

            <p className="max-w-md text-sm leading-6 text-neutral-500">
              Ranking prioritizes research work. Every candidate the Artificial
              CIO judged is listed, including the ones it rejected.
            </p>
          </div>

          {candidates.length === 0 ? (
            <p className="rounded-2xl border border-neutral-200 bg-neutral-50 p-6 text-sm leading-6 text-neutral-600">
              {pipeline
                ? "No watched security could be described on its own evidence this cycle, so the Artificial CIO judged none of them."
                : `The research pipeline could not be loaded from ${result.backendUrl}.`}
            </p>
          ) : (
            <div className="space-y-5">
              {candidates.map((candidate) => (
                <CandidateCard candidate={candidate} key={candidate.symbol} />
              ))}
            </div>
          )}

          <div className="mt-8 flex items-start gap-4 rounded-2xl border border-neutral-200 bg-neutral-50 p-6">
            <Search className="mt-1 h-5 w-5 text-emerald-800" />

            <div>
              <h3 className="font-semibold text-neutral-950">
                A candidate is not a recommendation
              </h3>

              <p className="mt-2 max-w-4xl text-sm leading-6 text-neutral-600">
                Reaching INVESTIGATE or PREPARE means the company deserves
                further work. It does not mean valuation, risk, evidence
                quality and portfolio fit are sufficient to deploy capital —
                only RECOMMEND means that.
              </p>
            </div>
          </div>
        </section>
      </main>
    </DashboardLayout>
  );
}
