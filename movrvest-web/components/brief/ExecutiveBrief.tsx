import type { ExecutiveBriefViewModel } from "@/types/executive-brief";

import { CommitteeConsensus } from "./CommitteeConsensus";
import { EvidenceSection } from "./EvidenceSection";
import { ExecutiveAssessment } from "./ExecutiveAssessment";
import { PortfolioImpact } from "./PortfolioImpact";
import { RiskSection } from "./RiskSection";
import { WhyThisBrief } from "./WhyThisBrief";

type ExecutiveBriefProps = {
  brief: ExecutiveBriefViewModel;
};

function MicrosoftMark() {
  return (
    <div
      aria-hidden="true"
      className="grid h-14 w-14 shrink-0 grid-cols-2 gap-1"
    >
      <span className="bg-red-500" />
      <span className="bg-lime-500" />
      <span className="bg-sky-500" />
      <span className="bg-amber-400" />
    </div>
  );
}

export function ExecutiveBrief({ brief }: ExecutiveBriefProps) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <main className="mx-auto w-[90vw] max-w-none py-8">
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-emerald-50 text-xs font-bold text-emerald-800">
              M
            </span>

            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-700">
              Executive Brief
            </p>
          </div>

          <p className="text-xs text-slate-500">
            {brief.generatedAt}
            <span className="mx-2">•</span>
            {brief.readingTime}
          </p>
        </div>

        <header className="grid gap-5 lg:grid-cols-[3fr_1fr]">
          <section className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm sm:p-9">
            <div className="flex items-center gap-6">
              <MicrosoftMark />

              <div>
                <h1 className="text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl lg:text-5xl">
                  {brief.companyName}
                </h1>

                <p className="mt-3 text-base text-slate-500 sm:text-lg">
                  {brief.symbol}
                  <span className="mx-2">•</span>
                  {brief.sector}
                </p>
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm sm:p-8">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Executive Score
            </p>

            <p className="mt-3 text-6xl font-semibold tracking-tight text-emerald-700">
              {brief.executiveScore}
            </p>

            <p className="mt-4 inline-flex rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-800">
              {brief.attentionLabel}
            </p>
          </section>
        </header>

        <div className="mt-6 grid items-start gap-6 lg:grid-cols-[1.15fr_0.85fr]">
          <div className="space-y-6">
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
              <div className="flex gap-4">
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-emerald-50 text-lg text-emerald-800">
                  ≡
                </span>

                <div className="min-w-0 flex-1">
                  <h2 className="text-xl font-semibold tracking-tight text-slate-950">
                    Executive Summary
                  </h2>

                  <p className="mt-3 text-sm leading-7 text-slate-700 sm:text-base">
                    {brief.executiveSummary}
                  </p>

                  <div className="mt-8">
                    <WhyThisBrief reasons={brief.whyNow} />
                  </div>
                </div>
              </div>
            </section>

            <PortfolioImpact impact={brief.portfolioImpact} />

            <RiskSection risks={brief.risks} />
          </div>

          <div className="space-y-6">
            <CommitteeConsensus committees={brief.committees} />

            <EvidenceSection evidence={brief.evidence} />

            <ExecutiveAssessment assessment={brief.executiveAssessment} />
          </div>
        </div>

        <footer className="py-8 text-center">
          <p className="text-xs leading-5 text-slate-500">
            This brief is provided for informational purposes and does not
            constitute financial advice. Final investment decisions remain
            yours.
          </p>
        </footer>
      </main>
    </div>
  );
}
