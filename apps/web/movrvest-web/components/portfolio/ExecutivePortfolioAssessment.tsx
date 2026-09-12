import {
  ChartPie,
  LineChart,
  ShieldCheck,
  TriangleAlert,
  TrendingDown,
  Wallet,
} from "lucide-react";

import { StatusPill } from "@/components/ui/StatusPill";
import type {
  PortfolioDrawdown,
  PortfolioRisk,
  RiskIndicator,
} from "@/lib/api/portfolio";

/**
 * What four indicators establish about this account's downside — and,
 * just as carefully, what they do not.
 *
 * This section used to be headed *"How this account can lose money"* and
 * read *"Overall risk reads low"* beside a **"Fully measured"** badge.
 * Three overstatements in one header. The composite is an equal mean of
 * exactly four indicators, so:
 *
 * - it is a composite of **those four**, not the account's total risk —
 *   nothing here measures counterparty, liquidity-of-exit, regulatory or
 *   currency exposure, and a badge saying "fully measured" claimed they
 *   had been;
 * - because it averages, **a component at the ceiling can sit inside a
 *   composite that bands low**. A low headline standing alone is then
 *   reassurance the evidence does not support.
 *
 * The calculation is untouched. Only the account of it changed.
 *
 * Every band, count and figure here arrives typed from the backend. This
 * component compares no score against a threshold of its own — Invariant
 * 8, and the reason `elevated` is served rather than derived.
 */

type ExecutivePortfolioAssessmentProps = {
  risk: PortfolioRisk | null;
  /** The account's own fall, already on the wire. Null where the balance
      history could not be read. */
  drawdown: PortfolioDrawdown | null;
  /** The largest holding and its share, from the capacity reading. */
  largestPosition: string | null;
  largestPositionPct: number | null;
  /** The account's cash share. */
  cashPct: number | null;
};

type IndicatorRow = {
  key: string;
  label: string;
  /** What the indicator measures — never what it implies. */
  description: string;
  /** The figure the score is a score *of*, with its unit. Null where the
      payload carries none. */
  measured: string | null;
  /** The window or coverage the figure describes, where one is held. */
  qualifier: string | null;
  icon: typeof Wallet;
};

const PERCENT = (value: number, digits = 1): string =>
  `${value.toFixed(digits)}%`;

/** A date as the rest of the page writes them. */
function formatDay(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeZone: "UTC",
  }).format(date);
}

/**
 * Whose limit the drawdown is measured against.
 *
 * **The one sentence this section must not get wrong.** The platform
 * applies its own default where the investor has stated nothing, and
 * calling that "the limit the investor set" picks an argument with a
 * figure nobody chose. The provenance is a typed field, never inferred
 * from whether the number looks like a default.
 */
function drawdownLimitStated(risk: PortfolioRisk): string | null {
  if (risk.drawdownLimitPct === null) {
    return null;
  }

  const limit = PERCENT(risk.drawdownLimitPct, 0);

  if (risk.drawdownLimitSource === "investor") {
    return `against the ${limit} the investor said they could accept`;
  }

  if (risk.drawdownLimitSource === "platform_default") {
    return `against the ${limit} this platform applies where the investor has stated no limit`;
  }

  return `against a ${limit} limit whose source is not stated`;
}

/** The rows, each carrying the figures the payload actually holds. */
function indicatorRows(
  risk: PortfolioRisk,
  drawdown: PortfolioDrawdown | null,
  largestPosition: string | null,
  largestPositionPct: number | null,
  cashPct: number | null,
): IndicatorRow[] {
  const limit = drawdownLimitStated(risk);

  return [
    {
      key: "market",
      label: "Market",
      // Not "how violently the market has moved" — it is a historical
      // measure, taken from benchmark instruments, of the slices of this
      // account that could be assigned one.
      description:
        "How much the benchmarks behind this account's holdings have moved historically",
      measured:
        risk.marketVolatilityPct === null
          ? null
          : `${PERCENT(risk.marketVolatilityPct)} annualised volatility`,
      qualifier:
        risk.marketCoveredPct === null
          ? null
          : `Describes ${PERCENT(risk.marketCoveredPct)} of the account` +
            (risk.marketBenchmarks.length > 0
              ? ` · ${risk.marketBenchmarks.join(", ")}`
              : ""),
      icon: LineChart,
    },
    {
      key: "drawdown",
      label: "Drawdown",
      description: `The deepest fall this account has taken, ${
        limit ?? "against a limit that is not stated"
      }`,
      measured:
        drawdown === null ? null : `${PERCENT(drawdown.depthPct)} peak to trough`,
      qualifier:
        drawdown === null
          ? null
          : `${formatDay(drawdown.startsOn)} to ${formatDay(
              drawdown.endsOn,
            )} · ${drawdown.observations} daily balances`,
      icon: TrendingDown,
    },
    {
      key: "concentration",
      label: "Concentration",
      description: "How much of the account sits in its largest holding",
      measured:
        largestPositionPct === null
          ? null
          : `${PERCENT(largestPositionPct)} of the account`,
      qualifier: largestPosition ? `Largest holding: ${largestPosition}` : null,
      icon: ChartPie,
    },
    {
      key: "cash_buffer",
      label: "Cash buffer",
      // Renamed from "Liquidity", which it never measured. Nothing here
      // says whether the holdings could be sold, or at what price.
      description:
        risk.cashBufferThresholdPct === null
          ? "How much cash the account holds"
          : `How much cash the account holds, against a ${PERCENT(
              risk.cashBufferThresholdPct,
              0,
            )} threshold`,
      measured: cashPct === null ? null : `${PERCENT(cashPct)} in cash`,
      qualifier: null,
      icon: Wallet,
    },
  ];
}

/**
 * One indicator, as five segments plus the figures beneath it.
 *
 * The bars are presentation; the score they fill is measured in the
 * Brain and arrives ready. An elevated indicator is marked in words as
 * well as weight, because colour and boldness alone are not a carrier.
 */
function IndicatorRowView({
  row,
  indicator,
}: {
  row: IndicatorRow;
  indicator: RiskIndicator | undefined;
}) {
  const score = indicator?.score ?? null;
  const filled = score === null ? 0 : Math.ceil(score * 5);
  const elevated = indicator?.elevated === true;

  return (
    <div
      className={`flex flex-col gap-3 border-b border-slate-100 py-4 last:border-0 sm:flex-row sm:items-start sm:justify-between ${
        elevated ? "-mx-3 rounded-xl bg-amber-50 px-3" : ""
      }`}
    >
      <div className="flex items-start gap-3">
        <row.icon
          aria-hidden="true"
          className={`mt-0.5 h-5 w-5 shrink-0 ${
            elevated ? "text-amber-700" : "text-slate-500"
          }`}
        />

        <div>
          <span className="font-medium text-slate-900">{row.label}</span>

          {elevated && indicator?.level ? (
            <span className="ml-2 rounded-full bg-amber-200 px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-amber-900">
              {indicator.level.replace("_", " ")}
            </span>
          ) : null}

          <p className="text-sm leading-6 text-slate-500">{row.description}</p>

          {/* The figure the score is a score of. Without it a filled bar
              is a claim with no quantity attached. */}
          {row.measured ? (
            <p className="mt-0.5 text-sm font-medium tabular-nums text-slate-700">
              {row.measured}
            </p>
          ) : null}

          {row.qualifier ? (
            <p className="mt-0.5 text-xs leading-5 text-slate-400">
              {row.qualifier}
            </p>
          ) : null}
        </div>
      </div>

      {score === null ? (
        <span className="shrink-0 text-sm font-medium text-slate-400">
          Not measured
        </span>
      ) : (
        <div
          aria-label={`${row.label}: ${filled} out of 5`}
          className="flex shrink-0 gap-1 sm:mt-1"
          role="img"
        >
          {Array.from({ length: 5 }, (_, index) => (
            <span
              className={`h-2.5 w-8 rounded-full ${
                index < filled
                  ? elevated
                    ? "bg-amber-600"
                    : "bg-slate-900"
                  : "bg-slate-200"
              }`}
              key={`${row.label}-${index}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function ExecutivePortfolioAssessment({
  risk,
  drawdown,
  largestPosition,
  largestPositionPct,
  cashPct,
}: ExecutivePortfolioAssessmentProps) {
  const level = risk?.level?.replace("_", " ") ?? null;

  const rows = risk
    ? indicatorRows(risk, drawdown, largestPosition, largestPositionPct, cashPct)
    : [];

  const byKey = new Map(
    (risk?.indicators ?? []).map((indicator) => [indicator.key, indicator]),
  );

  const elevated = (risk?.indicators ?? []).filter(
    (indicator) => indicator.elevated,
  );

  const labelFor = (key: string): string =>
    rows.find((row) => row.key === key)?.label ?? key;

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="rounded-2xl bg-slate-100 p-3 text-slate-700">
            <ShieldCheck aria-hidden="true" className="h-5 w-5" />
          </div>

          <div>
            <h2 className="text-xl font-semibold tracking-tight text-slate-950">
              Portfolio risk indicators
            </h2>

            {/* The composite is named as what it is. It was headed
                "Overall risk reads low", which reads as a verdict on the
                account rather than an average of four things. */}
            <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-500">
              {level
                ? `A composite of the four indicators below reads ${level}. It is an equal average of those four, not a measure of the account's total risk.`
                : "The composite is withheld while any indicator below is unmeasured. It would be an equal average of the four, not a measure of the account's total risk."}
            </p>
          </div>
        </div>

        {risk ? (
          <StatusPill
            status={risk.measuredCount === risk.indicatorCount ? "live" : "partial"}
            label={`${risk.measuredCount} of ${risk.indicatorCount} indicators available`}
          />
        ) : (
          <StatusPill status="partial" label="Risk unavailable" />
        )}
      </div>

      {/* A severe indicator says so above the list, not only inside it.
          An average of four can band low with one term at the ceiling,
          and the headline alone would then read as reassurance. */}
      {elevated.length > 0 ? (
        <div className="mt-5 flex gap-3 rounded-2xl border border-amber-300 bg-amber-50 p-4">
          <TriangleAlert
            aria-hidden="true"
            className="mt-0.5 h-5 w-5 shrink-0 text-amber-700"
          />

          <p className="text-sm leading-6 text-amber-900">
            {elevated.length === 1
              ? `${labelFor(elevated[0].key)} is elevated on its own scale. `
              : `${elevated
                  .map((indicator) => labelFor(indicator.key))
                  .join(" and ")} are elevated on their own scales. `}
            {level
              ? `The composite reads ${level} because it averages all four.`
              : "The composite is withheld, so it says nothing either way."}
          </p>
        </div>
      ) : null}

      <div className="mt-6">
        {rows.map((row) => (
          <IndicatorRowView
            indicator={byKey.get(row.key)}
            key={row.key}
            row={row}
          />
        ))}
      </div>

      {/* What these four do not cover, stated rather than left to the
          absence of a badge. */}
      <p className="mt-5 border-t border-slate-100 pt-4 text-xs leading-5 text-slate-500">
        These four are the downside indicators this platform measures. They
        are not a complete account of what could go wrong with this
        portfolio, and nothing here is a view on any individual holding.
      </p>

      {risk && risk.evidence.length > 0 ? (
        <div className="mt-4 space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-5">
          {risk.evidence.map((item) => (
            <div key={item.statement}>
              <p className="leading-7 text-slate-700">{item.statement}</p>

              {item.source ? (
                <p className="mt-1 text-sm text-slate-500">{item.source}</p>
              ) : null}
            </div>
          ))}
        </div>
      ) : null}

      {risk && risk.unmeasured.length > 0 ? (
        <ul className="mt-4 space-y-1 text-sm text-slate-500">
          {risk.unmeasured.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
