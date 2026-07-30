import { ContinueButton } from "../ContinueButton";
import { OnboardingLayout } from "../OnboardingLayout";

type Props = {
  onBack: () => void;
  onContinue: () => void;
};

const HYPOTHESES = [
  {
    title: "You may prefer long-term investing",
    confidence: 78,
    description:
      "Your historical activity suggests selective investing rather than frequent short-term trading.",
  },
  {
    title: "You may value capital preservation",
    confidence: 64,
    description:
      "Your current fully liquid position may reflect caution, transition or preparation for a new strategy.",
  },
  {
    title: "Your future portfolio may differ from your historical portfolio",
    confidence: 85,
    description:
      "Past behaviour is useful evidence, but it does not necessarily represent your current objectives.",
  },
];

export function StepHypotheses({
  onBack,
  onContinue,
}: Props) {
  return (
    <OnboardingLayout
      eyebrow="Investor understanding"
      title="Do these hypotheses reflect how you think?"
      description="These are tentative interpretations based on your investment history. Confirming or correcting them helps your Artificial CIO understand you more accurately."
    >
      <div className="space-y-4">
        {HYPOTHESES.map((hypothesis) => (
          <div
            key={hypothesis.title}
            className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
          >
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h3 className="text-lg font-semibold text-slate-950">
                  {hypothesis.title}
                </h3>

                <p className="mt-2 max-w-3xl leading-7 text-slate-600">
                  {hypothesis.description}
                </p>
              </div>

              <span className="shrink-0 rounded-full bg-violet-100 px-3 py-1 text-sm font-semibold text-violet-700">
                {hypothesis.confidence}% confidence
              </span>
            </div>

            <div className="mt-6 flex flex-wrap gap-3">
              <button
                type="button"
                className="rounded-xl bg-slate-950 px-4 py-2 font-medium text-white transition hover:bg-slate-800"
              >
                Agree
              </button>

              <button
                type="button"
                className="rounded-xl border border-slate-300 bg-white px-4 py-2 font-medium text-slate-700 transition hover:bg-slate-50"
              >
                Partially
              </button>

              <button
                type="button"
                className="rounded-xl border border-slate-300 bg-white px-4 py-2 font-medium text-slate-700 transition hover:bg-slate-50"
              >
                Disagree
              </button>
            </div>
          </div>
        ))}
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
          label="Define my goals →"
          onClick={onContinue}
        />
      </div>
    </OnboardingLayout>
  );
}
