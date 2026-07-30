import { ContinueButton } from "../ContinueButton";
import { OnboardingLayout } from "../OnboardingLayout";

type Props = {
  onBack: () => void;
  onContinue: () => void;
};

const GOALS = [
  {
    title: "Build long-term wealth",
    description:
      "Grow capital steadily over many years through disciplined investing.",
  },
  {
    title: "Reach financial independence",
    description:
      "Build enough invested assets to increase freedom and reduce dependence on active income.",
  },
  {
    title: "Prepare for retirement",
    description:
      "Create a resilient portfolio designed to support future retirement needs.",
  },
  {
    title: "Preserve capital",
    description:
      "Protect purchasing power while limiting the risk of permanent loss.",
  },
  {
    title: "Fund a future project",
    description:
      "Invest toward a major purchase, property, business or personal objective.",
  },
  {
    title: "I am still defining my goal",
    description:
      "Let MOVRvest help clarify the objective before proposing a strategy.",
  },
];

export function StepGoals({
  onBack,
  onContinue,
}: Props) {
  return (
    <OnboardingLayout
      eyebrow="Investment goals"
      title="What should your portfolio help you achieve?"
      description="Your current portfolio is only the starting point. Your objectives define the destination."
    >
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {GOALS.map((goal) => (
          <button
            key={goal.title}
            type="button"
            className="rounded-2xl border border-slate-200 bg-white p-6 text-left shadow-sm transition hover:border-slate-400 hover:shadow-md"
          >
            <h3 className="text-lg font-semibold text-slate-950">
              {goal.title}
            </h3>

            <p className="mt-2 leading-7 text-slate-600">
              {goal.description}
            </p>
          </button>
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
          label="Define my investment philosophy →"
          onClick={onContinue}
        />
      </div>
    </OnboardingLayout>
  );
}
