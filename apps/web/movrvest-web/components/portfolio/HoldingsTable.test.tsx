import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { HeldSecurity, PortfolioHolding } from "@/lib/api/portfolio";

import { HoldingsTable, holdingsViewFromParam } from "./HoldingsTable";

/**
 * What the account holds, asked two ways.
 *
 * The broker reports a position per trade, so "what trades are open"
 * and "what does this account hold" are different questions with
 * different answers — and on the live account they also have different
 * *orderings*. Both lists arrive folded, ranked and weighted from the
 * backend; these pin that the table renders whichever it is given and
 * folds nothing itself.
 *
 * Figures are the live demo account: BTC, ETH and ETOR each split
 * across two trades, 16 rows over 13 securities.
 */

const TRADES: PortfolioHolding[] = [
  { symbol: "BTC", resolved: true, assetClass: "crypto", investedUsd: 19_999.96, marketValueUsd: 23_732.12, unrealizedPnlUsd: 3_732.16, weightPct: 22.2956 },
  { symbol: "ETH", resolved: true, assetClass: "crypto", investedUsd: 9_999.99, marketValueUsd: 13_196.90, unrealizedPnlUsd: 3_196.91, weightPct: 12.3981 },
  { symbol: "BTC", resolved: true, assetClass: "crypto", investedUsd: 499.98, marketValueUsd: 603.84, unrealizedPnlUsd: 103.86, weightPct: 0.5672 },
  { symbol: "SPCX", resolved: true, assetClass: "stock", investedUsd: 500.0, marketValueUsd: 536.12, unrealizedPnlUsd: 36.12, weightPct: 0.5037 },
  { symbol: "ETH", resolved: true, assetClass: "crypto", investedUsd: 399.97, marketValueUsd: 532.64, unrealizedPnlUsd: 132.67, weightPct: 0.5003 },
  { symbol: "ETOR", resolved: true, assetClass: "stock", investedUsd: 496.75, marketValueUsd: 492.37, unrealizedPnlUsd: -4.38, weightPct: 0.4625 },
  { symbol: "ETOR", resolved: true, assetClass: "stock", investedUsd: 99.89, marketValueUsd: 83.37, unrealizedPnlUsd: -16.52, weightPct: 0.0783 },
];

const SECURITIES: HeldSecurity[] = [
  { instrumentId: 1, symbol: "BTC", resolved: true, assetClass: "crypto", investedUsd: 20_499.94, marketValueUsd: 24_335.96, unrealizedPnlUsd: 3_836.02, weightPct: 22.8629, trades: 2 },
  { instrumentId: 2, symbol: "ETH", resolved: true, assetClass: "crypto", investedUsd: 10_399.96, marketValueUsd: 13_729.54, unrealizedPnlUsd: 3_329.58, weightPct: 12.8985, trades: 2 },
  { instrumentId: 3, symbol: "ETOR", resolved: true, assetClass: "stock", investedUsd: 596.64, marketValueUsd: 575.74, unrealizedPnlUsd: -20.90, weightPct: 0.5408, trades: 2 },
  { instrumentId: 4, symbol: "SPCX", resolved: true, assetClass: "stock", investedUsd: 500.0, marketValueUsd: 536.12, unrealizedPnlUsd: 36.12, weightPct: 0.5037, trades: 1 },
];

function render(
  overrides: {
    holdings?: PortfolioHolding[];
    heldSecurities?: HeldSecurity[];
    positions?: number;
    view?: "securities" | "trades";
  } = {},
): string {
  return renderToStaticMarkup(
    <HoldingsTable
      holdings={overrides.holdings ?? TRADES}
      heldSecurities={overrides.heldSecurities ?? SECURITIES}
      positions={overrides.positions ?? 7}
      view={overrides.view ?? "securities"}
    />,
  );
}

/** The symbols in the order the rendered table prints them. */
function renderedSymbols(markup: string): string[] {
  const body = markup.slice(markup.indexOf("<tbody"));

  return [...body.matchAll(/<span class="font-semibold text-slate-900">([^<]+)</g)].map(
    (match) => match[1],
  );
}

// ── which view the URL asks for ─────────────────────────────────────

describe("the holdings view parameter", () => {
  it("defaults to securities, because that is the question the card asks", () => {
    expect(holdingsViewFromParam(undefined)).toBe("securities");
    expect(holdingsViewFromParam("")).toBe("securities");
    expect(holdingsViewFromParam("nonsense")).toBe("securities");
    expect(holdingsViewFromParam("securities")).toBe("securities");
  });

  it("selects the trade view when asked for it", () => {
    expect(holdingsViewFromParam("trades")).toBe("trades");
    expect(holdingsViewFromParam(["trades", "securities"])).toBe("trades");
  });
});

// ── the two answers are different answers ───────────────────────────

describe("the consolidated view", () => {
  it("renders one row per security, not one per trade", () => {
    expect(renderedSymbols(render())).toEqual(["BTC", "ETH", "ETOR", "SPCX"]);
  });

  it("counts holdings rather than positions", () => {
    const markup = render();

    expect(markup).toContain("4 holdings");
    expect(markup).not.toContain("4 positions");
  });

  it("shows the folded value and the folded share", () => {
    const markup = render();

    // $24,336 is BTC's two trades; neither trade carries that figure.
    expect(markup).toContain("$24,336");
    expect(markup).toContain("22.9%");
    expect(markup).not.toContain("$23,732");
  });

  it("says how many trades a holding is, and only above one", () => {
    const markup = render();

    expect(markup).toContain("2 trades");
    expect(markup).not.toContain("1 trades");
  });

  it("says a security bought twice is one holding", () => {
    expect(render()).toContain("One row per security");
  });
});

describe("the trade view", () => {
  it("renders every broker row, duplicates included", () => {
    const symbols = renderedSymbols(render({ view: "trades" }));

    expect(symbols).toHaveLength(7);
    expect(symbols.filter((symbol) => symbol === "BTC")).toHaveLength(2);
  });

  it("counts positions rather than holdings", () => {
    const markup = render({ view: "trades" });

    expect(markup).toContain("7 positions");
    expect(markup).not.toContain("7 holdings");
  });

  it("keeps the broker's own wording for what a row is", () => {
    expect(render({ view: "trades" })).toContain("one row per trade");
  });

  it("never shows a trade count, because a trade is one trade", () => {
    expect(render({ view: "trades" })).not.toContain("trades</span>");
  });
});

describe("the two views disagree, which is the whole point", () => {
  it("ranks differently — a split security outranks a single one", () => {
    // ETOR's two trades total $575.74 and outrank SPCX's single
    // $536.12, which the trade ordering puts above both of them.
    const securities = renderedSymbols(render());
    const trades = renderedSymbols(render({ view: "trades" }));

    expect(securities.indexOf("ETOR")).toBeLessThan(securities.indexOf("SPCX"));
    expect(trades.indexOf("SPCX")).toBeLessThan(trades.indexOf("ETOR"));
  });

  it("produces different markup for the same account", () => {
    expect(render()).not.toBe(render({ view: "trades" }));
  });
});

// ── the toggle ──────────────────────────────────────────────────────

describe("the view toggle", () => {
  it("is two links, so each view is a URL that survives a reload", () => {
    const markup = render();

    expect(markup).toContain('href="/portfolio"');
    expect(markup).toContain('href="/portfolio?holdings=trades"');
    expect(markup).not.toContain("<button");
  });

  it("marks the current view for assistive technology", () => {
    expect(render()).toContain('aria-current="page"');
  });

  it("states an absence rather than offering an empty view", () => {
    const markup = render({ heldSecurities: [], view: "trades" });

    expect(markup).toContain("Consolidated holdings are not in this snapshot.");
    expect(markup).not.toContain('href="/portfolio?holdings=trades"');
  });
});

// ── absences ────────────────────────────────────────────────────────

describe("what the table says when it has nothing", () => {
  it("falls back to the trade rows where no consolidated list arrived", () => {
    // Never folded here instead: a missing list is a missing list.
    const symbols = renderedSymbols(
      render({ heldSecurities: [], view: "securities" }),
    );

    expect(symbols).toHaveLength(7);
  });

  it("distinguishes missing rows from no positions", () => {
    expect(
      render({ holdings: [], heldSecurities: [], positions: 16 }),
    ).toContain("The rows are missing, not empty.");

    expect(
      render({ holdings: [], heldSecurities: [], positions: 0 }),
    ).toContain("The broker reports no open positions.");
  });

  it("says a share nobody could take is not measured, never zero", () => {
    const markup = render({
      heldSecurities: [{ ...SECURITIES[0], weightPct: null }],
    });

    expect(markup).toContain("Not measured");
    expect(markup).not.toContain("0.0%");
  });
});

// ── Invariant 8 ─────────────────────────────────────────────────────

describe("the table computes nothing", () => {
  it("contains no arithmetic over the rows it was given", () => {
    // The structural guard. Both lists arrive summed, ranked and
    // weighted; the moment this file adds them up it is the dashboard
    // calculating, which is what PR #230 refused and what this slice
    // moved to the backend to avoid.
    const source = readFileSync(
      fileURLToPath(new URL("./HoldingsTable.tsx", import.meta.url)),
      "utf8",
    );

    for (const arithmetic of [".reduce(", "+=", "marketValueUsd +", "weightPct +"]) {
      expect(source).not.toContain(arithmetic);
    }
  });
});
