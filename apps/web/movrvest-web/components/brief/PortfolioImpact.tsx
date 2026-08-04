import { StatusDot } from "@/components/ui/StatusDot";
import type { PortfolioImpactView } from "@/types/executive-brief";

type PortfolioImpactProps = {
  impact: PortfolioImpactView;
};

const metrics = [
  {
    label: "Current allocation",
    key: "currentAllocation",
    caption: "Below policy target",
  },
  {
    label: "Suggested allocation",
    key: "suggestedAllocation",
    caption: "Within target range",
  },
  {
    label: "Cash required",
    key: "cashRequired",
    caption: "To reach suggestion",
  },
  {
    label: "Policy status",
    key: "policyStatus",
    caption: "Within all limits",
  },
] as const;

export function PortfolioImpact({ impact }: PortfolioImpactProps) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex gap-4">
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-emerald-50 text-sm font-bold text-emerald-800">
          PI
        </span>

        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-xl font-semibold tracking-tight text-slate-950">
              Portfolio Impact
            </h2>

            <StatusDot status="partial" />
          </div>

          <p className="mt-1 text-sm leading-6 text-slate-500">
            This is how the opportunity would affect your portfolio and policy.
          </p>
        </div>
      </div>

      <dl className="mt-7 grid gap-6 sm:grid-cols-2 lg:grid-cols-4 lg:gap-0">
        {metrics.map((metric, index) => (
          <div
            key={metric.key}
            className={
              index === 0
                ? ""
                : "lg:border-l lg:border-slate-200 lg:pl-6"
            }
          >
            <dt className="text-xs font-medium text-slate-500">
              {metric.label}
            </dt>

            <dd
              className={`mt-3 text-2xl font-semibold tracking-tight ${
                metric.key === "policyStatus"
                  ? "text-emerald-700"
                  : "text-slate-950"
              }`}
            >
              {impact[metric.key]}
            </dd>

            <p className="mt-2 text-xs leading-5 text-slate-500">
              {metric.caption}
            </p>
          </div>
        ))}
      </dl>
    </section>
  );
}
