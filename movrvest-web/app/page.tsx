import { getToday } from "@/lib/api";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Header } from "@/components/dashboard/Header";
import { OpportunityCard } from "@/components/dashboard/OpportunityCard";
import { PortfolioHealthCard } from "@/components/dashboard/PortfolioHealthCard";
import { ChangesCard } from "@/components/dashboard/ChangesCard";

export default async function Home() {
  const today = await getToday();


  return (
    <DashboardLayout>
      <Header greeting={today.greeting} />

        <section className="grid gap-6 md:grid-cols-2">
          <ChangesCard changes={today.changes} />

          <OpportunityCard
            symbol={today.recommendation.symbol}
            action={today.recommendation.action}
            confidence={today.recommendation.confidence}
          />

          <PortfolioHealthCard
            score={today.health.score}
            summary={today.summary}
          />

          <article className="rounded-2xl border border-cyan-500/30 bg-cyan-500/10 p-6 md:col-span-2">
            <p className="text-sm font-semibold uppercase tracking-wider text-cyan-300">
              Next Action
            </p>

            <p className="mt-3 text-xl font-medium">
              {today.next_action}
            </p>
          </article>
        </section>
    </DashboardLayout>
  );
}