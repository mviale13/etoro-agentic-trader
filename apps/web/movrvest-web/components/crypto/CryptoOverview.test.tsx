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

function plan(overrides: Record<string, unknown> = {}) {
  return {
    asksForCapital: false,
    requirements: [
      {
        blocker: "supply_governance",
        blockerStated: "Supply Governance Committee",
        whatIsMissing: "No mechanical issuance rule is held for this asset.",
        whyItMatters: "Is this token's new supply created by a mechanical rule?",
        resolutionNeeded: "An answer to: is this token's new supply mechanical?",
        nextStepKind: "not_currently_resolvable",
        nextStepKindStated: "MOVRvest has no automatic path to this today",
        nextStepStated: "MOVRvest currently has no automatic path to resolve this.",
        retryable: false,
        destination: "evidence",
      },
      {
        blocker: "Circulating supply",
        blockerStated: "Circulating supply",
        whatIsMissing: "Sources differ on circulating supply.",
        whyItMatters: "A holder of a partly issued token is diluted by a schedule.",
        resolutionNeeded: "An exclusion set from the 3 of 4 sources that publish none.",
        nextStepKind: "not_currently_resolvable",
        nextStepKindStated: "MOVRvest has no automatic path to this today",
        nextStepStated:
          "MOVRvest holds every reading it can and cannot reconcile them: 3 of 4 sources publish no exclusion set.",
        retryable: false,
        destination: "tokenomics",
      },
    ],
    absentBecause: null,
    reconsideration:
      "When decision-critical evidence changes, MOVRvest can reconsider the case. Resolving a requirement licenses another look; it does not produce a recommendation, a purchase, a capital envelope or a higher conviction.",
    ...overrides,
  };
}

function decisionDossier(
  overrides: Record<string, unknown> = {},
): CryptoDossier {
  return {
    symbol: "HYPE",
    brief: brief(),
    researchPlan: plan(),
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
        <CryptoOverviewView dossier={decisionDossier()} brief={brief()} plan={plan()} />
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
      <CryptoOverviewView dossier={decisionDossier()} brief={brief()} plan={plan()} />,
    );

    // It is audit material — a sentence about this platform where the
    // investor needs one about the asset — so it moved rather than
    // shrank. Nothing here summarises or paraphrases it either.
    expect(markup).not.toContain(CEILING);
    expect(markup).not.toContain("Why MOVRvest stops here");
  });

  it("is pointed to, so the reader knows where it went", () => {
    const markup = renderToStaticMarkup(
      <CryptoOverviewView dossier={decisionDossier()} brief={brief()} plan={plan()} />,
    );

    expect(markup).toContain("view=evidence");
  });
});

// ── the brief ───────────────────────────────────────────────────────

describe("the CIO brief", () => {
  it("puts why-it-is-worth-researching before what-blocks-capital", () => {
    const markup = renderToStaticMarkup(
      <CryptoOverviewView dossier={decisionDossier()} brief={brief()} plan={plan()} />,
    );

    const worth = markup.indexOf("Why this asset is worth researching");
    const blocks = markup.indexOf("What blocks capital");

    expect(worth).toBeGreaterThan(-1);
    expect(blocks).toBeGreaterThan(worth);
  });

  it("names the owner of every finding", () => {
    const markup = renderToStaticMarkup(
      <CryptoOverviewView dossier={decisionDossier()} brief={brief()} plan={plan()} />,
    );

    expect(markup).toContain("Intelligence");
  });

  it("names a blocker in exactly one place — the plan owns it", () => {
    const markup = renderToStaticMarkup(
      <CryptoOverviewView dossier={decisionDossier()} brief={brief()} plan={plan()} />,
    );

    // Listed under the brief *and* the plan, "Circulating supply"
    // rendered twice and the reader met the same blocker under two
    // headings, only one of which said what would settle it.
    expect(occurrences(markup, "Circulating supply")).toBe(1);
  });
});

// ── the layout properties the redesign turns on ─────────────────────

describe("the Overview layout", () => {
  it("aligns its two columns at the top so neither stretches", () => {
    const markup = renderToStaticMarkup(
      <CryptoOverviewView dossier={decisionDossier()} brief={brief()} plan={plan()} />,
    );

    // The measured defect: the grid defaulted to `align-items: normal`,
    // so the short developments module stretched to the facts module's
    // 1,362px and the page carried a column of empty white.
    expect(markup).toContain("items-start");
  });

  it("gives the investment case the wider column", () => {
    const markup = renderToStaticMarkup(
      <CryptoOverviewView dossier={decisionDossier()} brief={brief()} plan={plan()} />,
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
        plan={plan()}
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

// ── the research plan ───────────────────────────────────────────────

describe("the research plan", () => {
  it("renders exactly one requirement per blocker, each naming its blocker", () => {
    const markup = renderToStaticMarkup(
      <CryptoOverviewView dossier={decisionDossier()} brief={brief()} plan={plan()} />,
    );

    // The one-to-one rule, which was broken before this existed: HYPE
    // showed a fee-economy watch item beside three unrelated supply
    // blockers, none of which it could resolve.
    expect(occurrences(markup, "Supply Governance Committee")).toBe(1);
    expect(occurrences(markup, "Circulating supply")).toBe(1);
  });

  it("states what is missing, why it matters and what would resolve it", () => {
    const markup = renderToStaticMarkup(
      <CryptoOverviewView dossier={decisionDossier()} brief={brief()} plan={plan()} />,
    );

    expect(markup).toContain("Missing");
    expect(markup).toContain("Matters");
    expect(markup).toContain("Resolution");
    expect(markup).toContain("An exclusion set from the 3 of 4 sources");
  });

  it("says honestly when MOVRvest cannot act, rather than manufacturing activity", () => {
    const markup = renderToStaticMarkup(
      <CryptoOverviewView dossier={decisionDossier()} brief={brief()} plan={plan()} />,
    );

    expect(markup).toContain("no automatic path to resolve this");
  });

  it("promises reconsideration and never an outcome", () => {
    const markup = renderToStaticMarkup(
      <CryptoOverviewView dossier={decisionDossier()} brief={brief()} plan={plan()} />,
    );

    expect(markup).toContain("MOVRvest can reconsider the case");

    for (const promise of [
      "will recommend",
      "will monitor",
      "will research",
      "will alert",
    ]) {
      expect(markup.toLowerCase()).not.toContain(promise);
    }
  });

  it("renders no button, because no workflow is reachable from a page", () => {
    const markup = renderToStaticMarkup(
      <CryptoOverviewView dossier={decisionDossier()} brief={brief()} plan={plan()} />,
    );

    expect(markup).not.toContain("<button");
  });

  it("states an absence rather than an empty plan", () => {
    const markup = renderToStaticMarkup(
      <CryptoOverviewView
        dossier={decisionDossier()}
        brief={brief()}
        plan={plan({
          requirements: [],
          absentBecause: "No decision-critical evidence is currently open.",
        })}
      />,
    );

    expect(markup).toContain("No decision-critical evidence is currently open.");
  });

  it("carries no score, count or completeness figure", () => {
    const markup = renderToStaticMarkup(
      <CryptoOverviewView dossier={decisionDossier()} brief={brief()} plan={plan()} />,
    );

    expect(markup).not.toMatch(/\b\d+\s*%\s*(complete|resolved|done)/i);
    expect(markup.toLowerCase()).not.toContain("progress");
  });
});

describe("investment readiness", () => {
  it("says not ready for capital only where the course asks for none", () => {
    const markup = renderToStaticMarkup(
      <CryptoHero hero={heroModel(decisionDossier(), "Hyperliquid")} />,
    );

    expect(markup).toContain("Not ready for capital");
  });

  it("says nothing about readiness where the course does ask for capital", () => {
    const markup = renderToStaticMarkup(
      <CryptoHero
        hero={heroModel(
          decisionDossier({ researchPlan: plan({ asksForCapital: true }) }),
          "Hyperliquid",
        )}
      />,
    );

    expect(markup).not.toContain("Not ready for capital");
  });
});
