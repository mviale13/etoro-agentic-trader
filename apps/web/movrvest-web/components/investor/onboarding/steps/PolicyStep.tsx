import { ContinueButton } from "../ContinueButton";
import { OnboardingLayout } from "../OnboardingLayout";

type Props = {
  onBack: () => void;
  onContinue: () => void;
};

const POLICY_SECTIONS = [
  {
    title: "Primary objective",
    value: "Build long-term wealth",
    description:
      "The portfolio should prioritize sustainable capital growth over short-term speculation.",
  },
  {
    title: "Investment horizon",
    value: "10+ years",
    description:
      "Short-term volatility is acceptable when the long-term thesis remains intact.",
  },
  {
    title: "Risk posture",
    value: "Growth-oriented",
    description:
      "The portfolio may accept meaningful volatility while avoiding unnecessary concentration and permanent loss risk.",
  },
  {
    title: "Liquidity",
    value: "Maintain flexibility",
    description:
      "A cash reserve should remain available for opportunities and unexpected needs.",
  },
  {
    title: "Preferred characteristics",
    value: "Quality and durable growth",
    description:
      "Preference for resilient companies with strong fundamentals, competitive advantages and disciplined capital allocation.",
  },
  {
    title: "Higher-risk assets",
    value: "Allowed within limits",
    description:
      "Crypto and other higher-risk opportunities may be included only within clearly defined allocation boundaries.",
  },
];

export function StepPolicy({
  onBack,
  onContinue,
}: Props) {
  return (
    <OnboardingLayout
      eyebrow="Executive investment policy"
      title="Here is the mandate for your Artificial CIO"
      description="This policy summarizes the objectives and principles that should guide future recommendations."
    >
      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
        <div className="grid gap-6 lg:grid-cols-2">
          {POLICY_SECTIONS.map((section) => (
            <div
              key={section.title}
              className="rounded-2xl border border-slate-200 bg-slate-50 p-6"
            >
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
                {section.title}
              </p>

              <h3 className="mt-3 text-xl font-semibold text-slate-950">
                {section.value}
              </h3>

              <p className="mt-2 leading-7 text-slate-600">
                {section.description}
              </p>
            </div>
          ))}
        </div>

        <div className="mt-8 rounded-2xl border border-blue-200 bg-blue-50 p-6">
          <p className="font-semibold text-slate-950">
            Your policy will evolve with you.
          </p>

          <p className="mt-2 leading-7 text-slate-700">
            MOVRvest will continue learning from your decisions, but any future
            change to this mandate should remain transparent and under your
            control.
          </p>
        </div>
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
          label="Activate my Artificial CIO →"
          onClick={onContinue}
        />
      </div>
    </OnboardingLayout>
  );
}
