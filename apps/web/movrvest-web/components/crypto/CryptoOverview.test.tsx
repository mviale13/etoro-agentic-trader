import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { CryptoDossier } from "@/lib/api/crypto-dossier";

import { CryptoHero, CryptoOverviewView } from "./CryptoOverview";
import { heroModel } from "./overview-model";

/**
 * What the default Overview actually renders.
 *
 * The selector tests pin what is *chosen*; these pin what reaches the
 * markup — the properties of the rendering itself: that the course is
 * stated once, that no audit essay is open by default, that the two
 * columns keep their own heights, and that an absent price states the
 * state rather than the store.
 *
 * Rendered with `renderToStaticMarkup`, which is what the server sends:
 * a `<details>` with no `open` attribute is a closed disclosure whose
 * content is in the document, which is precisely the distinction being
 * pinned.
 */

const CEILING =
  "No digital asset can currently progress past INVESTIGATE: this platform judges an investment case on business quality and valuation.";

const CAPITAL_ACTION = "No capital action is suggested.";

const CONFLICT_ESSAY =
  "credible sources disagree beyond observation-timing tolerance (10%): TokenInsight reports $26.6bn; CoinGecko reports $17.7bn. The sources appear to count the concept differently, and no methodology rule chooses between them.";

function occurrences(haystack: string, needle: string): number {
  return haystack.split(needle).length - 1;
}

function brief(overrides: Record<string, unknown> = {}) {
  return {
    course: "INVESTIGATE",
    courseMeans: CAPITAL_ACTION,
    setup:
      "Economic activity is reaching the token itself, but no issuance rule is held.",
    setupAbsent: null,
    currentView: [
      {
        stated: "Economic activity is reaching the token itself",
        owner: "Intelligence",
        qualification: null,
        support: "Observed",
      },
    ],
    currentViewAbsent: null,
    blocksProgress: [
      {
        stated: "No issuance rule is held",
        owner: "Supply Governance Committee",
        qualification: "That is a statement about what this platform has read.",
        support: null,
      },
      {
        stated: "Circulating supply cannot be stated as a single figure",
        owner: "Investor assessment",
        qualification: null,
        support: null,
      },
    ],
    blocksProgressAbsent: null,
    wouldChangeView: [],
    wouldChangeViewAbsent: "Nothing is currently held that could be watched.",
    withheld: [{ block: "blocks_progress", count: 2 }],
    boundary: CEILING,
    ...overrides,
  };
}

function decisionDossier(
  overrides: Record<string, unknown> = {},
): CryptoDossier {
  return {
    symbol: "HYPE",
    brief: brief(),
    identity: { name: "Exchange network", explanation: "" },
    decision: {
      state: "INVESTIGATE",
      rationale: "Structural evidence is established and quoted below.",
      unresolved: [
        {
          owner: "Supply Governance Committee",
          stated: "No issuance rule is held.",
        },
      ],
      materialUncertainties: [
        "Circulating supply cannot be stated as a single figure.",
      ],
      ceiling: CEILING,
    },
    facts: null,
    protocol: null,
    market: null,
    intelligence: null,
    ...overrides,
  } as unknown as CryptoDossier;
}

// ── the course, said once ───────────────────────────────────────────

describe("the course", () => {
  it("is stated once across the whole default view, with its meaning", () => {
    const markup = renderToStaticMarkup(
      <>
        <CryptoHero hero={heroModel(decisionDossier(), "Hyperliquid")} />
        <CryptoOverviewView dossier={decisionDossier()} brief={brief()} />
      </>,
    );

    // The measured defect: the hero and the card beneath it both
    // rendered the state and the capital-action sentence, so the
    // investor read the same conclusion twice before reaching a finding.
    expect(occurrences(markup, CAPITAL_ACTION)).toBe(1);
    expect(occurrences(markup, "INVESTIGATE")).toBe(1);
  });

  it("carries the one-line setup beside it, not a platform sentence", () => {
    const markup = renderToStaticMarkup(
      <CryptoHero hero={heroModel(decisionDossier(), "Hyperliquid")} />,
    );

    expect(markup).toContain("Economic activity is reaching the token itself");
    expect(markup).not.toContain("not established by this platform");
  });

  it("states the brief's own account where no setup could be composed", () => {
    const markup = renderToStaticMarkup(
      <CryptoHero
        hero={heroModel(
          decisionDossier({
            brief: brief({
              setup: null,
              setupAbsent: "Nothing is currently established either way.",
            }),
          }),
          "Hyperliquid",
        )}
      />,
    );

    expect(markup).toContain("Nothing is currently established either way.");
  });
});

// ── the platform boundary belongs to Evidence ───────────────────────

describe("the platform boundary", () => {
  it("does not appear on the Overview at all", () => {
    const markup = renderToStaticMarkup(
      <CryptoOverviewView dossier={decisionDossier()} brief={brief()} />,
    );

    // It is audit material — a sentence about this platform where the
    // investor needs one about the asset — so it moved rather than
    // shrank. Nothing here summarises or paraphrases it either.
    expect(markup).not.toContain(CEILING);
    expect(markup).not.toContain("Why MOVRvest stops here");
  });

  it("is pointed to, so the reader knows where it went", () => {
    const markup = renderToStaticMarkup(
      <CryptoOverviewView dossier={decisionDossier()} brief={brief()} />,
    );

    expect(markup).toContain("why MOVRvest stops here");
    expect(markup).toContain("view=evidence");
  });
});

// ── the brief ───────────────────────────────────────────────────────

describe("the CIO brief", () => {
  it("renders the three blocks in the investor's order", () => {
    const markup = renderToStaticMarkup(
      <CryptoOverviewView dossier={decisionDossier()} brief={brief()} />,
    );

    const view = markup.indexOf("Current view");
    const blocked = markup.indexOf("What blocks progress");
    const changing = markup.indexOf("What would change the view");

    expect(view).toBeGreaterThan(-1);
    expect(blocked).toBeGreaterThan(view);
    expect(changing).toBeGreaterThan(blocked);
  });

  it("keeps every qualification with the claim it limits", () => {
    const markup = renderToStaticMarkup(
      <CryptoOverviewView dossier={decisionDossier()} brief={brief()} />,
    );

    expect(markup).toContain("No issuance rule is held");
    expect(markup).toContain("That is a statement about what this platform has read.");
  });

  it("names the owner of every finding", () => {
    const markup = renderToStaticMarkup(
      <CryptoOverviewView dossier={decisionDossier()} brief={brief()} />,
    );

    expect(markup).toContain("Supply Governance Committee");
    expect(markup).toContain("Investor assessment");
  });

  it("says what a capped block holds back rather than truncating silently", () => {
    const markup = renderToStaticMarkup(
      <CryptoOverviewView dossier={decisionDossier()} brief={brief()} />,
    );

    expect(markup).toContain("2 further findings under Evidence.");
  });

  it("renders a stated absence, never an empty block", () => {
    const markup = renderToStaticMarkup(
      <CryptoOverviewView dossier={decisionDossier()} brief={brief()} />,
    );

    expect(markup).toContain("Nothing is currently held that could be watched.");
  });
});

// ── the layout properties the redesign turns on ─────────────────────

describe("the Overview layout", () => {
  it("aligns its two columns at the top so neither stretches", () => {
    const markup = renderToStaticMarkup(
      <CryptoOverviewView dossier={decisionDossier()} brief={brief()} />,
    );

    // The measured defect: the grid defaulted to `align-items: normal`,
    // so the short developments module stretched to the facts module's
    // 1,362px and the page carried a column of empty white.
    expect(markup).toContain("items-start");
  });

  it("gives the investment case the wider column", () => {
    const markup = renderToStaticMarkup(
      <CryptoOverviewView dossier={decisionDossier()} brief={brief()} />,
    );

    // Three equal cards gave three findings equal authority they had
    // not earned. Two columns, deliberately unequal.
    expect(markup).toContain("lg:grid-cols-3");
    expect(markup).toContain("lg:col-span-2");
  });

  it("opens no source-disagreement account by default", () => {
    const markup = renderToStaticMarkup(
      <CryptoOverviewView
        brief={brief()}
        dossier={decisionDossier({
          facts: {
            groups: [
              {
                title: "Market",
                rows: [
                  {
                    label: "Market value",
                    stated: null,
                    standing: "conflicted",
                    standingStated: "Sources conflict",
                    source: null,
                    age: null,
                    because: CONFLICT_ESSAY,
                  },
                ],
              },
            ],
          },
        })}
      />,
    );

    // The essay stays in the document — nothing is deleted and nothing
    // is reworded — and every disclosure carrying one is closed.
    expect(markup).toContain(CONFLICT_ESSAY);
    expect(markup).toContain("Sources conflict");

    for (const fragment of markup.split("<details").slice(1)) {
      expect(fragment.slice(0, fragment.indexOf(">"))).not.toContain("open");
    }
  });
});

// ── the hero's price ────────────────────────────────────────────────

describe("the hero price", () => {
  it("states the state, not the store, where no price is served", () => {
    const markup = renderToStaticMarkup(
      <CryptoHero hero={heroModel(decisionDossier(), "Hyperliquid")} />,
    );

    expect(markup).toContain("Price unavailable.");

    // The rule is that the *price* states its state rather than this
    // platform's store. The original pin was the bare word "held",
    // which is a proxy and not the rule — the hero now also carries the
    // brief's own sentence, "…no issuance rule is held", and a proxy
    // that fails on a correct sentence is a worse test than no test.
    for (const store of [
      "No price is held",
      "no price is held",
      "is held for this asset",
      "nothing is stored",
    ]) {
      expect(markup).not.toContain(store);
    }
  });
});

// ── portfolio exposure ──────────────────────────────────────────────

describe("exposure in the hero", () => {
  const portfolio = {
    observed: "eToro account response received at 2026-08-24 17:35 UTC",
    holdings: [{ symbol: "BTC", marketValueUsd: 24726.47, weightPct: 23.124 }],
  } as never;

  it("states a recorded position with the cycle's own receipt wording", () => {
    const markup = renderToStaticMarkup(
      <CryptoHero
        hero={heroModel(
          decisionDossier({ symbol: "BTC" }),
          "Bitcoin",
          portfolio,
        )}
      />,
    );

    expect(markup).toContain("23.1%");
    expect(markup).toContain("eToro account response received");
  });

  it("says not held rather than showing a zero", () => {
    const markup = renderToStaticMarkup(
      <CryptoHero hero={heroModel(decisionDossier(), "Hyperliquid", portfolio)} />,
    );

    expect(markup).toContain("Not held");
    expect(markup).not.toContain("0.0%");
    expect(markup).not.toContain("$0");
  });

  it("says nothing at all where no completed cycle could be read", () => {
    const markup = renderToStaticMarkup(
      <CryptoHero hero={heroModel(decisionDossier(), "Hyperliquid", null)} />,
    );

    expect(markup).not.toContain("Your exposure");
  });
});
