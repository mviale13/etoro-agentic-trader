import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { CryptoHeadlinePrice, StockQuoteRibbon } from "./FreshQuoteRibbon";

/**
 * What the ribbon renders before any poll — which is exactly what the
 * server sends. Effects do not run under `renderToStaticMarkup`, so
 * these pin the no-quote state: the page must be complete and honest
 * with zero quote requests made.
 */

describe("the crypto headline, server-rendered", () => {
  it("leads with the established price, named as what it is", () => {
    const markup = renderToStaticMarkup(
      <CryptoHeadlinePrice
        symbol="HYPE"
        establishedStated="$79.14"
        establishedAge="TokenInsight, received 22 hours ago"
      />,
    );

    expect(markup).toContain("$79.14");
    expect(markup).toContain("Last established price");
    expect(markup).toContain("TokenInsight, received 22 hours ago");

    // Never dressed as fresh.
    expect(markup).not.toContain("Updated");
    expect(markup.toLowerCase()).not.toContain("live");
  });

  it("states the absence where nothing is held", () => {
    const markup = renderToStaticMarkup(
      <CryptoHeadlinePrice
        symbol="TAO"
        establishedStated={null}
        establishedAge={null}
      />,
    );

    expect(markup).toContain("Price unavailable.");
  });
});

describe("the stock ribbon, server-rendered", () => {
  it("renders nothing until a quote stands — the hero as it was", () => {
    expect(renderToStaticMarkup(<StockQuoteRibbon symbol="DIS" />)).toBe("");
  });
});
