import { describe, expect, it } from "vitest";

import {
  type FreshQuoteView,
  headlineModel,
  parseQuote,
  ribbonModel,
  statedAge,
} from "./quote-model";

/**
 * The ribbon's wording rules. Fixtures mirror the Stage 0 measurement:
 * eToro states a per-instrument clock and states neither currency,
 * delay nor market status.
 */

const NOW = new Date("2026-08-25T14:16:10Z");

function quote(overrides: Partial<FreshQuoteView> = {}): FreshQuoteView {
  return {
    movrvestSymbol: "HYPE",
    assetClass: "crypto",
    provider: "eToro",
    providerInstrumentIdentity: "100446",
    providerLabel: "Hyperliquid",
    price: 80.86,
    currency: null,
    bid: 80.86,
    ask: 80.87,
    sourceAsOf: "2026-08-25T14:15:53.343213+00:00",
    receivedAt: "2026-08-25T14:15:53.5+00:00",
    clockKind: "source_stated",
    delayStatus: "unknown",
    marketStatus: "unknown",
    status: "current",
    stated: "As eToro stated it, on the source's own clock.",
    ...overrides,
  };
}

// ── parsing ─────────────────────────────────────────────────────────

describe("the wire parse", () => {
  it("reads the backend's snake_case shape", () => {
    const parsed = parseQuote({
      movrvest_symbol: "DIS",
      asset_class: "security",
      provider: "eToro",
      provider_instrument_identity: "1016",
      provider_label: "Walt Disney",
      price: 110.8,
      currency: null,
      bid: 110.8,
      ask: 110.82,
      source_as_of: "2026-08-25T14:15:52.962922+00:00",
      received_at: "2026-08-25T14:15:53+00:00",
      clock_kind: "source_stated",
      delay_status: "unknown",
      market_status: "unknown",
      status: "current",
      stated: "As eToro stated it, on the source's own clock.",
    });

    expect(parsed?.movrvestSymbol).toBe("DIS");
    expect(parsed?.providerInstrumentIdentity).toBe("1016");
    expect(parsed?.price).toBe(110.8);
  });

  it("refuses a malformed quote rather than partially reading it", () => {
    expect(parseQuote(null)).toBeNull();
    expect(parseQuote("HYPE")).toBeNull();
    expect(parseQuote({ movrvest_symbol: "HYPE" })).toBeNull();
    expect(parseQuote({ status: "current", stated: "x" })).toBeNull();
  });
});

// ── the ribbon ──────────────────────────────────────────────────────

describe("the ribbon", () => {
  it("shows a current quote with the source-clock age and the provider", () => {
    const model = ribbonModel(quote(), NOW);

    expect(model?.current).toBe(true);
    expect(model?.figure).toBe("80.86");
    expect(model?.attribution).toBe("Updated 16 seconds ago · eToro");
  });

  it("invents no currency symbol where the provider names none", () => {
    const model = ribbonModel(quote(), NOW);

    expect(model?.figure).not.toContain("$");
    expect(model?.figure).not.toContain("USD");
  });

  it("prints a provider-named currency where one is stated", () => {
    const model = ribbonModel(quote({ currency: "USD" }), NOW);

    expect(model?.figure).toBe("USD 80.86");
  });

  it("shows a stale quote with its honest clock and never as fresh", () => {
    const model = ribbonModel(
      quote({
        status: "stale",
        sourceAsOf: "2026-08-25T14:30:00+00:00",
      }),
      NOW,
    );

    expect(model?.current).toBe(false);
    expect(model?.attribution).toBe("As of 14:30 UTC · eToro");
    expect(model?.attribution).not.toContain("Updated");
  });

  it("never says live and never manufactures delay or closure", () => {
    // The measured provider states neither delay nor market status, so
    // with unknown/unknown nothing extra renders — the qualifier
    // branches exist only for a provider that speaks.
    for (const status of ["current", "stale"] as const) {
      const model = ribbonModel(quote({ status }), NOW);

      const blob = JSON.stringify(model).toLowerCase();

      expect(blob).not.toContain("live");
      expect(blob).not.toContain("real-time");
      expect(model?.qualifiers).toEqual([]);
    }
  });

  it("renders provider-stated delay and closure sentences only", () => {
    const model = ribbonModel(
      quote({ delayStatus: "delayed", marketStatus: "closed" }),
      NOW,
    );

    expect(model?.qualifiers).toEqual(["Quote delayed", "Market closed"]);
  });

  it("renders nothing for refused, unavailable or priceless quotes", () => {
    expect(ribbonModel(null, NOW)).toBeNull();
    expect(ribbonModel(quote({ status: "identity_refused" }), NOW)).toBeNull();
    expect(ribbonModel(quote({ status: "unavailable" }), NOW)).toBeNull();
    expect(ribbonModel(quote({ price: null }), NOW)).toBeNull();
  });

  it("never shows the receipt clock as an observation age", () => {
    // A receipt-only stale quote has no source moment; the attribution
    // falls back to the quote's own stated sentence rather than ageing
    // our receipt and calling it the market's.
    const model = ribbonModel(
      quote({
        status: "stale",
        clockKind: "receipt_only",
        sourceAsOf: null,
        stated:
          "eToro stated no observation time for this quote; only this platform's receipt time exists, which cannot establish currency.",
      }),
      NOW,
    );

    expect(model?.attribution).toContain("stated no observation time");
    expect(model?.attribution).not.toContain("ago");
  });
});

// ── the crypto headline ─────────────────────────────────────────────

describe("the crypto headline", () => {
  const established = {
    stated: "$79.14",
    age: "TokenInsight, received 22 hours ago",
  };

  it("leads with a current fresh quote", () => {
    const model = headlineModel(quote(), established, NOW);

    expect(model.kind).toBe("fresh");
    expect(model.ribbon?.figure).toBe("80.86");
  });

  it("falls back to the established price, named as what it is", () => {
    const model = headlineModel(null, established, NOW);

    expect(model.kind).toBe("established");
    expect(model.establishedStated).toBe("$79.14");
    expect(model.establishedAge).toBe("TokenInsight, received 22 hours ago");
  });

  it("a stale fresh quote never outranks the established figure", () => {
    // Current-or-fallback, with no middle tier that could dress a
    // stale value as fresh.
    const model = headlineModel(quote({ status: "stale" }), established, NOW);

    expect(model.kind).toBe("established");
    expect(model.ribbon).toBeNull();
  });

  it("states the absence where neither figure exists", () => {
    const model = headlineModel(null, { stated: null, age: null }, NOW);

    expect(model.kind).toBe("absent");
  });
});

// ── the age sentence ────────────────────────────────────────────────

describe("the age sentence", () => {
  it("counts from the source clock, coarsely", () => {
    expect(statedAge("2026-08-25T14:16:09Z", NOW)).toBe("1 second ago");
    expect(statedAge("2026-08-25T14:14:10Z", NOW)).toBe("2 minutes ago");
    expect(statedAge("2026-08-25T11:16:10Z", NOW)).toBe("3 hours ago");
  });

  it("refuses an unparseable moment", () => {
    expect(statedAge("whenever", NOW)).toBeNull();
  });
});
