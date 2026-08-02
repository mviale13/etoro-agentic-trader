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
            ? "Portfolio, executive decisions and recorded decision changes are live. The change feed does not yet cover market or macro movements."
            : `Backend unreachable, showing demo data. ${result.error ?? ""}`
        }
      />

      <main className="mx-auto w-full max-w-[1600px] px-5 py-8 sm:px-8 lg:px-10 lg:py-12">
        <ExecutiveWorkspaceBriefing
          workspace={result.workspace}
          dataSource={result.source}
        />

        {result.source === "fallback" ? (
          <details className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-900">
            <summary className="cursor-pointer font-semibold">
              Backend connection unavailable
            </summary>

            <p className="mt-3 leading-6">
              MOVRvest tried to load:
              <code className="ml-2 rounded bg-white/70 px-1.5 py-0.5">
                {result.backendUrl}
              </code>
            </p>

            {result.error ? (
              <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-xs leading-5">
                {result.error}
              </pre>
            ) : null}
          </details>
        ) : null}

        <div className="mt-20 border-t border-slate-200 pt-14">
          <TopInvestmentCases cases={result.investmentCases} />
        </div>
      </main>
    </DashboardLayout>
  );
}
