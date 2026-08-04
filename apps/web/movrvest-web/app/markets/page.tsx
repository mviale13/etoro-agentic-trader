import { Activity, Database, Minus, TrendingDown, TrendingUp } from "lucide-react";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { PageIntegrity } from "@/components/system-integrity/PageIntegrity";
import { StatusPill } from "@/components/ui/StatusPill";
import {
  getMarket,
  type Direction,
  type MarketOverview,
  type MarketQuote,
} from "@/lib/api/market";

export const dynamic = "force-dynamic";

const GROUPS: { key: keyof MarketOverview["breadth"]; label: string }[] = [
  { key: "equities", label: "Equities" },
  { key: "technology", label: "Technology" },
  { key: "smallCaps", label: "Small caps" },
  { key: "crypto", label: "Crypto" },
  { key: "commodities", label: "Commodities" },
  { key: "dollar", label: "US dollar" },
  { key: "rates", label: "10-year rates" },
];

function directionStyle(direction: Direction): {
  label: string;
  className: string;
  icon: typeof TrendingUp;
} {
  switch (direction) {
    case "positive":
      return {
        label: "Up",
        className: "border-emerald-200 bg-emerald-50 text-emerald-800",
        icon: TrendingUp,
      };
    case "negative":
      return {
        label: "Down",
        className: "border-rose-200 bg-rose-50 text-rose-800",
        icon: TrendingDown,
      };
    case "neutral":
      return {
        label: "Flat",
        className: "border-slate-200 bg-slate-50 text-slate-700",
        icon: Minus,
      };
    default:
      // Not flat. Nobody looked, and the page says so rather than
      // drawing a line through the middle of a reading never taken.
      return {
        label: "Not priced",
        className: "border-slate-200 bg-white text-slate-400",
        icon: Minus,
      };
  }
}

function BreadthCard({
  label,
  direction,
}: {
  label: string;
  direction: Direction;
}) {
  const style = directionStyle(direction);
  const Icon = style.icon;

  return (
    <article
      className={`rounded-2xl border p-4 ${style.className}`}
      aria-label={`${label}: ${style.label}`}
    >
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium">{label}</p>

        <Icon aria-hidden="true" className="h-4 w-4" />
      </div>

      <p className="mt-2 text-lg font-semibold tracking-tight">{style.label}</p>
    </article>
  );
}

function QuoteRow({ quote }: { quote: MarketQuote }) {
  const up = quote.changePercent > 0;

  return (
    <tr className="border-b border-slate-100 last:border-0">
      <td className="py-3 pr-4">
        <p className="font-medium text-slate-900">{quote.symbol}</p>

        <p className="text-sm text-slate-500">{quote.name}</p>
      </td>

      <td className="py-3 pr-4 text-right tabular-nums text-slate-900">
        {quote.price.toLocaleString("en-US", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })}
      </td>

      <td
        className={`py-3 pr-4 text-right tabular-nums font-medium ${
          up ? "text-emerald-700" : "text-rose-700"
        }`}
      >
        {up ? "+" : ""}
        {quote.changePercent.toFixed(2)}%
      </td>

      <td className="py-3 text-right tabular-nums text-slate-600">
        {/* Absent, not zero: a series too short to measure is not a calm one. */}
        {quote.realizedVolatility === null
          ? "Not measured"
          : `${(quote.realizedVolatility * 100).toFixed(1)}%`}
      </td>
    </tr>
  );
}

function MarketContent({ market }: { market: MarketOverview }) {
  const unpriced = GROUPS.filter(
    (group) => market.breadth[group.key] === "unknown",
  ).length;

  return (
    <>
      <section className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-sm font-medium text-slate-500">
              Across the nine instruments this platform prices
            </p>

            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">
              {market.summary}
            </h2>

            {/* The mood is an average, and an average nets a crypto rally
                against a bond sell-off. The groups below are what it hides. */}
            <p className="mt-3 max-w-2xl leading-7 text-slate-600">
              That is the average move. What it nets out is below.
            </p>
          </div>

          <div className="flex flex-col items-start gap-2 sm:items-end">
            <StatusPill
              status={unpriced === 0 ? "live" : "partial"}
              label={
                unpriced === 0 ? "All groups priced" : `${unpriced} not priced`
              }
            />

            {market.observed ? (
              <span className="text-sm text-slate-500">{market.observed}</span>
            ) : null}
          </div>
        </div>

        <div className="mt-7 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {GROUPS.map((group) => (
            <BreadthCard
              direction={market.breadth[group.key]}
              key={group.key}
              label={group.label}
            />
          ))}

          <article className="rounded-2xl border border-slate-200 bg-slate-950 p-4 text-white">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-medium text-slate-300">Volatility</p>

              <Activity aria-hidden="true" className="h-4 w-4 text-slate-300" />
            </div>

            <p className="mt-2 text-lg font-semibold capitalize tracking-tight">
              {market.breadth.volatility}
            </p>

            <p className="mt-1 text-sm text-slate-400">
              {market.vix === null
                ? "VIX could not be read"
                : `VIX ${market.vix.toFixed(2)}`}
            </p>
          </article>
        </div>
      </section>

      {market.sentiment ? (
        <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 sm:p-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              {/* Labelled by subject, always. The only index MOVRvest reads
                  is a crypto one, and "market sentiment" would invite the
                  reader to apply it to everything they hold. */}
              <p className="text-sm font-medium text-slate-500">
                <span className="capitalize">{market.sentiment.subject}</span>{" "}
                sentiment
              </p>

              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">
                {market.sentiment.score} — {market.sentiment.label}
              </h2>

              <p className="mt-3 max-w-2xl leading-7 text-slate-600">
                This describes {market.sentiment.subject} and is not evidence
                about the rest of the market. No sentiment index is read for
                equities.
              </p>
            </div>

            <span className="text-sm text-slate-500">
              {market.sentiment.observed}
            </span>
          </div>
        </section>
      ) : (
        // The crypto index could not be read this cycle. The equity absence
        // is a constant fact of the platform, not a reading that failed, so
        // it must not vanish with the one index MOVRvest has.
        <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 sm:p-8">
          <p className="text-sm font-medium text-slate-500">Sentiment</p>

          <p className="mt-3 max-w-2xl leading-7 text-slate-600">
            The crypto sentiment index could not be read this cycle. No
            sentiment index is read for equities.
          </p>
        </section>
      )}

      <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 sm:p-8">
        <h2 className="text-xl font-semibold tracking-tight text-slate-950">
          What each instrument did
        </h2>

        <p className="mt-1 text-sm leading-6 text-slate-500">
          Volatility is annualised, measured over the past year of closes.
        </p>

        <div className="mt-6 overflow-x-auto">
          <table className="w-full min-w-[36rem] text-left">
            <thead>
              <tr className="border-b border-slate-200 text-sm text-slate-500">
                <th className="pb-3 pr-4 font-medium">Instrument</th>
                <th className="pb-3 pr-4 text-right font-medium">Price</th>
                <th className="pb-3 pr-4 text-right font-medium">Today</th>
                <th className="pb-3 text-right font-medium">Volatility</th>
              </tr>
            </thead>

            <tbody>
              {market.quotes.map((quote) => (
                <QuoteRow key={quote.symbol} quote={quote} />
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

export default async function MarketsPage() {
  const result = await getMarket();

  return (
    <DashboardLayout>
      <PageIntegrity
        status={result.market ? "live" : "placeholder"}
        endpoint={result.market ? "/market/" : undefined}
        description={
          result.market
            ? "Live Yahoo Finance quotes, classified by group."
            : "Backend unreachable, no market data shown."
        }
      />

      <main className="mx-auto w-full max-w-[1600px] px-5 py-8 sm:px-8 lg:px-10 lg:py-12">
        <header className="mb-8 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
              Markets
            </p>

            <div className="mt-3 flex flex-wrap items-center gap-3">
              <h1 className="text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
                What changed in the world
              </h1>

              {result.market ? (
                <StatusPill status="live" label="Live quotes" />
              ) : (
                <StatusPill status="placeholder" label="Unavailable" />
              )}
            </div>

            <p className="mt-4 max-w-3xl text-lg leading-8 text-slate-600">
              This page reports the instruments MOVRvest actually prices. Sector
              rotation and market events are not measured yet, and are absent
              rather than illustrated.
            </p>
          </div>

          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Database aria-hidden="true" className="h-4 w-4" />

            {result.market ? "Yahoo Finance" : "Backend unavailable"}
          </div>
        </header>

        {result.market ? (
          <MarketContent market={result.market} />
        ) : (
          <section className="rounded-3xl border border-amber-200 bg-amber-50 p-6 text-amber-950">
            <h2 className="font-semibold">Unable to load the market</h2>

            <p className="mt-2 leading-7">
              Start the MOVRvest backend and reload this page.
            </p>

            <details className="mt-4 text-sm">
              <summary className="cursor-pointer font-medium">
                Technical details
              </summary>

              <p className="mt-2 break-words font-mono text-xs">
                {result.backendUrl}
              </p>

              {result.error ? (
                <p className="mt-2 break-words font-mono text-xs">
                  {result.error}
                </p>
              ) : null}
            </details>
          </section>
        )}
      </main>
    </DashboardLayout>
  );
}
