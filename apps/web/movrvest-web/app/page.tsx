import { TopInvestmentCases } from "@/components/executive/TopInvestmentCases";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { topInvestmentCasesMock } from "@/lib/mocks/top-investment-cases";

export default function HomePage() {
  return (
    <DashboardLayout>
      <main className="mx-auto w-full max-w-[1600px] px-5 py-8 sm:px-8 lg:px-10 lg:py-12">
        <header className="mb-14 border-b border-zinc-200 pb-8 dark:border-zinc-800">
          <p className="text-sm font-medium text-zinc-500">
            Executive Brief · Wednesday, July 29
          </p>
          <p className="mt-3 max-w-4xl text-xl leading-8 text-zinc-700 dark:text-zinc-300">
            Today’s strongest opportunities are driven primarily by company
            fundamentals rather than broad market momentum. Selection matters
            more than sector exposure.
          </p>
        </header>

        <TopInvestmentCases cases={topInvestmentCasesMock} />
      </main>
    </DashboardLayout>
  );
}
