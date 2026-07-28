import Link from "next/link";
import { StrategyReadiness } from "@/lib/strategy-api";
import { Card } from "@/components/ui/Card";

type Props = {
  readiness: StrategyReadiness;
};

const LABELS: Record<string, string> = {
  investor_type: "Investor Type",
  primary_goal: "Primary Goal",
  time_horizon_years: "Time Horizon",
  maximum_acceptable_drawdown_pct: "Maximum Drawdown",
  target_cash_pct: "Target Cash Allocation",
};

export function InvestmentPolicyCard({
  readiness,
}: Props) {
  return (
    <Card>
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">
          🧭 Investment Policy
        </h2>

        <Link
          href="/strategy"
          className="text-sm text-blue-400 hover:underline"
        >
          {readiness.configured ? "Edit" : "Complete"}
        </Link>
      </div>

      {readiness.configured ? (
        <>
          <p className="mt-4 text-green-400">
            🟢 Personalized
          </p>

          <p className="mt-2 text-slate-400">
            Your investment policy is configured.
          </p>
        </>
      ) : (
        <>
          <p className="mt-4 text-amber-400">
            🟡 Generic recommendations
          </p>

          <p className="mt-2 text-slate-400">
            Complete your Investment Policy so the
            Brain can personalize its advice.
          </p>

          <ul className="mt-4 list-disc pl-5 text-sm text-slate-400">
            {readiness.missing_fields.map((field) => (
              <li key={field}>
                {LABELS[field] ?? field}
              </li>
            ))}
          </ul>
        </>
      )}
    </Card>
  );
}
