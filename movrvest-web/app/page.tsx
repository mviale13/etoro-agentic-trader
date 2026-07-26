import { getToday } from "@/lib/api";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/Card";
import { Header } from "@/components/dashboard/Header";

export default async function Home() {
  const today = await getToday();

  const actionStyle =
    today.recommendation.action === "BUY"
      ? "bg-emerald-500/15 text-emerald-300"
      : today.recommendation.action === "SELL"
        ? "bg-red-500/15 text-red-300"
        : "bg-amber-500/15 text-amber-300";

  return (
    <DashboardLayout>
      <Header greeting={today.greeting} />

        <section className="grid gap-6 md:grid-cols-2">
          <article className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <p className="text-sm text-slate-400">Portfolio Health</p>

            <p className="mt-3 text-4xl font-semibold">
              {today.health.score}
              <span className="text-xl text-slate-500"> / 100</span>
            </p>

            <p className="mt-4 text-slate-300">{today.summary}</p>
          </article>

          <Card>
            <p className="text-sm text-slate-400">
              Today&apos;s Focus
            </p>

            <p className="mt-3 text-3xl font-semibold">
              {today.recommendation.symbol}
            </p>

            <div className="mt-4 flex items-center gap-3">
              <span
                className={`rounded-full px-3 py-1 text-sm font-semibold ${actionStyle}`}
              >
                {today.recommendation.action}
              </span>

              <span className="text-slate-400">
                {today.recommendation.confidence}% confidence
              </span>
            </div>
          </Card>

          <article className="rounded-2xl border border-slate-800 bg-slate-900 p-6 md:col-span-2">
            <p className="text-sm text-slate-400">What Changed</p>

            <ul className="mt-4 space-y-2">
              {today.changes.map((change) => (
                <li key={change} className="text-slate-300">
                  • {change}
                </li>
              ))}
            </ul>
          </article>

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