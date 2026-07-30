import Link from "next/link";
import {
  ArrowRight,
  Banknote,
  BriefcaseBusiness,
  CircleDollarSign,
  Clock3,
  Database,
  Landmark,
  Layers3,
  RefreshCw,
  ShieldCheck,
  WalletCards,
} from "lucide-react";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { ExecutivePortfolioAssessment } from "@/components/portfolio/ExecutivePortfolioAssessment";
import {
  getPortfolioOverview,
  type PortfolioOverview,
} from "@/lib/api/portfolio";

export const dynamic = "force-dynamic";

const usdFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

const eurFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 0,
});

function formatSyncTime(value: string | null): string {
  if (!value) {
    return "Synchronization time unavailable";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Europe/Brussels",
  }).format(date);
}

function MetricCard({
  label,
  value,
  secondary,
  icon: Icon,
}: {
  label: string;
  value: string;
  secondary?: string;
  icon: typeof Banknote;
}) {
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">{label}</p>

          <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">
            {value}
          </p>

          {secondary ? (
            <p className="mt-2 text-sm text-slate-500">{secondary}</p>
          ) : null}
        </div>

        <div className="rounded-2xl bg-slate-100 p-3 text-slate-700">
          <Icon aria-hidden="true" className="h-5 w-5" />
        </div>
      </div>
    </article>
  );
}

function PortfolioContent({ portfolio }: { portfolio: PortfolioOverview }) {
  const investedWidth = Math.max(
    0,
    Math.min(100, 100 - portfolio.liquidityPct),
  );

  return (
    <>
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Total portfolio value"
          value={usdFormatter.format(portfolio.totalValueUsd)}
          secondary={eurFormatter.format(portfolio.totalValueEur)}
          icon={Landmark}
        />

        <MetricCard
          label="Available cash"
          value={usdFormatter.format(portfolio.availableCashUsd)}
          secondary={eurFormatter.format(portfolio.availableCashEur)}
          icon={WalletCards}
        />

        <MetricCard
          label="Invested capital"
          value={usdFormatter.format(portfolio.investedUsd)}
          secondary={eurFormatter.format(portfolio.investedEur)}
          icon={CircleDollarSign}
        />

        <MetricCard
          label="Open positions"
          value={portfolio.positions.toString()}
          secondary="Connected eToro positions"
          icon={Layers3}
        />
      </section>

      <section className="mt-6 grid items-start gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        <div className="space-y-6">
          <article className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">
                  Capital allocation
                </p>

                <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">
                  {portfolio.liquidityPct.toFixed(2)}% currently held in cash
                </h2>
              </div>

              <span className="inline-flex w-fit items-center gap-2 rounded-full bg-emerald-50 px-3 py-1.5 text-sm font-medium text-emerald-800">
                <Database aria-hidden="true" className="h-4 w-4" />
                Real portfolio data
              </span>
            </div>

            <div className="mt-8">
              <div
                aria-label={`${portfolio.liquidityPct.toFixed(
                  2,
                )}% cash and ${investedWidth.toFixed(2)}% invested`}
                className="flex h-4 overflow-hidden rounded-full bg-slate-200"
                role="img"
              >
                <div
                  className="bg-slate-900"
                  style={{ width: `${investedWidth}%` }}
                />

                <div
                  className="bg-emerald-400"
                  style={{ width: `${portfolio.liquidityPct}%` }}
                />
              </div>

              <div className="mt-4 flex flex-wrap gap-x-8 gap-y-3 text-sm">
                <div className="flex items-center gap-2 text-slate-700">
                  <span className="h-2.5 w-2.5 rounded-full bg-slate-900" />
                  Invested {investedWidth.toFixed(2)}%
                </div>

                <div className="flex items-center gap-2 text-slate-700">
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />
                  Cash {portfolio.liquidityPct.toFixed(2)}%
                </div>
              </div>
            </div>

            <div className="mt-8 rounded-2xl border border-slate-200 bg-slate-50 p-5">
              <div className="flex gap-3">
                <ShieldCheck
                  aria-hidden="true"
                  className="mt-0.5 h-5 w-5 shrink-0 text-slate-700"
                />

                <div>
                  <h3 className="font-semibold text-slate-950">
                    {portfolio.observationTitle}
                  </h3>

                  <p className="mt-2 leading-7 text-slate-600">
                    {portfolio.observationMessage}
                  </p>
                </div>
              </div>
            </div>
          </article>

          <ExecutivePortfolioAssessment
            liquidity={portfolio.liquidityPct}
            positions={portfolio.positions}
          />
        </div>

        <aside className="rounded-3xl border border-slate-200 bg-slate-950 p-6 text-white sm:p-8">
          <p className="text-sm font-medium text-slate-400">
            Portfolio intelligence
          </p>

          <h2 className="mt-3 text-2xl font-semibold tracking-tight">
            What MOVRvest knows today
          </h2>

          <div className="mt-7 space-y-5">
            <div className="flex gap-3">
              <BriefcaseBusiness
                aria-hidden="true"
                className="mt-0.5 h-5 w-5 shrink-0 text-slate-400"
              />

              <p className="text-sm leading-6 text-slate-300">
                Account value, cash, invested capital and position count are
                connected to the live portfolio snapshot.
              </p>
            </div>

            <div className="flex gap-3">
              <RefreshCw
                aria-hidden="true"
                className="mt-0.5 h-5 w-5 shrink-0 text-slate-400"
              />

              <p className="text-sm leading-6 text-slate-300">
                Last synchronized {formatSyncTime(portfolio.lastSync)}.
              </p>
            </div>

            <div className="flex gap-3">
              <Clock3
                aria-hidden="true"
                className="mt-0.5 h-5 w-5 shrink-0 text-slate-400"
              />

              <p className="text-sm leading-6 text-slate-300">
                Position-level exposure, concentration and performance analysis
                will arrive in the next portfolio slice.
              </p>
            </div>
          </div>

          <Link
            className="mt-8 inline-flex items-center gap-2 rounded-xl bg-white px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-slate-100"
            href="/research"
          >
            Explore opportunities
            <ArrowRight aria-hidden="true" className="h-4 w-4" />
          </Link>
        </aside>
      </section>
    </>
  );
}

export default async function PortfolioPage() {
  const result = await getPortfolioOverview();

  return (
    <DashboardLayout>
      <main className="mx-auto w-full max-w-[1600px] px-5 py-8 sm:px-8 lg:px-10 lg:py-12">
        <header className="mb-8 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
              Portfolio
            </p>

            <h1 className="mt-3 text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
              Portfolio health
            </h1>

            <p className="mt-4 max-w-3xl text-lg leading-8 text-slate-600">
              Understand how your capital is currently allocated before making
              the next investment decision.
            </p>
          </div>

          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Database aria-hidden="true" className="h-4 w-4" />

            {result.source === "backend"
              ? "Connected to MOVRvest Brain"
              : "Backend unavailable"}
          </div>
        </header>

        {result.portfolio ? (
          <PortfolioContent portfolio={result.portfolio} />
        ) : (
          <section className="rounded-3xl border border-amber-200 bg-amber-50 p-6 text-amber-950">
            <h2 className="font-semibold">Unable to load the portfolio</h2>

            <p className="mt-2 leading-7">
              Start the MOVRvest backend and reload this page.
            </p>

            <details className="mt-4 text-sm">
              <summary className="cursor-pointer font-medium">
                Technical details
              </summary>

              <p className="mt-3">
                Endpoint: <code>{result.backendUrl}</code>
              </p>

              {result.error ? (
                <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-xs">
                  {result.error}
                </pre>
              ) : null}
            </details>
          </section>
        )}
      </main>
    </DashboardLayout>
  );
}
