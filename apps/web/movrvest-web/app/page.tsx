import { ExecutiveWorkspaceBriefing } from "@/components/executive/ExecutiveWorkspaceBriefing";
import { TopInvestmentCases } from "@/components/executive/TopInvestmentCases";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { getExecutiveWorkspace } from "@/lib/api/executive-workspace";
import { PageIntegrity } from "@/components/system-integrity/PageIntegrity";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const result = await getExecutiveWorkspace();

  return (
    <DashboardLayout>
      <PageIntegrity
        status={result.source === "backend" ? "partial" : "placeholder"}
        endpoint={
          result.source === "backend"
            ? "/brain/ + /executive/portfolio"
            : undefined
        }
        description={
          result.source === "backend"
            ? "Portfolio, executive decisions and market movements — mood, volatility and sentiment — are live in the change feed. Individual instrument moves are not tracked yet."
            : "Backend unreachable. Nothing is shown in its place: an invented figure on an investment surface would read as a measurement."
        }
      />

      <main className="mx-auto w-full max-w-[1600px] px-5 py-8 sm:px-8 lg:px-10 lg:py-12">
        {result.workspace ? (
          <ExecutiveWorkspaceBriefing workspace={result.workspace} />
        ) : (
          <section className="rounded-[28px] border border-amber-200 bg-amber-50 px-8 py-10">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-amber-700">
              Overview
            </p>

            <h1 className="mt-3 text-3xl font-semibold tracking-[-0.035em] text-amber-950">
              The backend is unreachable
            </h1>

            <p className="mt-4 max-w-2xl text-sm leading-6 text-amber-900">
              MOVRvest cannot currently read your account, so nothing is shown.
              No demo figures stand in for real ones: with the backend away,
              this page knows nothing about your portfolio, and says so.
            </p>

            <p className="mt-6 text-sm text-amber-900">
              Tried:
              <code className="ml-2 rounded bg-white/70 px-1.5 py-0.5">
                {result.backendUrl}
              </code>
            </p>

            {result.error ? (
              <details className="mt-4 text-sm text-amber-900">
                <summary className="cursor-pointer font-semibold">
                  Connection details
                </summary>

                <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-xs leading-5">
                  {result.error}
                </pre>
              </details>
            ) : null}
          </section>
        )}

        {result.workspace ? (
          <div className="mt-20 border-t border-slate-200 pt-14">
            <TopInvestmentCases cases={result.investmentCases} />
          </div>
        ) : null}
      </main>
    </DashboardLayout>
  );
}
