import {
  Binoculars,
  ChevronDown,
  CircleAlert,
  Search,
  Sparkles,
  TrendingUp,
} from "lucide-react";

import { DecisionCard } from "@/components/decisions/DecisionCard";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { StatusPill } from "@/components/ui/StatusPill";
import { PageIntegrity } from "@/components/system-integrity/PageIntegrity";
import { getResearchPipeline } from "@/lib/api/research";
import type {
  ResearchCandidateViewModel,
  ResearchFunnelViewModel,
  WatchedCandidateViewModel,
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

/**
 * A roll of watched securities, folded away until it is asked for.
 *
 * Sixty-odd symbols that nobody looked at is a footnote, not a section:
 * printed open it was most of the page, and the twelve securities the
 * cycle actually judged were somewhere underneath it. Folded, it still
 * names every one — a security silently absent reads as
 * considered-and-dismissed, which is a different claim from "nobody
 * looked".
 */
function WatchedRoll({
  title,
  explanation,
  candidates,
  tone,
}: {
  title: string;
  explanation: string;
  candidates: readonly WatchedCandidateViewModel[];
  tone: "amber" | "neutral";
}) {
  if (candidates.length === 0) {
    return null;
  }

  const amber = tone === "amber";

  return (
    <details
      className={`group overflow-hidden rounded-2xl border ${
        amber
          ? "border-amber-200 bg-amber-50/80"
          : "border-neutral-200 bg-neutral-50"
      }`}
    >
      <summary className="flex cursor-pointer list-none items-center justify-between gap-4 p-5">
        <span className="flex items-center gap-2">
          {amber ? <CircleAlert className="h-4 w-4 text-amber-900" /> : null}

          <span
            className={`text-xs font-bold uppercase tracking-[0.15em] ${
              amber ? "text-amber-900" : "text-neutral-600"
            }`}
          >
            {title}
          </span>

          <span
            className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${
              amber
                ? "bg-amber-200/70 text-amber-900"
                : "bg-neutral-200 text-neutral-700"
            }`}
          >
            {candidates.length}
          </span>
        </span>

        <ChevronDown
          aria-hidden="true"
          className={`h-4 w-4 shrink-0 transition group-open:rotate-180 ${
            amber ? "text-amber-800" : "text-neutral-500"
          }`}
        />
      </summary>

      <div className="px-5 pb-5">
        <p
          className={`text-sm leading-6 ${
            amber ? "text-amber-950" : "text-neutral-600"
          }`}
        >
          {explanation}
        </p>

        <ul className="mt-4 grid gap-x-8 gap-y-2 sm:grid-cols-2 xl:grid-cols-3">
          {candidates.map((candidate) => (
            <li
              className={`flex flex-wrap items-baseline gap-x-2 text-sm ${
                amber ? "text-amber-950" : "text-neutral-800"
              }`}
              key={candidate.symbol}
            >
              <span className="font-semibold">{candidate.symbol}</span>
              <span>{candidate.name}</span>
            </li>
          ))}
        </ul>
      </div>
    </details>
  );
}

function CandidateCard({
  candidate,
}: {
  candidate: ResearchCandidateViewModel;
}) {
  return (
    <DecisionCard
      rank={candidate.rank}
      symbol={candidate.symbol}
      name={candidate.name}
      decisionState={candidate.recommendation}
      conviction={candidate.conviction}
      convictionLabel={candidate.convictionLabel}
      tags={candidate.source ? [candidate.source] : []}
      trend={candidate.trend}
      reviewHref={candidate.dossierHref}
    >
      <Lifecycle state={candidate.recommendation} />

      {/* The card ends here until it is asked to go on. Twelve candidates
          printed whole is a page nobody scans: the identity, the state and
          the conviction are what the eye compares between securities, and
          the reasoning underneath is what it reads about one of them. */}
      <details className="group/case mt-6">
        <summary className="flex cursor-pointer list-none items-center gap-2 text-sm font-semibold text-neutral-600 transition hover:text-neutral-950">
          <ChevronDown
            aria-hidden="true"
            className="h-4 w-4 transition group-open/case:rotate-180"
          />

          <span className="group-open/case:hidden">Why this verdict</span>
          <span className="hidden group-open/case:inline">Hide the reasoning</span>
        </summary>

      <div className="mt-7 grid gap-4 border-y border-neutral-200 py-6 lg:grid-cols-2">
        {candidate.evidenceWeighed.length > 0 ? (
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50/70 p-5">
            <h4 className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.15em] text-emerald-900">
              <TrendingUp className="h-4 w-4" />
              Evidence weighed
            </h4>

            {/* How old these readings are. A judgement is exactly as
                current as the facts under it, and the investor could
                not previously tell whether they were minutes or a day
                old. */}
            {candidate.evidenceAsOf ? (
              <p className="mt-1 text-xs font-medium text-emerald-800">
                {candidate.evidenceAsOf}
              </p>
            ) : null}

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

      {/* Every score here is about this security, and every one runs the
          same way: higher is better for the case. Safety comes from its
          own price history, and fit from the room this portfolio has for
          it under the investor's own policy — see the evidence above for
          the numbers behind them. */}
      <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Score label="Quality" value={candidate.qualityScore} />
        <Score label="Valuation" value={candidate.valuationScore} />
        <Score label="Safety" value={candidate.safetyScore} />
        <Score
          label="Fit with your portfolio"
          value={candidate.portfolioFitScore}
        />
      </div>

      <div className="mt-3">
        <Metric label="Evidence" value={String(candidate.evidenceScore)} />
      </div>

        <ReasonList title="Still missing" reasons={candidate.missingEvidence} />
        <ReasonList title="Catalysts" reasons={candidate.catalysts} />

        {candidate.nextTrigger ? (
          <p className="mt-6 text-sm leading-6 text-neutral-700">
            <span className="font-semibold">Next trigger:</span>{" "}
            {candidate.nextTrigger}
          </p>
        ) : null}

        <p className="mt-6 text-xs text-neutral-500">
          Research candidate only. No capital deployment is currently
          recommended.
        </p>
      </details>
    </DecisionCard>
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
                <StatusPill
                  status="partial"
                  label="Artificial CIO"
                  explanation="Partial, honestly: every candidate is judged on real per-security evidence, but each cycle reviews a capped number of them, and no upside, price target or sector is estimated."
                />
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

          {/* The rest of the watchlist, after the securities that were
              actually judged rather than before them. */}
          {pipeline ? (
            <div className="mt-8 space-y-4">
              <WatchedRoll
                title="Reviewed, but nothing could be evidenced"
                tone="amber"
                candidates={pipeline.unevidenced}
                explanation="A fundamentals request was spent on each of these, and no evidence came back. They were deliberately not judged — a verdict without security-level evidence would only be describing your portfolio."
              />

              <WatchedRoll
                title="Not reviewed this cycle"
                tone="neutral"
                candidates={pipeline.notReviewed}
                explanation="Each review costs a request against a rate-limited provider, so a cycle covers a capped number of securities. These were outside this cycle's budget — nobody looked, and nothing was decided about them."
              />
            </div>
          ) : null}

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
