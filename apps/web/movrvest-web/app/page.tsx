import { ExecutiveWorkspaceBriefing } from "@/components/executive/ExecutiveWorkspaceBriefing";
import { TopInvestmentCases } from "@/components/executive/TopInvestmentCases";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { executiveWorkspaceMock } from "@/lib/mocks/executive-workspace";
import { topInvestmentCasesMock } from "@/lib/mocks/top-investment-cases";

export default function HomePage() {
  return (
    <DashboardLayout>
      <main className="mx-auto w-full max-w-[1600px] px-5 py-8 sm:px-8 lg:px-10 lg:py-12">
        <ExecutiveWorkspaceBriefing workspace={executiveWorkspaceMock} />

        <div className="mt-20 border-t border-slate-200 pt-14">
          <TopInvestmentCases cases={topInvestmentCasesMock} />
        </div>
      </main>
    </DashboardLayout>
  );
}
