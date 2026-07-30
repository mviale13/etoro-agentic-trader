import type { ReactNode } from "react";
import {
  ArrowRight,
  Brain,
  Check,
  CircleHelp,
  Clock3,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react";

import { getArtificialCio } from "@/lib/api/artificial-cio";

export const dynamic = "force-dynamic";

export default async function InvestorPage() {
  const result = await getArtificialCio();
  const { cio } = result;

  return (
    <main className="min-h-screen bg-[#f6f7f9] px-5 py-8 text-[#15171a] sm:px-8 lg:px-12">
      <div className="mx-auto w-full max-w-[1500px] space-y-8">
        <header className="flex flex-col gap-6 rounded-[28px] border border-black/5 bg-white p-7 shadow-[0_20px_60px_rgba(0,0,0,0.05)] lg:flex-row lg:items-end lg:justify-between lg:p-10">
          <div className="max-w-4xl">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-black/5 bg-[#f3f4f6] px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.18em] text-black/55">
              <Sparkles className="h-3.5 w-3.5" />
              Investor relationship
            </div>

            <h1 className="text-4xl font-semibold tracking-[-0.045em] sm:text-5xl lg:text-6xl">
              My Artificial CIO
            </h1>

            <p className="mt-5 max-w-3xl text-base leading-7 text-black/55 sm:text-lg">
              Your investment partner learns how you think, understands your
              objectives and explains every recommendation before you decide.
            </p>
          </div>

          <button
            type="button"
            className="inline-flex items-center justify-center gap-2 rounded-full bg-[#17191c] px-5 py-3 text-sm font-semibold text-white transition hover:bg-black"
          >
            Continue the conversation
            <ArrowRight className="h-4 w-4" />
          </button>
        </header>

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            icon={<Brain className="h-5 w-5" />}
            label="Understanding of you"
            value={cio.understanding.value}
            detail={cio.understanding.detail}
          />

          <MetricCard
            icon={<ShieldCheck className="h-5 w-5" />}
            label="Policy confidence"
            value={cio.policyConfidence.value}
            detail={cio.policyConfidence.detail}
          />

          <MetricCard
            icon={<Clock3 className="h-5 w-5" />}
            label="Relationship"
            value={cio.relationship.value}
            detail={cio.relationship.detail}
          />

          <MetricCard
            icon={<CircleHelp className="h-5 w-5" />}
            label="Open questions"
            value={cio.openQuestionCount.value}
            detail={cio.openQuestionCount.detail}
          />
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
          <Panel
            title="Investment policy"
            description="The principles currently guiding your Artificial CIO."
            icon={<Target className="h-5 w-5" />}
          >
            <div className="divide-y divide-black/5">
              {cio.investmentPolicy.map((item) => (
                <PolicyRow
                  key={item.label}
                  label={item.label}
                  value={item.value}
                />
              ))}
            </div>

            <button
              type="button"
              className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-black"
            >
              Review investment policy
              <ArrowRight className="h-4 w-4" />
            </button>
          </Panel>

          <Panel
            title="What I know about you"
            description="Current beliefs based on your preferences and behaviour."
            icon={<Brain className="h-5 w-5" />}
          >
            <div className="space-y-3">
              {cio.knowledgeItems.map((item) => (
                <div
                  key={item}
                  className="flex gap-3 rounded-2xl bg-[#f6f7f8] p-4"
                >
                  <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white shadow-sm">
                    <Check className="h-3.5 w-3.5" />
                  </span>

                  <p className="text-sm leading-6 text-black/70">
                    {item}
                  </p>
                </div>
              ))}
            </div>
          </Panel>
        </section>

        <section className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
          <Panel
            title="Open questions"
            description="Answering these will make future recommendations more personal."
            icon={<CircleHelp className="h-5 w-5" />}
          >
            <div className="space-y-3">
              {cio.openQuestions.map((question, index) => (
                <button
                  key={question}
                  type="button"
                  className="group flex w-full items-center justify-between gap-4 rounded-2xl border border-black/5 bg-white p-4 text-left transition hover:border-black/15 hover:bg-[#fafafa]"
                >
                  <div className="flex items-start gap-3">
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#f1f2f4] text-xs font-semibold">
                      {index + 1}
                    </span>

                    <span className="text-sm font-medium leading-6">
                      {question}
                    </span>
                  </div>

                  <ArrowRight className="h-4 w-4 shrink-0 text-black/30 transition group-hover:translate-x-0.5 group-hover:text-black" />
                </button>
              ))}
            </div>
          </Panel>

          <Panel
            title="Recent learning"
            description="How your Artificial CIO's understanding has evolved."
            icon={<Sparkles className="h-5 w-5" />}
          >
            <div className="space-y-6">
              {cio.recentLearning.map((item, index) => (
                <div
                  key={`${item.title}-${index}`}
                  className="grid gap-3 border-l-2 border-black/10 pl-5 sm:grid-cols-[1fr_auto]"
                >
                  <div>
                    <h3 className="text-sm font-semibold">
                      {item.title}
                    </h3>

                    <p className="mt-1 text-sm leading-6 text-black/55">
                      {item.description}
                    </p>
                  </div>

                  <span className="text-xs font-medium text-black/35">
                    {item.date}
                  </span>
                </div>
              ))}
            </div>
          </Panel>
        </section>

        <div
          className={`rounded-2xl border px-5 py-4 text-sm ${
            result.source === "backend"
              ? "border-emerald-200 bg-emerald-50 text-emerald-900"
              : "border-amber-200 bg-amber-50 text-amber-900"
          }`}
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="font-semibold">
              {result.source === "backend"
                ? "Connected to the MOVRvest Brain"
                : "Using local fallback data"}
            </p>

            <code className="rounded bg-white/60 px-2 py-1 text-xs">
              {result.backendUrl}
            </code>
          </div>

          {result.error ? (
            <details className="mt-3">
              <summary className="cursor-pointer font-medium">
                Connection details
              </summary>

              <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-xs leading-5">
                {result.error}
              </pre>
            </details>
          ) : null}
        </div>
      </div>
    </main>
  );
}

function MetricCard({
  icon,
  label,
  value,
  detail,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <article className="rounded-[24px] border border-black/5 bg-white p-6 shadow-[0_14px_40px_rgba(0,0,0,0.035)]">
      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#f2f3f5]">
        {icon}
      </div>

      <p className="mt-7 text-3xl font-semibold tracking-[-0.04em]">
        {value}
      </p>

      <p className="mt-2 text-sm font-medium">{label}</p>
      <p className="mt-1 text-xs text-black/40">{detail}</p>
    </article>
  );
}

function Panel({
  title,
  description,
  icon,
  children,
}: {
  title: string;
  description: string;
  icon: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="rounded-[28px] border border-black/5 bg-white p-6 shadow-[0_18px_50px_rgba(0,0,0,0.04)] sm:p-8">
      <div className="mb-7 flex items-start gap-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#f2f3f5]">
          {icon}
        </div>

        <div>
          <h2 className="text-xl font-semibold tracking-[-0.025em]">
            {title}
          </h2>

          <p className="mt-1 text-sm leading-6 text-black/45">
            {description}
          </p>
        </div>
      </div>

      {children}
    </section>
  );
}

function PolicyRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="flex flex-col gap-1 py-4 first:pt-0 sm:flex-row sm:items-center sm:justify-between">
      <span className="text-sm text-black/45">{label}</span>
      <span className="text-sm font-semibold">{value}</span>
    </div>
  );
}
