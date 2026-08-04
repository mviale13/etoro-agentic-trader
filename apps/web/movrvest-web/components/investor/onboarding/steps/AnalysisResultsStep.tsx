import { mockInvestorAnalysis } from "@/lib/investor/mockAnalysis";

import { ContinueButton } from "../ContinueButton";
import { OnboardingLayout } from "../OnboardingLayout";
import { FactCard } from "../cards/FactCard";
import { HypothesisCard } from "../cards/HypothesisCard";
import { ObservationCard } from "../cards/ObservationCard";

type Props = {
  onBack: () => void;
  onContinue: () => void;
};

export function AnalysisResultsStep({
  onBack,
  onContinue,
}: Props) {
  const { facts, observations, hypotheses } = mockInvestorAnalysis;

  return (
    <OnboardingLayout
      eyebrow="Portfolio review"
      title="I've reviewed your investment history"
      description="Before discussing what you want to achieve, here is what I can establish from your current portfolio and historical activity."
    >
      <section>
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-slate-500">
            Facts
          </p>

          <p className="mt-2 max-w-3xl text-slate-600">
            These are objective data points. They do not require interpretation
            or confirmation.
          </p>
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {facts.map((fact) => (
            <FactCard
              key={fact.id}
              label={fact.title}
              value={fact.value}
            />
          ))}
        </div>
      </section>

      <section className="mt-14">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-blue-600">
            Observations
          </p>

          <p className="mt-2 max-w-3xl text-slate-600">
            These are conclusions directly supported by the portfolio data.
          </p>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-3">
          {observations.map((observation) => (
            <ObservationCard
              key={observation.id}
              title={observation.title}
              description={observation.description}
            />
          ))}
        </div>
      </section>

      <section className="mt-14">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-violet-600">
            Initial hypotheses
          </p>

          <p className="mt-2 max-w-3xl text-slate-600">
            These are tentative interpretations, not conclusions. You will be
            able to confirm, refine or reject them.
          </p>
        </div>

        <div className="mt-6 grid gap-4 xl:grid-cols-3">
          {hypotheses.map((hypothesis) => (
            <HypothesisCard
              key={hypothesis.id}
              title={hypothesis.title}
              confidence={hypothesis.confidence}
              evidence={hypothesis.evidence}
            />
          ))}
        </div>
      </section>

      <div className="mt-14 rounded-2xl border border-amber-200 bg-amber-50 p-6">
        <p className="font-semibold text-slate-900">
          Historical behaviour is evidence, not intent.
        </p>

        <p className="mt-2 max-w-4xl leading-7 text-slate-700">
          Your current portfolio and previous transactions do not necessarily
          represent the portfolio you want. MOVRvest will use them as context,
          then ask about your objectives before making any recommendation.
        </p>
      </div>

      <div className="mt-10 flex flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-between">
        <button
          type="button"
          onClick={onBack}
          className="rounded-xl border border-slate-300 bg-white px-6 py-4 font-medium text-slate-700 transition hover:border-slate-400 hover:bg-slate-50"
        >
          ← Back
        </button>

        <ContinueButton
          label="Help me understand your goals →"
          onClick={onContinue}
        />
      </div>
    </OnboardingLayout>
  );
}
