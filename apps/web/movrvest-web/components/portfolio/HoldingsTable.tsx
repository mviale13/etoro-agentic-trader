"use client";

/**
 * A client component for one reason: **switching view must not cost a
 * page load.**
 *
 * Both lists are already in this component's props, so choosing
 * between them is free — but the toggle was two plain links, and this
 * route is `force-dynamic`, so every click re-ran the whole server
 * render *and* fired another authenticated account read for data the
 * browser was already holding. Seconds of blank page to reorder
 * thirteen rows.
 *
 * It is still two real anchors. The click is intercepted and the URL
 * updated through the history API — which Next integrates with its
 * router — so the view stays linkable, Back still undoes it, and with
 * JavaScript off the anchors navigate exactly as they did before.
 */

import { useEffect, useState } from "react";
import { Layers3 } from "lucide-react";

import {
  HOLDINGS_PARAM,
  type HoldingsView,
  holdingsViewFromParam,
  holdingsViewHref,
} from "@/components/portfolio/holdings-view";
import { StatusPill } from "@/components/ui/StatusPill";
import type { HeldSecurity, PortfolioHolding } from "@/lib/api/portfolio";

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
 * One row of either view, flattened to what the table prints.
 *
 * Both views arrive from the backend already folded, already ranked and
 * already weighted. This type exists so one table body can render
 * either without knowing which — it carries no rule and decides
 * nothing.
 */
interface Row {
  key: string;
  symbol: string;
  resolved: boolean;
  assetClass: string | null;
  investedUsd: number;
  marketValueUsd: number;
  unrealizedPnlUsd: number;
  weightPct: number | null;
  /** Present only in the consolidated view, and only above one. */
  trades: number | null;
}

/**
 * What the account holds — as securities, or as the broker's trades.
 *
 * **Two questions, two answers, and the page computes neither.** The
 * broker reports a position per trade, so an account holding one
 * security bought twice sends two rows; folding them is analysis, and
 * Invariant 8 keeps analysis out of the dashboard. Both lists arrive
 * summed, ranked and weighted from the backend, and this chooses which
 * one to print.
 *
 * The toggle is two links carrying a `?holdings=` parameter, so each
 * view is URL-addressable, works without JavaScript, and gets its
 * keyboard behaviour from the anchor element itself.
 *
 * This table renders last on the page by design: the measured story —
 * capacity, drawdown, risk — comes first, and the rows are the evidence
 * behind it, not the headline.
 */
export function HoldingsTable({
  holdings,
  heldSecurities,
  positions,
  view: serverView,
}: {
  holdings: PortfolioHolding[];
  heldSecurities: HeldSecurity[];
  positions: number;
  /** What the URL asked for, decided on the server so the first paint
      is already right and a direct link works without JavaScript. */
  view: HoldingsView;
}) {
  // Seeded from the server's answer and owned here afterwards. A
  // server navigation that lands on the other view — a direct link, a
  // reload, the no-JavaScript path — remounts this component through
  // the `key` at the call site, which re-seeds it. Syncing that with an
  // effect instead would set state during render for no gain.
  const [view, setView] = useState<HoldingsView>(serverView);

  // Back and Forward move through the history entries the toggle
  // pushed. Without this the URL would change and the table would not,
  // which is a worse defect than the page load this replaced.
  useEffect(() => {
    function onPopState(): void {
      setView(
        holdingsViewFromParam(
          new URLSearchParams(window.location.search).get(HOLDINGS_PARAM),
        ),
      );
    }

    window.addEventListener("popstate", onPopState);

    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  function show(next: HoldingsView): void {
    setView(next);
    window.history.pushState(null, "", holdingsViewHref(next));
  }

  // A consolidated view the backend did not serve is not silently
  // replaced with a folded-here one: the trade rows are shown and the
  // toggle says so, because inventing the fold on this side is the one
  // thing this component may not do.
  const consolidated = view === "securities" && heldSecurities.length > 0;

  const rows: Row[] = consolidated
    ? heldSecurities.map((held) => ({
        key: `security-${held.instrumentId}`,
        symbol: held.symbol,
        resolved: held.resolved,
        assetClass: held.assetClass,
        investedUsd: held.investedUsd,
        marketValueUsd: held.marketValueUsd,
        unrealizedPnlUsd: held.unrealizedPnlUsd,
        weightPct: held.weightPct,
        trades: held.trades > 1 ? held.trades : null,
      }))
    : // The broker's own order is not a ranking, so the trade view is
      // sorted here — presentation ordering over values the backend
      // already stated, which is the one thing this may do with them.
      [...holdings]
        .sort((a, b) => b.marketValueUsd - a.marketValueUsd)
        .map((holding, index) => ({
          key: `trade-${holding.symbol}-${index}`,
          symbol: holding.symbol,
          resolved: holding.resolved,
          assetClass: holding.assetClass,
          investedUsd: holding.investedUsd,
          marketValueUsd: holding.marketValueUsd,
          unrealizedPnlUsd: holding.unrealizedPnlUsd,
          weightPct: holding.weightPct,
          trades: null,
        }));

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
              {consolidated
                ? "One row per security, largest holding first. A security " +
                  "bought more than once is one holding here."
                : "Every open position as the broker reported it, largest " +
                  "first. The broker reports one row per trade."}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <ViewToggle
            current={view}
            available={heldSecurities.length > 0}
            onShow={show}
          />

          <StatusPill
            status="live"
            label={
              consolidated
                ? `${rows.length} ${rows.length === 1 ? "holding" : "holdings"}`
                : `${rows.length} ${rows.length === 1 ? "position" : "positions"}`
            }
          />
        </div>
      </div>

      {rows.length === 0 ? (
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
                  Unrealized P&amp;L
                </th>
                <th className="py-3 text-right font-medium">Weight</th>
              </tr>
            </thead>

            <tbody>
              {rows.map((row) => (
                <tr
                  className="border-b border-slate-100 last:border-0"
                  key={row.key}
                >
                  <td className="py-3.5 pr-4">
                    <span className="font-semibold text-slate-900">
                      {row.symbol}
                    </span>

                    {row.resolved ? null : (
                      <span className="ml-2 text-xs text-slate-400">
                        Unresolved instrument
                      </span>
                    )}

                    {/* Said only where it changes what the row is: this
                        holding is more than one open trade. */}
                    {row.trades === null ? null : (
                      <span className="ml-2 text-xs text-slate-400">
                        {row.trades} trades
                      </span>
                    )}
                  </td>

                  <td className="py-3.5 pr-4 text-slate-600">
                    {assetClassLabel(row.assetClass)}
                  </td>

                  <td className="py-3.5 pr-4 text-right text-slate-700">
                    {usdFormatter.format(row.investedUsd)}
                  </td>

                  <td className="py-3.5 pr-4 text-right font-medium text-slate-900">
                    {usdFormatter.format(row.marketValueUsd)}
                  </td>

                  <td
                    className={`py-3.5 pr-4 text-right font-medium ${
                      row.unrealizedPnlUsd < 0
                        ? "text-red-700"
                        : "text-emerald-700"
                    }`}
                  >
                    {signedUsdFormatter.format(row.unrealizedPnlUsd)}
                  </td>

                  <td className="py-3.5 text-right text-slate-700">
                    {row.weightPct === null
                      ? "Not measured"
                      : `${row.weightPct.toFixed(1)}%`}
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

/**
 * Two anchors, enhanced — not a control that only works with scripts.
 *
 * Each view is a real `href`, so it is linkable, and with JavaScript off
 * the click navigates and the server renders the right view. With
 * JavaScript on, the click is intercepted and only the URL moves: the
 * rows are already here, and fetching them again to reorder them is the
 * defect this replaced.
 *
 * Modified clicks — new tab, new window, download — are left entirely
 * alone. Intercepting those would break the one thing an anchor is for.
 *
 * Where the backend served no consolidated rows the toggle states that
 * rather than offering a view that would arrive empty: an absence
 * named, never a dead control.
 */
function ViewToggle({
  current,
  available,
  onShow,
}: {
  current: HoldingsView;
  available: boolean;
  onShow: (view: HoldingsView) => void;
}) {
  if (!available) {
    return (
      <p className="text-xs text-slate-400">
        Consolidated holdings are not in this snapshot.
      </p>
    );
  }

  return (
    <nav
      aria-label="Holdings view"
      className="flex rounded-xl border border-slate-200 p-0.5"
    >
      {(
        [
          ["securities", "By security"],
          ["trades", "By trade"],
        ] as const
      ).map(([value, label]) => {
        const active = value === current;

        return (
          <a
            key={value}
            href={holdingsViewHref(value)}
            aria-current={active ? "page" : undefined}
            onClick={(event) => {
              if (
                event.metaKey ||
                event.ctrlKey ||
                event.shiftKey ||
                event.altKey ||
                event.button !== 0
              ) {
                return;
              }

              event.preventDefault();
              onShow(value);
            }}
            className={
              active
                ? "rounded-[10px] bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white"
                : "rounded-[10px] px-3 py-1.5 text-xs font-medium text-slate-500 hover:text-slate-950 focus-visible:text-slate-950"
            }
          >
            {label}
          </a>
        );
      })}
    </nav>
  );
}
