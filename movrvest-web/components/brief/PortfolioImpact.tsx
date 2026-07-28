import type { PortfolioImpactView } from "@/types/executive-brief";

type PortfolioImpactProps = {
  impact: PortfolioImpactView;
};

const metrics = [
  {
    label: "Current allocation",
    key: "currentAllocation",
  },
  {
    label: "Suggested allocation",
    key: "suggestedAllocation",
  },
  {
    label: "Cash required",
    key: "cashRequired",
  },
  {
    label: "Policy status",
    key: "policyStatus",
  },
] as const;

export function PortfolioImpact({
  impact,
}: PortfolioImpactProps) {
  return (
    <section className="border-t border-slate-200 py-12">
      <h2 className="text-2xl font-semibold tracking-tight text-slate-900">
        Portfolio Impact
      </h2>

      <p className="mt-3 max-w-2xl text-base leading-7 text-slate-600">
        This is how the opportunity would affect your current portfolio and
        investment policy.
      </p>

      <dl className="mt-8 grid gap-px overflow-hidden rounded-2xl border border-slate-200 bg-slate-200 sm:grid-cols-2">
        {metrics.map((metric) => (
          <div
            key={metric.key}
            className="bg-white p-5"
          >
            <dt className="text-sm font-medium text-slate-500">
              {metric.label}
            </dt>

            <dd className="mt-2 text-xl font-semibold tracking-tight text-slate-900">
              {impact[metric.key]}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
