import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type {
  PortfolioDrawdown,
  PortfolioRisk,
  RiskIndicator,
} from "@/lib/api/portfolio";

import { ExecutivePortfolioAssessment } from "./ExecutivePortfolioAssessment";

/**
 * What four indicators may claim, and what they may not.
 *
 * The section overstated its scope three ways at once: a heading that
 * read as a verdict on the account, a composite described as "overall
 * risk", and a "Fully measured" badge over four indicators that do not
 * cover everything a portfolio can lose money to. The calculation is
 * unchanged; these pin the account of it.
 */

function indicator(
  key: string,
  score: number | null,
  level: string | null,
  elevated = false,
): RiskIndicator {
  return { key, score, level, elevated };
}

function risk(overrides: Partial<PortfolioRisk> = {}): PortfolioRisk {
  return {
    overall: 0.3,
    level: "low",
    market: 0.2,
    concentration: 0.3,
    liquidity: 0.4,
    drawdown: 0.3,
    factors: [],
    evidence: [],
    unmeasured: [],
    indicators: [
      indicator("market", 0.2, "low"),
      indicator("drawdown", 0.3, "low"),
      indicator("concentration", 0.3, "low"),
      indicator("cash_buffer", 0.4, "moderate"),
    ],
    measuredCount: 4,
    indicatorCount: 4,
    drawdownLimitPct: 20,
    drawdownLimitSource: "platform_default",
    cashBufferThresholdPct: 10,
    marketVolatilityPct: 18,
    marketCoveredPct: 45.7,
    marketBenchmarks: ["BTC", "ETH", "IWM", "QQQ", "SPY"],
    ...overrides,
  };
}

const DRAWDOWN: PortfolioDrawdown = {
  depthPct: 15.8,
  currentDepthPct: 6,
  recovered: false,
  peakOn: "2026-05-10",
  troughOn: "2026-06-25",
  startsOn: "2025-09-12",
  endsOn: "2026-09-10",
  observations: 364,
  reading: "eToro, just now",
};

function render(
  overrides: {
    risk?: PortfolioRisk | null;
    drawdown?: PortfolioDrawdown | null;
    largestPosition?: string | null;
    largestPositionPct?: number | null;
    cashPct?: number | null;
  } = {},
): string {
  return renderToStaticMarkup(
    <ExecutivePortfolioAssessment
      cashPct={overrides.cashPct === undefined ? 54.2 : overrides.cashPct}
      drawdown={overrides.drawdown === undefined ? DRAWDOWN : overrides.drawdown}
      largestPosition={
        overrides.largestPosition === undefined
          ? "BTC"
          : overrides.largestPosition
      }
      largestPositionPct={
        overrides.largestPositionPct === undefined
          ? 22.9
          : overrides.largestPositionPct
      }
      risk={overrides.risk === undefined ? risk() : overrides.risk}
    />,
  );
}

// ── scope: what the section says it is ──────────────────────────────

describe("the section's own scope", () => {
  it("is headed as indicators, not as how the account loses money", () => {
    const markup = render();

    expect(markup).toContain("Portfolio risk indicators");
    expect(markup).not.toContain("How this account can lose money");
  });

  it("never claims everything is measured", () => {
    const markup = render();

    expect(markup).toContain("4 of 4 indicators available");
    expect(markup).not.toContain("Fully measured");
  });

  it("counts honestly when an indicator is missing", () => {
    const markup = render({
      risk: risk({
        measuredCount: 3,
        overall: null,
        level: null,
        market: null,
        indicators: [
          indicator("market", null, null),
          indicator("drawdown", 0.3, "low"),
          indicator("concentration", 0.3, "low"),
          indicator("cash_buffer", 0.4, "moderate"),
        ],
        marketVolatilityPct: null,
        marketCoveredPct: null,
        marketBenchmarks: [],
      }),
    });

    expect(markup).toContain("3 of 4 indicators available");
  });

  it("states that these four are not the whole of what can go wrong", () => {
    expect(render()).toContain(
      "not a complete account of what could go wrong",
    );
  });
});

// ── the composite is named as a composite ───────────────────────────

describe("the composite", () => {
  it("is described as an average of the four, not the account's risk", () => {
    const markup = render();

    expect(markup).toContain("A composite of the four indicators below");
    expect(markup).toContain("equal average");
    expect(markup).toContain("not a measure of the account&#x27;s total risk");

    // The old sentence read as a verdict on the account.
    expect(markup).not.toContain("Overall risk reads");
  });

  it("says nothing either way while it is withheld", () => {
    const markup = render({
      risk: risk({ overall: null, level: null }),
    });

    expect(markup).toContain("withheld while any indicator below is unmeasured");
  });
});

// ── a low composite must not stand alone as reassurance ─────────────

describe("a severe indicator inside a low composite", () => {
  const severe = risk({
    overall: 0.2875,
    level: "low",
    concentration: 1.0,
    indicators: [
      indicator("market", 0.05, "very_low"),
      indicator("drawdown", 0.05, "very_low"),
      indicator("concentration", 1.0, "very_high", true),
      indicator("cash_buffer", 0.05, "very_low"),
    ],
  });

  it("is announced above the list, not buried inside it", () => {
    const markup = render({ risk: severe, largestPositionPct: 100 });
    const notice = markup.indexOf("Concentration is elevated");
    const list = markup.indexOf("aria-label=\"Market:");

    expect(notice).toBeGreaterThan(-1);
    expect(list).toBeGreaterThan(notice);
  });

  it("says the composite reads low *because* it averages", () => {
    const markup = render({ risk: severe, largestPositionPct: 100 });

    expect(markup).toContain(
      "The composite reads low because it averages all four.",
    );
  });

  it("carries the band in words, never by colour alone", () => {
    const markup = render({ risk: severe, largestPositionPct: 100 });

    expect(markup).toContain("very high");
  });

  it("names every elevated indicator when more than one is", () => {
    const markup = render({
      risk: risk({
        indicators: [
          indicator("market", 0.9, "very_high", true),
          indicator("drawdown", 0.05, "very_low"),
          indicator("concentration", 1.0, "very_high", true),
          indicator("cash_buffer", 0.05, "very_low"),
        ],
      }),
    });

    expect(markup).toContain("Market and Concentration are elevated");
  });

  it("shows no notice when nothing is elevated", () => {
    expect(render()).not.toContain("elevated on its own scale");
  });
});

// ── whose limit the drawdown is measured against ────────────────────

describe("the drawdown limit", () => {
  it("credits the investor only when the investor set it", () => {
    const markup = render({
      risk: risk({ drawdownLimitPct: 15, drawdownLimitSource: "investor" }),
    });

    expect(markup).toContain("against the 15% the investor said they could accept");
    expect(markup).not.toContain("this platform applies");
  });

  it("names the platform default as the platform's", () => {
    // The claim this section must not get wrong.
    const markup = render();

    expect(markup).toContain(
      "against the 20% this platform applies where the investor has stated no limit",
    );
    expect(markup).not.toContain("the investor said they could accept");
    expect(markup).not.toContain("the limit the investor set");
  });

  it("refuses to attribute a limit whose source is not stated", () => {
    const markup = render({
      risk: risk({ drawdownLimitSource: null }),
    });

    expect(markup).toContain("whose source is not stated");
    expect(markup).not.toContain("the investor said");
  });

  it("describes the fall as this account's own history", () => {
    const markup = render();

    expect(markup).toContain("The deepest fall this account has taken");
    expect(markup).toContain("15.8% peak to trough");
    expect(markup).toContain("364 daily balances");
  });
});

// ── market is a benchmark measure, with its coverage ────────────────

describe("the market indicator", () => {
  it("is described as historical movement of benchmarks", () => {
    const markup = render();

    expect(markup).toContain(
      "How much the benchmarks behind this account&#x27;s holdings have moved historically",
    );
    expect(markup).not.toContain("How violently the market");
  });

  it("shows the figure with its unit and the benchmarks behind it", () => {
    const markup = render();

    expect(markup).toContain("18.0% annualised volatility");
    expect(markup).toContain("BTC, ETH, IWM, QQQ, SPY");
  });

  it("states what share of the account the figure actually describes", () => {
    // A blended volatility over part of an account is not a statement
    // about the account.
    const markup = render({
      risk: risk({ marketVolatilityPct: 3, marketCoveredPct: 12 }),
    });

    expect(markup).toContain("3.0% annualised volatility");
    expect(markup).toContain("Describes 12.0% of the account");
  });
});

// ── cash buffer is not liquidity ────────────────────────────────────

describe("the cash buffer indicator", () => {
  it("is no longer called Liquidity", () => {
    const markup = render();

    expect(markup).toContain("Cash buffer");
    expect(markup).not.toContain(">Liquidity<");
    expect(markup).not.toContain("How little cash is left to act with");
  });

  it("names the threshold it is scored against", () => {
    const markup = render();

    expect(markup).toContain("against a 10% threshold");
    expect(markup).toContain("54.2% in cash");
  });

  it("claims nothing about whether holdings could be sold", () => {
    const markup = render().toLowerCase();

    expect(markup).not.toContain("can be sold");
    expect(markup).not.toContain("sellable");
    expect(markup).not.toContain("exit");
  });
});

// ── absences survive as absences ────────────────────────────────────

describe("missing inputs", () => {
  it("keeps an unmeasured indicator as Not measured, never zero", () => {
    const markup = render({
      risk: risk({
        indicators: [
          indicator("market", null, null),
          indicator("drawdown", 0.3, "low"),
          indicator("concentration", 0.3, "low"),
          indicator("cash_buffer", 0.4, "moderate"),
        ],
        measuredCount: 3,
      }),
    });

    expect(markup).toContain("Not measured");
    expect(markup).not.toContain('aria-label="Market: 0 out of 5"');
  });

  it("omits a figure the payload does not carry rather than inventing one", () => {
    const markup = render({
      risk: risk({
        marketVolatilityPct: null,
        marketCoveredPct: null,
        marketBenchmarks: [],
        cashBufferThresholdPct: null,
      }),
      drawdown: null,
      largestPosition: null,
      largestPositionPct: null,
      cashPct: null,
    });

    expect(markup).toContain("Portfolio risk indicators");
    expect(markup).not.toContain("annualised volatility");
    expect(markup).not.toContain("peak to trough");
    expect(markup).not.toContain("of the account<");
    expect(markup).not.toContain("in cash");
    expect(markup).toContain("How much cash the account holds");
  });

  it("says risk is unavailable where no assessment arrived at all", () => {
    const markup = render({ risk: null });

    expect(markup).toContain("Risk unavailable");
    expect(markup).toContain("Portfolio risk indicators");
  });
});

// ── Invariant 8 ─────────────────────────────────────────────────────

describe("the section computes nothing", () => {
  it("renders the band the backend served and derives none of its own", () => {
    // `elevated` is the backend's answer. A component deciding it here
    // would be a second set of thresholds beside the real ones.
    const markup = render({
      risk: risk({
        indicators: [
          indicator("market", 0.2, "low"),
          indicator("drawdown", 0.3, "low"),
          // Score says 0.95 but the backend did not flag it. The page
          // must follow the backend, not the number.
          indicator("concentration", 0.95, "very_high", false),
          indicator("cash_buffer", 0.4, "moderate"),
        ],
      }),
    });

    expect(markup).not.toContain("is elevated on its own scale");
  });
});
