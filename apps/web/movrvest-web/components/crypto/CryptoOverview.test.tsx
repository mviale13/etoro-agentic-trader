import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { CryptoDossier } from "@/lib/api/crypto-dossier";

import {
  CryptoDecisionBlock,
  CryptoHero,
  CryptoOverviewView,
} from "./CryptoOverview";
import { heroModel } from "./overview-model";

/**
 * What the default Overview actually renders.
 *
 * The selector tests above pin what is *chosen*; these pin what reaches
 * the markup — the two rules that are properties of the rendering and
 * not of the model: the platform boundary is present and collapsed, and
 * an absent price states the state rather than the store.
 *
 * Rendered with `renderToStaticMarkup`, which is what the server sends:
 * a `<details>` with no `open` attribute is a closed disclosure whose
 * content is in the document, which is precisely the distinction being
 * pinned.
 */

const CEILING =
  "No digital asset can currently progress past INVESTIGATE: this platform judges an investment case on business quality and valuation.";

function occurrences(haystack: string, needle: string): number {
  return haystack.split(needle).length - 1;
}

function decisionDossier(
  overrides: Record<string, unknown> = {},
): CryptoDossier {
  return {
    symbol: "HYPE",
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

// ── the platform boundary ───────────────────────────────────────────

describe("the current-course block", () => {
  it("leads with the course and the capital-action sentence", () => {
    const markup = renderToStaticMarkup(
      <CryptoDecisionBlock dossier={decisionDossier()} />,
    );

    expect(markup).toContain("INVESTIGATE");
    expect(markup).toContain("No capital action is suggested.");
    expect(markup).toContain(
      "Structural evidence is established and quoted below.",
    );
    expect(markup).toContain("No issuance rule is held.");
  });

  it("keeps the platform ceiling in the document and collapsed", () => {
    const markup = renderToStaticMarkup(
      <CryptoDecisionBlock dossier={decisionDossier()} />,
    );

    // Present, behind a named disclosure...
    expect(markup).toContain("Why MOVRvest stops here");
    expect(markup).toContain(CEILING);

    // ...and closed: a `<details>` is collapsed exactly when it carries
    // no `open` attribute, so the sentence is reachable without ever
    // occupying the default block.
    const details = markup.slice(markup.indexOf("<details"));

    expect(details.startsWith("<details")).toBe(true);
    expect(details.slice(0, details.indexOf(">"))).not.toContain("open");
  });

  it("renders the backend sentence exactly, neither parsed nor summarised", () => {
    const markup = renderToStaticMarkup(
      <CryptoDecisionBlock dossier={decisionDossier()} />,
    );

    const disclosure = markup.slice(markup.indexOf("<details"));

    // The whole sentence, inside the disclosure, character for
    // character — no clause of it is lifted out or reworded.
    expect(disclosure).toContain(CEILING);
  });

  it("states the ceiling once across the whole default view", () => {
    const markup = renderToStaticMarkup(
      <CryptoOverviewView dossier={decisionDossier()} />,
    );

    expect(occurrences(markup, CEILING)).toBe(1);
    expect(occurrences(markup, "Why MOVRvest stops here")).toBe(1);
  });

  it("offers no disclosure where no ceiling stands", () => {
    const bare = decisionDossier();
    const markup = renderToStaticMarkup(
      <CryptoDecisionBlock
        dossier={decisionDossier({ decision: { ...bare.decision, ceiling: "" } })}
      />,
    );

    expect(markup).not.toContain("Why MOVRvest stops here");
    expect(markup).not.toContain("No capital action is suggested.");
  });
});

// ── the decision's own uncertainties, on the rendered page ──────────

describe("the key risks widget, rendered", () => {
  it("shows the material uncertainty even under three adverse developments", () => {
    const markup = renderToStaticMarkup(
      <CryptoOverviewView
        dossier={decisionDossier({
          intelligence: {
            drivers: [
              {
                stated: "First adverse development.",
                directionStated: "Adverse",
                supportStated: "Supported",
                mattersBecause: null,
                claims: [],
              },
              {
                stated: "Second adverse development.",
                directionStated: "Adverse",
                supportStated: "Supported",
                mattersBecause: null,
                claims: [],
              },
              {
                stated: "Third adverse development.",
                directionStated: "Adverse",
                supportStated: "Supported",
                mattersBecause: null,
                claims: [],
              },
            ],
            events: [],
            watchNext: [],
          },
        })}
      />,
    );

    expect(markup).toContain(
      "Circulating supply cannot be stated as a single figure.",
    );
    expect(markup).toContain("First adverse development.");
    expect(markup).toContain("Second adverse development.");
    expect(markup).not.toContain("Third adverse development.");
  });
});

// ── the hero's price ────────────────────────────────────────────────

describe("the hero price", () => {
  it("states the state, not the store, where no price is served", () => {
    const markup = renderToStaticMarkup(
      <CryptoHero hero={heroModel(decisionDossier(), "Hyperliquid")} />,
    );

    expect(markup).toContain("Price unavailable.");
    expect(markup).not.toContain("No price is held.");
    expect(markup).not.toContain("held");
  });
});
