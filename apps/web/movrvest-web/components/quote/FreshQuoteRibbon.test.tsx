import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { FreshQuoteView, StoredPrice } from "./quote-model";

import {
  CryptoHeadlinePrice,
  CryptoHeadlinePriceView,
  StockQuoteRibbon,
} from "./FreshQuoteRibbon";

/**
 * What the crypto headline renders, for every combination of quote and
 * stored standing that can reach it.
 *
 * Two properties carry this file. **A stored conflict outranks a
 * current display quote** — one provider's number may not appear to
 * settle a disagreement the gate refused to settle — and **a claim is
 * never labelled as established**, because the hero is the first thing
 * read and a borrowed label is read as authority.
 *
 * `CryptoHeadlinePrice` is pinned through `renderToStaticMarkup`, which
 * is exactly what the server sends and runs no effects: that fixes the
 * quote at null and pins the pre-poll state. Everything that needs a
 * live quote goes through `CryptoHeadlinePriceView`, which takes one.
 */

/**
 * A conflicted price's own account, in the judged-facts gate's shape: a
 * price is pooled at the 10% observation-timing tolerance and carries
 * no methodology clause, which only counts and market values get.
 */
const CONFLICT_ESSAY =
  "credible sources disagree beyond observation-timing tolerance (10%): " +
  "TokenInsight reports $80.12 (TokenInsight, received 22 hours ago); " +
  "CoinGecko reports $71.30 (CoinGecko, received 3 hours ago). " +
  "Uncertainty is exposed rather than a consensus manufactured.";

const ABSENCE = "Price unavailable.";

const NOW = new Date("2026-08-25T14:16:10Z");

const ESTABLISHED: StoredPrice = {
  stated: "$79.14",
  standing: "established",
  standingStated: "Established",
  age: "TokenInsight, received 22 hours ago",
  because: null,
};

const CLAIMED: StoredPrice = {
  stated: "$79.14",
  standing: "claimed",
  standingStated: "Provider claim",
  age: "CoinGecko, received 4 hours ago",
  because: null,
};

const CONFLICTED: StoredPrice = {
  stated: null,
  standing: "conflicted",
  standingStated: "Sources conflict",
  age: null,
  because: CONFLICT_ESSAY,
};

const UNSERVED: StoredPrice = {
  stated: null,
  standing: "unserved",
  standingStated: "Not reported",
  age: null,
  because: null,
};

/** A CURRENT quote on the source's own clock, 16 seconds old at NOW. */
const CURRENT: FreshQuoteView = {
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
};

/** The server-rendered headline: no quote, because effects do not run. */
function headline(stored: StoredPrice | null): string {
  return renderToStaticMarkup(
    <CryptoHeadlinePrice symbol="HYPE" stored={stored} />,
  );
}

/** The same headline with a quote supplied directly. */
function headlineWith(
  quote: FreshQuoteView | null,
  stored: StoredPrice | null,
): string {
  return renderToStaticMarkup(
    <CryptoHeadlinePriceView quote={quote} stored={stored} now={NOW} />,
  );
}

// ── the stored fallback, standing by standing ───────────────────────

describe("the crypto headline, server-rendered", () => {
  it("leads with the established price, named as what it is", () => {
    const markup = headline(ESTABLISHED);

    expect(markup).toContain("$79.14");
    expect(markup).toContain("Last established price");
    expect(markup).toContain("TokenInsight, received 22 hours ago");

    // Never dressed as fresh.
    expect(markup).not.toContain("Updated");
    expect(markup.toLowerCase()).not.toContain("live");
  });

  it("states the absence where nothing is held", () => {
    expect(headline(UNSERVED)).toContain(ABSENCE);
  });

  it("states the absence where no row exists at all", () => {
    expect(headline(null)).toContain(ABSENCE);
  });

  it("states the absence for a standing it cannot name", () => {
    // Fail-closed: a figure whose standing this side cannot name gets
    // no label, and an unlabelled figure borrows the nearest authority.
    expect(headline({ ...UNSERVED, stated: "$79.14" })).toContain(ABSENCE);
  });
});

// ── a claim is not an establishment ─────────────────────────────────

describe("the crypto headline, for a provider claim", () => {
  it("shows the figure, the gate's own standing and the age", () => {
    const markup = headline(CLAIMED);

    expect(markup).toContain("$79.14");
    expect(markup).toContain("Provider claim");
    expect(markup).toContain("CoinGecko, received 4 hours ago");
  });

  it("never calls it established", () => {
    // The defect: "Last established price" was a hardcoded label under
    // any served figure, so one vendor's uncorroborated claim was
    // printed under a corroborated price's name in the one place a
    // reader looks first.
    const markup = headline(CLAIMED);

    expect(markup.toLowerCase()).not.toContain("established");
    expect(markup.toLowerCase()).not.toContain("establish");
  });

  it("quotes whatever the gate calls it, composing no label of its own", () => {
    const markup = headline({
      ...CLAIMED,
      standingStated: "One vendor reports it",
    });

    expect(markup).toContain("One vendor reports it");
  });

  it("renders differently from an established price of the same figure", () => {
    // Same value, same shape, different authority — and the markup has
    // to say so, or the distinction exists only in the model.
    expect(headline(CLAIMED)).not.toBe(headline(ESTABLISHED));
  });
});

// ── the conflicted state ────────────────────────────────────────────

describe("the crypto headline, where sources disagree", () => {
  it("says the sources conflict, in the gate's own words", () => {
    expect(headline(CONFLICTED)).toContain("Sources conflict");
  });

  it("carries the disagreement account character for character", () => {
    // Nothing shortens it, names the sources out of it, or composes a
    // friendlier version: the markup holds the whole sentence exactly
    // as the backend composed it.
    expect(headline(CONFLICTED)).toContain(CONFLICT_ESSAY);
  });

  it("renders no figure, at any size", () => {
    const markup = headline(CONFLICTED);

    // `$80.12` and `$71.30` appear *inside* the account — as the two
    // claims that disagree — and nowhere as a price this platform is
    // quoting, so the check is structural: the headline figure's own
    // element is absent.
    expect(markup).not.toContain("text-3xl");
    expect(markup).not.toContain("tabular-nums");
    expect(markup).not.toContain("Last established price");
  });

  it("carries no absence wording", () => {
    expect(headline(CONFLICTED)).not.toContain(ABSENCE);
  });

  it("never renders a value a conflicted row carries anyway", () => {
    const markup = headline({ ...CONFLICTED, stated: "$80.12" });

    expect(markup).toContain("Sources conflict");
    expect(markup).not.toContain("text-3xl");
  });

  it("cannot regress into the absence, which is a different finding", () => {
    const conflicted = headline(CONFLICTED);

    expect(conflicted).not.toContain(ABSENCE);
    expect(conflicted).not.toBe(headline(UNSERVED));
  });

  it("gives the four stored standings four different renderings", () => {
    const markups = [ESTABLISHED, CLAIMED, CONFLICTED, UNSERVED].map(headline);

    expect(new Set(markups).size).toBe(4);

    expect(markups[0]).toContain("Last established price");
    expect(markups[1]).toContain("Provider claim");
    expect(markups[2]).toContain(CONFLICT_ESSAY);
    expect(markups[3]).toContain(ABSENCE);
  });
});

// ── a conflict outranks the display quote ───────────────────────────

describe("a current quote beside a stored conflict", () => {
  it("shows the conflict, never the quote's number", () => {
    // THE discriminating case, rendered. `CURRENT` leads beside an
    // established row — the control below proves the fixture really is
    // current — so this markup reverts to the quote's figure the
    // moment fresh-quote precedence is restored.
    const markup = headlineWith(CURRENT, CONFLICTED);

    expect(markup).toContain("Sources conflict");
    expect(markup).toContain(CONFLICT_ESSAY);
    expect(markup).not.toContain("80.86");
    expect(markup).not.toContain("Updated");
    expect(markup).not.toContain("text-3xl");
  });

  it("control: the same quote does lead beside an established row", () => {
    const markup = headlineWith(CURRENT, ESTABLISHED);

    expect(markup).toContain("80.86");
    expect(markup).toContain("Updated 16 seconds ago · eToro");
  });

  it("control: the same quote does lead beside a claimed row", () => {
    // A claim is outranked by a current quote exactly as an
    // established figure is. Only the conflict is privileged, and it is
    // privileged because it is not a figure.
    const markup = headlineWith(CURRENT, CLAIMED);

    expect(markup).toContain("80.86");
    expect(markup).not.toContain("Provider claim");
  });

  it("falls back to the conflict when the quote goes stale", () => {
    const markup = headlineWith({ ...CURRENT, status: "stale" }, CONFLICTED);

    expect(markup).toContain("Sources conflict");
    expect(markup).not.toContain("80.86");
  });

  it("falls back to the stored figure when the quote goes stale", () => {
    const markup = headlineWith({ ...CURRENT, status: "stale" }, ESTABLISHED);

    expect(markup).toContain("$79.14");
    expect(markup).toContain("Last established price");
    expect(markup).not.toContain("80.86");
  });

  it("shows the quote where the store holds nothing at all", () => {
    expect(headlineWith(CURRENT, null)).toContain("80.86");
    expect(headlineWith(CURRENT, UNSERVED)).toContain("80.86");
  });
});

describe("the stock ribbon, server-rendered", () => {
  it("renders nothing until a quote stands — the hero as it was", () => {
    expect(renderToStaticMarkup(<StockQuoteRibbon symbol="DIS" />)).toBe("");
  });
});
