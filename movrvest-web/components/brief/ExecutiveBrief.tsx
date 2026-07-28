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

export function ExecutiveBrief({
  brief,
}: ExecutiveBriefProps) {
  return (
    <main className="mx-auto max-w-5xl px-8 py-12">
      <header className="border-b border-slate-200 pb-10">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">
          Executive Brief
        </p>

        <h1 className="mt-4 text-4xl font-semibold tracking-tight text-slate-900">
          {brief.companyName}
        </h1>

        <p className="mt-2 text-lg text-slate-500">
          {brief.symbol} • {brief.sector}
        </p>

        <div className="mt-10">
          <p className="text-sm uppercase tracking-wide text-slate-500">
            Executive Score
          </p>

          <p className="mt-2 text-6xl font-semibold tracking-tight text-slate-900">
            {brief.executiveScore}
          </p>

          <p className="mt-3 text-base text-slate-600">
            {brief.attentionLabel}
          </p>

          <p className="mt-2 text-sm text-slate-500">
            {brief.readingTime} • {brief.generatedAt}
          </p>
        </div>
      </header>

      <section className="py-12">
        <h2 className="text-2xl font-semibold tracking-tight text-slate-900">
          Executive Summary
        </h2>

        <p className="mt-6 max-w-3xl text-lg leading-9 text-slate-700">
          {brief.executiveSummary}
        </p>
      </section>

      <WhyThisBrief reasons={brief.whyNow} />

      <CommitteeConsensus committees={brief.committees} />

      <PortfolioImpact impact={brief.portfolioImpact} />

      <EvidenceSection evidence={brief.evidence} />

      <RiskSection risks={brief.risks} />

      <ExecutiveAssessment assessment={brief.executiveAssessment} />
    </main>
  );
}
