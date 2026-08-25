import {
  Activity,
  CalendarDays,
  Compass,
  Database,
  Minus,
  TrendingDown,
  TrendingUp,
  Zap,
} from "lucide-react";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { PageMain } from "@/components/layout/PageMain";
import { PageIntegrity } from "@/components/system-integrity/PageIntegrity";
import { StatusPill } from "@/components/ui/StatusPill";
import {
  getEarnings,
  type EarningsEntry,
  type EarningsResult,
} from "@/lib/api/earnings";
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

/**
 * What this page is allowed to mean.
 *
 * The claim is checkable: the Artificial CIO's decision policy reads no
 * market mood. Market context reaches a decision only as measured
 * evidence about the security itself — its sensitivity to this market,
 * its own volatility and falls.
 */
function InformsNotGates() {
  return (
    <section className="mt-6 rounded-3xl border border-slate-200 bg-slate-950 p-6 text-white sm:p-8">
      <div className="flex gap-4">
        <Compass
          aria-hidden="true"
          className="mt-1 h-5 w-5 shrink-0 text-slate-300"
        />

        <div>
          <h2 className="text-xl font-semibold tracking-tight">
            The market informs decisions. It does not gate them.
          </h2>

          <p className="mt-3 max-w-3xl leading-7 text-slate-300">
            Nothing on this page blocks or approves an investment. The
            Artificial CIO never reads the market&apos;s mood when it judges a
            security — market context reaches a decision only as measured
            evidence about that security: how much it moves with this market,
            its own volatility, its own deepest falls. A red day here is
            context for your attention, not a signal the platform trades on.
          </p>
        </div>
      </div>
    </section>
  );
}

/**
 * The instruments whose day was unusual for them.
 *
 * "Unusual" is measured in the backend: at least twice the instrument's
 * own typical day, read off its own volatility. A raw percentage cannot
 * make that call — a 2% day is routine for Bitcoin and remarkable for a
 * bond index.
 */
function UnusualMoves({ quotes: allQuotes }: { quotes: MarketQuote[] }) {
  const unusual = allQuotes.filter((quote) => quote.unusual === true);
  const unmeasured = allQuotes.filter((quote) => quote.unusual === null);

  return (
    <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 sm:p-8">
      <div className="flex items-start gap-3">
        <div className="rounded-2xl bg-slate-100 p-3 text-slate-700">
          <Zap aria-hidden="true" className="h-5 w-5" />
        </div>

        <div>
          <h2 className="text-xl font-semibold tracking-tight text-slate-950">
            Unusual today
          </h2>

          <p className="mt-1 text-sm leading-6 text-slate-500">
            Moves of at least twice the instrument&apos;s own typical day,
            measured off its own year of closes.
          </p>
        </div>
      </div>

      {unusual.length === 0 ? (
        <p className="mt-5 leading-7 text-slate-600">
          No instrument moved unusually for itself today
          {unmeasured.length > 0
            ? ` — among the ${
                allQuotes.length - unmeasured.length
              } whose ordinary day is measured. For ${unmeasured.length} ${
                unmeasured.length === 1 ? "instrument" : "instruments"
              } the comparison is not measurable, which is not the same as calm.`
            : "."}
        </p>
      ) : (
        <ul className="mt-5 space-y-3">
          {unusual.map((quote) => (
            <li
              className="flex flex-wrap items-baseline gap-x-3 gap-y-1 rounded-2xl border border-amber-200 bg-amber-50/80 px-4 py-3"
              key={quote.symbol}
            >
              <span className="font-semibold text-amber-950">
                {quote.symbol}
              </span>

              <span className="text-sm text-amber-950">
                {quote.changePercent > 0 ? "+" : ""}
                {quote.changePercent.toFixed(2)}% today
              </span>

              {quote.moveRatio !== null ? (
                <span className="text-sm font-medium text-amber-900">
                  {quote.moveRatio.toFixed(1)}× its typical day
                </span>
              ) : null}

              {quote.typicalDailyMovePct !== null ? (
                <span className="text-xs text-amber-800">
                  an ordinary day for {quote.name} is about{" "}
                  {quote.typicalDailyMovePct.toFixed(1)}%
                </span>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </section>
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

      <td className="py-3 pr-4 text-right tabular-nums text-slate-600">
        {/* Absent, not zero: a series too short to measure is not a calm one. */}
        {quote.realizedVolatility === null
          ? "Not measured"
          : `${(quote.realizedVolatility * 100).toFixed(1)}%`}
      </td>

      <td
        className={`py-3 text-right tabular-nums ${
          quote.unusual === true
            ? "font-semibold text-amber-800"
            : "text-slate-600"
        }`}
      >
        {quote.moveRatio === null
          ? "Not measured"
          : `${quote.moveRatio.toFixed(1)}×`}
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

      <UnusualMoves quotes={market.quotes} />

      <InformsNotGates />

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
                <th className="pb-3 pr-4 text-right font-medium">Volatility</th>
                <th className="pb-3 text-right font-medium">vs typical day</th>
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

/** The backend measured the distance; this only words it. */
function reportsWhen(days: number): string {
  if (days === 0) return "Today";
  if (days === 1) return "Tomorrow";
  if (days > 1) return `In ${days} days`;
  if (days === -1) return "Yesterday";
  return `${-days} days ago`;
}

function reportDay(iso: string): string {
  return new Date(`${iso}T00:00:00Z`).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  });
}

function EarningsRow({ entry }: { entry: EarningsEntry }) {
  const window =
    entry.endsOn === null
      ? reportDay(entry.startsOn)
      : `${reportDay(entry.startsOn)} – ${reportDay(entry.endsOn)}`;

  return (
    <li className="flex items-center justify-between gap-4 py-3">
      <div className="flex min-w-0 items-center gap-3">
        <span className="font-semibold text-slate-950">{entry.symbol}</span>

        <span className="truncate text-sm text-slate-500">{entry.name}</span>

        <span
          className={`rounded-full border px-2 py-0.5 text-xs font-medium ${
            entry.held
              ? "border-slate-300 bg-slate-100 text-slate-700"
              : "border-slate-200 bg-white text-slate-500"
          }`}
        >
          {entry.held ? "Held" : "Watched"}
        </span>
      </div>

      <div className="flex shrink-0 items-baseline gap-3 text-right">
        <span
          className={`text-sm font-semibold ${
            entry.startsInDays === 0 ? "text-amber-800" : "text-slate-800"
          }`}
        >
          {reportsWhen(entry.startsInDays)}
        </span>

        <span className="text-sm tabular-nums text-slate-500">{window}</span>
      </div>
    </li>
  );
}

/**
 * The book's own earnings calendar — deliberately not the market's.
 *
 * Thousands of companies report every week; the ones that can bear on a
 * decision here are the ones held or watched. Dates are scheduling fact
 * read from the provider that already prices these companies, and the
 * two absences are stated apart: no published date is not a failed read.
 */
function EarningsAhead({ result }: { result: EarningsResult }) {
  const calendar = result.calendar;

  return (
    <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 sm:p-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="flex items-center gap-2 text-sm font-medium text-slate-500">
            <CalendarDays aria-hidden="true" className="h-4 w-4" />
            Earnings ahead
          </p>

          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">
            When the companies you hold or watch report next
          </h2>

          <p className="mt-3 max-w-2xl leading-7 text-slate-600">
            Scheduling, not prediction: the published date of each next
            report, for your book only. What a report will say is not
            measured here.
          </p>
        </div>

        <StatusPill
          status={
            calendar === null
              ? "placeholder"
              : calendar.unread.length > 0
                ? "partial"
                : "live"
          }
          label={
            calendar === null
              ? "Unavailable"
              : calendar.unread.length > 0
                ? `${calendar.unread.length} not read`
                : "All calendars read"
          }
        />
      </div>

      {calendar === null ? (
        <p className="mt-6 text-slate-600">
          The earnings calendar could not be read this cycle.
        </p>
      ) : (
        <>
          {calendar.upcoming.length > 0 ? (
            <ul className="mt-5 divide-y divide-slate-100">
              {calendar.upcoming.map((entry) => (
                <EarningsRow entry={entry} key={entry.symbol} />
              ))}
            </ul>
          ) : (
            <p className="mt-6 text-slate-600">
              No company in your book has a published upcoming report.
            </p>
          )}

          {calendar.reported.length > 0 ? (
            <div className="mt-6 border-t border-slate-100 pt-4">
              {/* The provider keeps publishing a window for a while
                  after the report ran. That is the last report, not the
                  next one, and it is labelled as what it is. */}
              <p className="text-sm font-medium text-slate-500">
                Recently reported — next date not yet published
              </p>

              <ul className="mt-1 divide-y divide-slate-100">
                {calendar.reported.map((entry) => (
                  <EarningsRow entry={entry} key={entry.symbol} />
                ))}
              </ul>
            </div>
          ) : null}

          {calendar.unscheduled.length > 0 ? (
            <p className="mt-4 text-sm text-slate-500">
              No upcoming date published for{" "}
              {calendar.unscheduled.join(", ")}.
            </p>
          ) : null}

          {calendar.unread.length > 0 ? (
            <p className="mt-1 text-sm text-slate-500">
              Could not be read this cycle: {calendar.unread.join(", ")}.
            </p>
          ) : null}
        </>
      )}
    </section>
  );
}

export default async function MarketsPage() {
  const [result, earnings] = await Promise.all([getMarket(), getEarnings()]);

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

      <PageMain>
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
              This page reports the instruments MOVRvest actually prices, and
              when the companies in your book report earnings next. Sector
              rotation is not measured yet, and is absent rather than
              illustrated.
            </p>
          </div>

          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Database aria-hidden="true" className="h-4 w-4" />

            {result.market ? "Yahoo Finance" : "Backend unavailable"}
          </div>
        </header>

        {result.market ? (
          <>
            <MarketContent market={result.market} />
            <EarningsAhead result={earnings} />
          </>
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
      </PageMain>
    </DashboardLayout>
  );
}
