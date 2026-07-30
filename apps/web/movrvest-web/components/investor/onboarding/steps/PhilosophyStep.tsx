import { ContinueButton } from "../ContinueButton";
import { OnboardingLayout } from "../OnboardingLayout";

type Props = {
  onBack: () => void;
  onContinue: () => void;
};

const PHILOSOPHY_ITEMS = [
  {
    title: "Market volatility",
    description:
      "Temporary declines are acceptable when the long-term investment thesis remains intact.",
  },
  {
    title: "Investment horizon",
    description:
      "Capital should generally be invested with a multi-year perspective rather than for short-term speculation.",
  },
  {
    title: "Portfolio quality",
    description:
      "Preference should be given to financially resilient businesses with durable competitive advantages.",
  },
  {
    title: "Diversification",
    description:
      "Concentration may be appropriate when conviction is high, but individual risks should remain controlled.",
  },
  {
    title: "Crypto assets",
    description:
      "Crypto may be considered as a higher-risk allocation within clearly defined portfolio limits.",
  },
  {
    title: "Investor control",
    description:
      "The Artificial CIO provides recommendations and reasoning, while the investor retains final authority.",
  },
];

export function StepPhilosophy({
  onBack,
  onContinue,
}: Props) {
  return (
    <OnboardingLayout
      eyebrow="Investment philosophy"
      title="How should your Artificial CIO think?"
      description="These principles will guide how MOVRvest evaluates opportunities, risk and portfolio decisions."
    >
      <div className="grid gap-4 lg:grid-cols-2">
        {PHILOSOPHY_ITEMS.map((item) => (
          <button
            key={item.title}
            type="button"
            className="rounded-2xl border border-slate-200 bg-white p-6 text-left shadow-sm transition hover:border-slate-400 hover:shadow-md"
          >
            <h3 className="text-lg font-semibold text-slate-950">
              {item.title}
            </h3>

            <p className="mt-2 leading-7 text-slate-600">
              {item.description}
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
          label="Create my investment policy →"
          onClick={onContinue}
        />
      </div>
    </OnboardingLayout>
  );
}
