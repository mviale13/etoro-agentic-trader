import Link from "next/link";

import { Card } from "@/components/ui/Card";
import type {
  StrategyReadiness,
} from "@/lib/strategy-api";

type Props = {
  readiness: StrategyReadiness;
};

const LABELS: Record<string, string> = {
  investor_type: "Investor type",
  primary_goal: "Primary goal",
  time_horizon_years: "Time horizon",
  maximum_acceptable_drawdown_pct:
    "Maximum drawdown",
  target_cash_pct: "Target cash allocation",
};

export function InvestmentPolicyCard({
  readiness,
}: Props) {
  if (readiness.status === "ready") {
    return (
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-semibold">
              🧭 Investment Policy
            </h2>

            <p className="mt-1 text-sm text-green-400">
              🟢 Ready and active
            </p>
          </div>

          <Link
            href="/strategy"
            className="text-sm text-blue-400 hover:underline"
          >
            Edit
          </Link>
        </div>
      </Card>
    );
  }

  if (readiness.status === "incomplete") {
    return (
      <Card>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="font-semibold">
              🧭 Investment Policy
            </h2>

            <p className="mt-1 text-sm text-amber-400">
              🟡 More information needed
            </p>

            <p className="mt-2 text-sm text-slate-400">
              Missing:{" "}
              {readiness.missing_fields
                .map(
                  (field) =>
                    LABELS[field] ?? field,
                )
                .join(", ")}
            </p>
          </div>

          <Link
            href="/strategy"
            className="text-sm text-blue-400 hover:underline"
          >
            Complete
          </Link>
        </div>
      </Card>
    );
  }

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
          Start
        </Link>
      </div>

      <p className="mt-4 text-amber-400">
        🟡 Generic recommendations
      </p>

      <p className="mt-2 text-slate-400">
        Complete your Investment Policy so the Brain
        can personalize its advice.
      </p>
    </Card>
  );
}
