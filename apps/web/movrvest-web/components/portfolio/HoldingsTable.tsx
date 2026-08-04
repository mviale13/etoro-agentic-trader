import { Layers3 } from "lucide-react";

import { StatusPill } from "@/components/ui/StatusPill";
import type { PortfolioHolding } from "@/lib/api/portfolio";

const usdFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

const signedUsdFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
  signDisplay: "exceptZero",
});

function assetClassLabel(value: string | null): string {
  if (!value) {
    return "Unclassified";
  }

  return value.charAt(0).toUpperCase() + value.slice(1);
}

/**
 * The positions the broker reported, one row per holding, facts only.
 *
 * This table renders last on the page by design: the measured story —
 * capacity, drawdown, risk — comes first, and the raw rows are the
 * evidence behind it, not the headline.
 */
export function HoldingsTable({
  holdings,
  positions,
}: {
  holdings: PortfolioHolding[];
  positions: number;
}) {
  return (
    <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 sm:p-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="rounded-2xl bg-slate-100 p-3 text-slate-700">
            <Layers3 aria-hidden="true" className="h-5 w-5" />
          </div>

          <div>
            <h2 className="text-xl font-semibold tracking-tight text-slate-950">
              What the account holds
            </h2>

            <p className="mt-1 text-sm leading-6 text-slate-500">
              Every open position as the broker reported it, largest first.
            </p>
          </div>
        </div>

        <StatusPill
          status="live"
          label={
            holdings.length === 1
              ? "1 position"
              : `${holdings.length} positions`
          }
        />
      </div>

      {holdings.length === 0 ? (
        <p className="mt-6 leading-7 text-slate-600">
          {positions > 0
            ? `The broker reports ${positions} open positions, but their ` +
              "position-level detail did not arrive with this snapshot. " +
              "The rows are missing, not empty."
            : "The broker reports no open positions."}
        </p>
      ) : (
        <div className="mt-6 overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500">
                <th className="py-3 pr-4 font-medium">Security</th>
                <th className="py-3 pr-4 font-medium">Asset class</th>
                <th className="py-3 pr-4 text-right font-medium">Invested</th>
                <th className="py-3 pr-4 text-right font-medium">Value</th>
                <th className="py-3 pr-4 text-right font-medium">
                  Unrealized P&L
                </th>
                <th className="py-3 text-right font-medium">Weight</th>
              </tr>
            </thead>

            <tbody>
              {[...holdings]
                .sort((a, b) => b.marketValueUsd - a.marketValueUsd)
                .map((holding, index) => (
                  <tr
                    className="border-b border-slate-100 last:border-0"
                    key={`${holding.symbol}-${index}`}
                  >
                    <td className="py-3.5 pr-4">
                      <span className="font-semibold text-slate-900">
                        {holding.symbol}
                      </span>

                      {holding.resolved ? null : (
                        <span className="ml-2 text-xs text-slate-400">
                          Unresolved instrument
                        </span>
                      )}
                    </td>

                    <td className="py-3.5 pr-4 text-slate-600">
                      {assetClassLabel(holding.assetClass)}
                    </td>

                    <td className="py-3.5 pr-4 text-right text-slate-700">
                      {usdFormatter.format(holding.investedUsd)}
                    </td>

                    <td className="py-3.5 pr-4 text-right font-medium text-slate-900">
                      {usdFormatter.format(holding.marketValueUsd)}
                    </td>

                    <td
                      className={`py-3.5 pr-4 text-right font-medium ${
                        holding.unrealizedPnlUsd < 0
                          ? "text-red-700"
                          : "text-emerald-700"
                      }`}
                    >
                      {signedUsdFormatter.format(holding.unrealizedPnlUsd)}
                    </td>

                    <td className="py-3.5 text-right text-slate-700">
                      {holding.weightPct === null
                        ? "Not measured"
                        : `${holding.weightPct.toFixed(1)}%`}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
