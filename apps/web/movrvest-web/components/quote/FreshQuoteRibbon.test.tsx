import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { StoredPrice } from "./quote-model";

import { CryptoHeadlinePrice, StockQuoteRibbon } from "./FreshQuoteRibbon";

/**
 * What the ribbon renders before any poll — which is exactly what the
 * server sends. Effects do not run under `renderToStaticMarkup`, so
 * these pin the no-quote state: the page must be complete and honest
 * with zero quote requests made.
 *
 * The stored fallback has **three** states and the markup must
 * distinguish all three. A conflicted row and an empty store both carry
 * a null figure, and reading the figure alone is what made a refused
 * settlement render as an unreported price.
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

const ESTABLISHED: StoredPrice = {
  stated: "$79.14",
  standingStated: "Established",
  age: "TokenInsight, received 22 hours ago",
  because: null,
  conflicted: false,
};

const CLAIMED: StoredPrice = {
  stated: "$79.14",
  standingStated: "Provider claim",
  age: "CoinGecko, received 4 hours ago",
  because: "one source reports it and nothing here can corroborate it.",
  conflicted: false,
};

const CONFLICTED: StoredPrice = {
  stated: null,
  standingStated: "Sources conflict",
  age: null,
  because: CONFLICT_ESSAY,
  conflicted: true,
};

const ABSENT: StoredPrice = {
  stated: null,
  standingStated: "Not reported",
  age: null,
  because: null,
  conflicted: false,
};

function headline(stored: StoredPrice | null): string {
  return renderToStaticMarkup(
    <CryptoHeadlinePrice symbol="HYPE" stored={stored} />,
  );
}

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

  it("serves a provider claim's figure the same way", () => {
    // The gate serves a value for `claimed` as it does for
    // `established`, and the hero leads with it either way.
    const markup = headline(CLAIMED);

    expect(markup).toContain("$79.14");
    expect(markup).toContain("CoinGecko, received 4 hours ago");
    expect(markup).not.toContain(ABSENCE);
  });

  it("states the absence where nothing is held", () => {
    expect(headline(ABSENT)).toContain(ABSENCE);
  });

  it("states the absence where no row exists at all", () => {
    expect(headline(null)).toContain(ABSENCE);
  });
});

describe("the crypto headline, where sources disagree", () => {
  it("says the sources conflict, in the gate's own words", () => {
    const markup = headline(CONFLICTED);

    expect(markup).toContain("Sources conflict");
  });

  it("carries the disagreement account character for character", () => {
    // Nothing here shortens it, names the sources out of it, or
    // composes a friendlier version: the escaped markup must hold the
    // whole sentence exactly as the backend composed it.
    expect(headline(CONFLICTED)).toContain(CONFLICT_ESSAY);
  });

  it("renders no figure, at any size", () => {
    const markup = headline(CONFLICTED);

    // The gate serves none. `$80.12` and `$71.30` appear *inside* the
    // account — as the two claims that disagree — and nowhere as a
    // price this platform is quoting, so the check is structural: the
    // headline figure's own element is absent.
    expect(markup).not.toContain("text-3xl");
    expect(markup).not.toContain("tabular-nums");
    expect(markup).not.toContain("Last established price");
  });

  it("never renders a value a conflicted row carries anyway", () => {
    // The gate cannot produce this today. The assertion is what keeps
    // the ordering honest if one ever arrives: a conflict is not
    // resolvable by finding a number attached to it.
    const markup = headline({ ...CONFLICTED, stated: "$80.12" });

    expect(markup).toContain("Sources conflict");
    expect(markup).not.toContain("text-3xl");
  });

  it("cannot regress into the absence, which is a different finding", () => {
    // The defect this fixes, pinned directly: the conflicted render and
    // the absent render must not be the same markup, and the conflicted
    // one must never carry the absence sentence.
    const conflicted = headline(CONFLICTED);

    expect(conflicted).not.toContain(ABSENCE);
    expect(conflicted).not.toBe(headline(ABSENT));
  });

  it("gives the three stored states three different renderings", () => {
    const markups = [ESTABLISHED, CONFLICTED, ABSENT].map(headline);

    expect(new Set(markups).size).toBe(3);

    // And each is recognisable as itself rather than merely different.
    expect(markups[0]).toContain("$79.14");
    expect(markups[1]).toContain(CONFLICT_ESSAY);
    expect(markups[2]).toContain(ABSENCE);
  });
});

describe("the stock ribbon, server-rendered", () => {
  it("renders nothing until a quote stands — the hero as it was", () => {
    expect(renderToStaticMarkup(<StockQuoteRibbon symbol="DIS" />)).toBe("");
  });
});
