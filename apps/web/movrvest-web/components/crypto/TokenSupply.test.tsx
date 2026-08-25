import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { SupplyView } from "@/lib/api/crypto-dossier";

import { TokenSupply } from "./TokenSupply";

/**
 * What the Tokenomics view actually renders: the four section headings
 * in reading order, and the default-collapsed state.
 */

const SUPPLY = {
  figures: [
    {
      concept: "max_supply",
      conceptStated: "Protocol maximum",
      stated: "1,000,000,000 HYPE",
      definedBy: "The protocol",
      methodology: "As published.",
      disclosed: true,
      excludes: [],
      source: "Hyperliquid info API",
      age: "Hyperliquid info API, yesterday",
      standingStated: "Provider claim",
      authorityStated: "Primary observation",
      because: null,
      caveats: [],
    },
    {
      concept: "max_supply",
      conceptStated: "Protocol maximum",
      stated: "1,000,000,000 tokens",
      definedBy: "The protocol",
      methodology: "As published.",
      disclosed: true,
      excludes: [],
      source: "TokenInsight",
      age: "TokenInsight, yesterday",
      standingStated: "Provider claim",
      authorityStated: "Provider aggregate",
      because: null,
      caveats: [],
    },
  ],
  comparisons: [
    {
      verdict: "corroborated",
      verdictStated: "Agree",
      leftSource: "Hyperliquid info API",
      leftStated: "1,000,000,000 HYPE",
      rightSource: "TokenInsight",
      rightStated: "1,000,000,000 tokens",
      leftConcept: "max_supply",
      rightConcept: "max_supply",
      because: "Same quantity, same figure.",
    },
  ],
  methodologyDisagreement: false,
  unresolved: [{ stated: "No chain reading for HYPE.", concept: null }],
  unavailableBecause: null,
} as unknown as SupplyView;

describe("the rendered token supply view", () => {
  it("names the summary section on the page, not only in the code", () => {
    // The panel was anonymous: the module described it and the reader
    // saw an unlabelled table.
    const markup = renderToStaticMarkup(<TokenSupply supply={SUPPLY} />);

    expect(markup).toContain("What MOVRvest can say");
  });

  it("keeps the authority boundary in the heading", () => {
    const markup = renderToStaticMarkup(<TokenSupply supply={SUPPLY} />);

    // "can say", never "knows": what is held here is provider claims.
    expect(markup).not.toContain("What MOVRvest knows");
    expect(markup).not.toContain("verified");
    expect(markup).not.toContain("established");
  });

  it("renders the four sections in the ruled reading order", () => {
    const markup = renderToStaticMarkup(<TokenSupply supply={SUPPLY} />);

    const order = [
      "Token supply",
      "What MOVRvest can say",
      "What remains unsettled",
      "Source detail",
      "View source-comparison audit",
    ].map((heading) => markup.indexOf(heading));

    expect(order.every((position) => position > -1)).toBe(true);
    expect(order).toEqual([...order].sort((a, b) => a - b));
  });

  it("collapses every disclosure by default", () => {
    const markup = renderToStaticMarkup(<TokenSupply supply={SUPPLY} />);

    expect(markup).toContain("<details");
    expect(markup).not.toMatch(/<details[^>]*\sopen/);
  });

  it("shows no comparison verdict before expansion", () => {
    const markup = renderToStaticMarkup(<TokenSupply supply={SUPPLY} />);
    const summaryOnly = markup.slice(0, markup.indexOf("View source-comparison"));

    expect(summaryOnly).not.toContain("Same quantity, same figure.");
  });

  it("states the backend's absence sentence where nothing is held", () => {
    const markup = renderToStaticMarkup(
      <TokenSupply
        supply={
          {
            figures: [],
            comparisons: [],
            methodologyDisagreement: false,
            unresolved: [],
            unavailableBecause: "No supply evidence is held for this asset.",
          } as unknown as SupplyView
        }
      />,
    );

    expect(markup).toContain("No supply evidence is held for this asset.");
  });
});
