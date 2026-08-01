import Link from "next/link";

import { InvestmentPolicyForm } from "@/components/strategy/InvestmentPolicyForm";
import {
  getStrategy,
  getStrategyReadiness,
} from "@/lib/strategy-api";
import { StatusPill } from "@/components/ui/StatusPill";

export default async function StrategyPage() {
  const strategy = await getStrategy();
  const readiness =
    await getStrategyReadiness();

  return (
    <main className="mx-auto max-w-4xl p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-3xl font-bold">
              Investment Policy
            </h1>

            {/* The policy is read from and written to the backend. */}
            <StatusPill status="live" label="Live policy" />
          </div>

          <p className="mt-2 text-slate-400">
            Define how MOVRvest should evaluate your
            portfolio, opportunities and risks.
          </p>
        </div>

        <Link
          href="/"
          className="rounded-lg border border-slate-700 px-4 py-2"
        >
          ← Dashboard
        </Link>
      </div>

      <div
        className={
          readiness.status === "ready"
            ? "mb-8 rounded-xl border border-green-500/30 bg-green-500/10 p-5"
            : "mb-8 rounded-xl border border-amber-500/30 bg-amber-500/10 p-5"
        }
      >
        <p className="font-semibold">
          {readiness.status === "ready"
            ? "🟢 Investment Policy ready"
            : "🟡 Investment Policy incomplete"}
        </p>

        <p className="mt-2 text-sm text-slate-300">
          {readiness.message}
        </p>
      </div>

      <InvestmentPolicyForm
        initialStrategy={strategy}
      />
    </main>
  );
}
