import { InvestmentPolicyForm } from "@/components/strategy/InvestmentPolicyForm";
import {
  getStrategy,
  getStrategyReadiness,
} from "@/lib/strategy-api";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { StatusPill } from "@/components/ui/StatusPill";
import { PageIntegrity } from "@/components/system-integrity/PageIntegrity";

export default async function StrategyPage() {
  // An unreachable backend renders an explicit unavailable state, never a
  // crash and never a stand-in policy.
  let strategy;
  let readiness;

  try {
    strategy = await getStrategy();
    readiness = await getStrategyReadiness();
  } catch (error) {
    return (
      <DashboardLayout>
        <PageIntegrity
          status="placeholder"
          description="Backend unreachable. Nothing is shown in its place."
        />

        <main className="mx-auto w-full max-w-4xl px-5 py-8 sm:px-8 lg:px-10 lg:py-12">
          <section className="rounded-[28px] border border-amber-200 bg-amber-50 px-8 py-10">
            <h1 className="text-3xl font-semibold tracking-[-0.035em] text-amber-950">
              The backend is unreachable
            </h1>

            <p className="mt-4 max-w-2xl text-sm leading-6 text-amber-900">
              MOVRvest cannot currently read your investment policy, so
              nothing is shown. No default policy stands in for yours.
            </p>

            {error instanceof Error ? (
              <details className="mt-4 text-sm text-amber-900">
                <summary className="cursor-pointer font-semibold">
                  Connection details
                </summary>

                <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-xs leading-5">
                  {error.message}
                </pre>
              </details>
            ) : null}
          </section>
        </main>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <PageIntegrity
        status="live"
        endpoint="/strategy"
        description="The investment policy is read from and written to the backend."
      />

      <main className="mx-auto w-full max-w-4xl px-5 py-8 sm:px-8 lg:px-10 lg:py-12">
        <div className="mb-8">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-3xl font-semibold tracking-[-0.035em] text-slate-950">
              Investor Policy
            </h1>

            {/* The policy is read from and written to the backend. */}
            <StatusPill status="live" label="Live policy" />
          </div>

          <p className="mt-2 text-slate-500">
            Define how MOVRvest should evaluate your
            portfolio, opportunities and risks.
          </p>
        </div>

        <div
          className={
            readiness.status === "ready"
              ? "mb-8 rounded-xl border border-emerald-200 bg-emerald-50 p-5"
              : "mb-8 rounded-xl border border-amber-200 bg-amber-50 p-5"
          }
        >
          <p
            className={
              readiness.status === "ready"
                ? "font-semibold text-emerald-900"
                : "font-semibold text-amber-900"
            }
          >
            {readiness.status === "ready"
              ? "Investment Policy ready"
              : "Investment Policy incomplete"}
          </p>

          <p
            className={
              readiness.status === "ready"
                ? "mt-2 text-sm text-emerald-800"
                : "mt-2 text-sm text-amber-800"
            }
          >
            {readiness.message}
          </p>
        </div>

        <InvestmentPolicyForm
          initialStrategy={strategy}
        />
      </main>
    </DashboardLayout>
  );
}
