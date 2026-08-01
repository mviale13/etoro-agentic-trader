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

const BUY_THRESHOLD = 80;

const candidates = [
  {
    symbol: "UUUU",
    company: "Energy Fuels",
    source: "Watchlist",
    sector: "Energy & materials",
    conviction: 71,
    upside: 28,
    quality: 74,
    valuation: 69,
    risk: 64,
    status: "Near threshold",
    thesis:
      "Strategic uranium and rare-earth exposure benefits from energy-security demand and improving commodity momentum.",
    missing:
      "The committee still needs stronger evidence on earnings durability, project execution, and valuation margin of safety.",
    catalyst: "Quarterly operating update",
  },
  {
    symbol: "CND2",
    company: "Quality Compounder",
    source: "Broader market",
    sector: "Industrials",
    conviction: 68,
    upside: 19,
    quality: 82,
    valuation: 58,
    risk: 73,
    status: "Researching",
    thesis:
      "Strong returns on capital and resilient cash generation passed the quality screen and justify deeper research.",
    missing:
      "The current valuation does not provide sufficient protection against slower growth or multiple compression.",
    catalyst: "Full-year results",
  },
  {
    symbol: "CND3",
    company: "Emerging Opportunity",
    source: "Broader market",
    sector: "Technology",
    conviction: 65,
    upside: 24,
    quality: 69,
    valuation: 66,
    risk: 59,
    status: "New",
    thesis:
      "Improving operations and stronger free-cash-flow conversion moved the company above the research threshold.",
    missing:
      "The committee needs confirmation that recent margin expansion is structural rather than temporary.",
    catalyst: "Management guidance update",
  },
];

function Metric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl border border-neutral-200 bg-neutral-50 p-4">
      <span className="block text-xs text-neutral-500">{label}</span>
      <strong className="mt-2 block font-serif text-2xl font-normal text-neutral-950">
        {value}
      </strong>
    </div>
  );
}

export default function ResearchPage() {
  const watchlistCount = candidates.filter(
    (candidate) => candidate.source === "Watchlist",
  ).length;

  const averageUpside = Math.round(
    candidates.reduce((total, candidate) => total + candidate.upside, 0) /
      candidates.length,
  );

  return (
    <DashboardLayout>
      <main className="mx-auto w-[90%] max-w-[1700px] py-10">
        <section className="grid gap-8 border-b border-neutral-200 pb-12 xl:grid-cols-[1.2fr_0.8fr]">
          <div>
            <div className="mb-5 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-emerald-800">
              <Sparkles className="h-4 w-4" />
              Opportunity pipeline
            </div>

            <div className="flex flex-wrap items-center gap-4">
              <h1 className="max-w-5xl font-serif text-5xl leading-[0.98] tracking-[-0.05em] text-neutral-950 md:text-7xl">
                {candidates.length} candidates deserve deeper research.
              </h1>

              {/* Candidates are hardcoded in this page; no scanner feeds it. */}
              <StatusPill status="placeholder" label="Illustrative" />
            </div>

            <p className="mt-7 max-w-3xl text-base leading-7 text-neutral-600 md:text-lg">
              Every company above the research threshold is shown. MOVRvest
              does not impose an arbitrary top-three limit.
            </p>
          </div>

          <aside className="rounded-3xl border border-neutral-200 bg-white p-7 shadow-sm">
            <div className="flex items-start justify-between gap-5">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-500">
                  Artificial CIO
                </p>

                <h2 className="mt-2 font-serif text-3xl text-neutral-950">
                  Research, not buy-ready
                </h2>
              </div>

              <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800">
                Live pipeline
              </span>
            </div>

            <p className="mt-5 text-sm leading-6 text-neutral-600">
              These companies merit investigation, but none currently clears
              the {BUY_THRESHOLD}% buy threshold.
            </p>

            <div className="mt-7 grid grid-cols-2 gap-3">
              <Metric label="Candidates" value={String(candidates.length)} />
              <Metric label="From watchlist" value={String(watchlistCount)} />
              <Metric label="Highest conviction" value="71%" />
              <Metric label="Average upside" value={`+${averageUpside}%`} />
            </div>
          </aside>
        </section>

        <section className="border-b border-neutral-200 py-12">
          <div className="mb-7">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-800">
              Screening funnel
            </p>

            <h2 className="mt-2 font-serif text-4xl tracking-[-0.04em] text-neutral-950">
              How today&apos;s candidates survived
            </h2>
          </div>

          <div className="grid overflow-hidden rounded-2xl border border-neutral-200 bg-white md:grid-cols-5">
            {[
              ["1,284", "Companies screened"],
              ["79", "Watchlist instruments reviewed"],
              ["12", "Passed quality filters"],
              [String(candidates.length), "Exceeded research threshold"],
              ["0", "Currently buy-ready"],
            ].map(([value, label], index) => (
              <div
                className={
                  index === 3
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
                    index === 3
                      ? "mt-2 block text-xs leading-5 text-emerald-100"
                      : "mt-2 block text-xs leading-5 text-neutral-500"
                  }
                >
                  {label}
                </span>
              </div>
            ))}
          </div>
        </section>

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
              Ranking prioritizes research work. It never hides candidates that
              crossed the threshold.
            </p>
          </div>

          <div className="space-y-5">
            {candidates.map((candidate, index) => {
              const gap = BUY_THRESHOLD - candidate.conviction;

              return (
                <article
                  className="overflow-hidden rounded-3xl border border-neutral-200 bg-white shadow-sm"
                  key={candidate.symbol}
                >
                  <div className="grid lg:grid-cols-[92px_1fr]">
                    <div className="border-b border-neutral-200 bg-neutral-50 p-6 lg:border-b-0 lg:border-r">
                      <span className="block text-xs uppercase tracking-widest text-neutral-400">
                        Rank
                      </span>

                      <strong className="mt-2 block font-serif text-3xl font-normal text-emerald-950">
                        {String(index + 1).padStart(2, "0")}
                      </strong>
                    </div>

                    <div className="p-6 md:p-8">
                      <div className="flex flex-col justify-between gap-5 md:flex-row">
                        <div>
                          <div className="flex flex-wrap items-baseline gap-3">
                            <h3 className="font-serif text-3xl tracking-[-0.03em] text-neutral-950">
                              {candidate.company}
                            </h3>

                            <span className="text-xs font-bold tracking-wider text-neutral-500">
                              {candidate.symbol}
                            </span>
                          </div>

                          <div className="mt-3 flex flex-wrap gap-2">
                            {[candidate.sector, candidate.source, candidate.status].map(
                              (tag) => (
                                <span
                                  className="rounded-full border border-neutral-200 px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-neutral-500"
                                  key={tag}
                                >
                                  {tag}
                                </span>
                              ),
                            )}
                          </div>
                        </div>

                        <div className="md:text-right">
                          <strong className="block font-serif text-4xl font-normal text-neutral-950">
                            {candidate.conviction}%
                          </strong>

                          <span className="text-xs text-neutral-500">
                            research conviction
                          </span>
                        </div>
                      </div>

                      <div className="relative mt-7 h-2 rounded-full bg-neutral-200">
                        <div
                          className="h-full rounded-full bg-emerald-800"
                          style={{ width: `${candidate.conviction}%` }}
                        />

                        <div
                          className="absolute -top-1 h-4 w-px bg-red-600"
                          style={{ left: `${BUY_THRESHOLD}%` }}
                        />
                      </div>

                      <div className="mt-3 flex flex-wrap gap-5 text-xs text-neutral-500">
                        <span>Current: {candidate.conviction}%</span>
                        <span>Buy threshold: {BUY_THRESHOLD}%</span>
                        <span>Remaining gap: {gap} points</span>
                      </div>

                      <div className="mt-7 grid gap-4 border-y border-neutral-200 py-6 lg:grid-cols-2">
                        <div className="rounded-2xl border border-emerald-200 bg-emerald-50/70 p-5">
                          <h4 className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.15em] text-emerald-900">
                            <TrendingUp className="h-4 w-4" />
                            Why investigate
                          </h4>

                          <p className="mt-3 text-sm font-medium leading-6 text-emerald-950">
                            {candidate.thesis}
                          </p>
                        </div>

                        <div className="rounded-2xl border border-amber-200 bg-amber-50/80 p-5">
                          <h4 className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.15em] text-amber-900">
                            <CircleAlert className="h-4 w-4" />
                            Why not buy yet
                          </h4>

                          <p className="mt-3 text-sm font-medium leading-6 text-amber-950">
                            {candidate.missing}
                          </p>
                        </div>
                      </div>

                      <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
                        <Metric label="Quality" value={String(candidate.quality)} />
                        <Metric
                          label="Valuation"
                          value={String(candidate.valuation)}
                        />
                        <Metric label="Risk" value={String(candidate.risk)} />
                        <Metric
                          label="Potential upside"
                          value={`+${candidate.upside}%`}
                        />
                        <Metric label="Next catalyst" value={candidate.catalyst} />
                      </div>

                      <div className="mt-7 flex flex-col justify-between gap-4 md:flex-row md:items-center">
                        <p className="text-xs text-neutral-500">
                          Research candidate only. No capital deployment is
                          currently recommended.
                        </p>

                        <Link
                          className="inline-flex items-center justify-center gap-3 rounded-xl bg-emerald-950 px-5 py-3 text-sm font-semibold !text-white shadow-sm transition hover:bg-emerald-800 hover:!text-white"
                          href={`/dossiers/${candidate.symbol}`}
                        >
                          Open investment dossier
                          <ArrowRight className="h-4 w-4" />
                        </Link>
                      </div>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>

          <div className="mt-8 flex items-start gap-4 rounded-2xl border border-neutral-200 bg-neutral-50 p-6">
            <Search className="mt-1 h-5 w-5 text-emerald-800" />

            <div>
              <h3 className="font-semibold text-neutral-950">
                A candidate is not a recommendation
              </h3>

              <p className="mt-2 max-w-4xl text-sm leading-6 text-neutral-600">
                Passing the research threshold means the company deserves
                further investigation. It does not mean valuation, risk,
                evidence quality, expected return, and portfolio fit are
                sufficient to deploy capital.
              </p>
            </div>
          </div>
        </section>
      </main>
    </DashboardLayout>
  );
}
