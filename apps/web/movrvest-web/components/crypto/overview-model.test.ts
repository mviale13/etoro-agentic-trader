import { describe, expect, it } from "vitest";

import type { CryptoDossier } from "@/lib/api/crypto-dossier";

import {
  KEY_FACT_LIMIT,
  briefBlocks,
  exposureModel,
  heroModel,
  keyFacts,
  latestDevelopments,
  marketSetup,
  viewFromParam,
} from "./overview-model";

/**
 * The redesign's rules, tested at the selector layer: what the
 * Overview chooses from the typed dossier, what it refuses to invent,
 * and what it must never surface. Fixtures follow the three acceptance
 * specimens — HYPE (complex, conflicted), BTC (established), TAO
 * (sparse) — trimmed to the fields the selectors read.
 */

function dossier(overrides: Record<string, unknown> = {}): CryptoDossier {
  const base = {
    symbol: "HYPE",
    brief: {
      course: "INVESTIGATE",
      courseMeans: "No capital action is suggested.",
      setup:
        "Economic activity is reaching the token itself, but no issuance rule is held.",
      setupAbsent: null,
      currentView: [
        {
          stated: "Economic activity is reaching the token itself",
          owner: "Intelligence",
          qualification: "A protocol can earn and pass its holders nothing.",
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
      ],
      blocksProgressAbsent: null,
      wouldChangeView: [
        {
          stated: "Whether the fee economy holds up",
          owner: "Intelligence",
          qualification: null,
          support: "the next daily fee and holder-revenue reading",
        },
      ],
      wouldChangeViewAbsent: null,
      withheld: [{ block: "blocks_progress", count: 2 }],
      boundary:
        "No digital asset can currently progress past INVESTIGATE: this platform judges an investment case on business quality and valuation.",
    },
    identity: {
      name: "Exchange network",
      explanation: "Read as a trading venue that runs its own settlement layer.",
    },
    decision: {
      state: "INVESTIGATE",
      rationale: "Structural evidence is established and quoted below.",
      unresolved: [
        { owner: "Supply Governance Committee", stated: "No issuance rule is held." },
      ],
      materialUncertainties: [
        "Tokens in existence cannot be stated as a single figure: estimates run from 586.86 million to 955.31 million.",
        "Circulating supply cannot be stated as a single figure: estimates run from 222.45 million to 1.50 billion.",
      ],
      ceiling:
        "No digital asset can currently progress past INVESTIGATE: this platform judges an investment case on business quality and valuation.",
    },
    facts: {
      groups: [
        {
          title: "Market",
          rows: [
            {
              label: "Price",
              stated: "$79.14",
              standing: "established",
              standingStated: "Established",
              source: "TokenInsight",
              age: "TokenInsight, received 19 hours ago",
              because: "coherent with its source's own arithmetic",
              claimants: ["TokenInsight", "CoinGecko"],
              rule: "crypto-price@1",
            },
            {
              label: "Market value",
              stated: null,
              standing: "conflicted",
              standingStated: "Sources conflict",
              source: null,
              age: null,
              because:
                "credible sources disagree beyond observation-timing tolerance (10%): TokenInsight $17.6bn against CoinGecko $32.4bn.",
              claimants: [],
              rule: null,
            },
            {
              label: "Market-value rank",
              stated: "#9",
              standing: "claimed",
              standingStated: "Provider claim",
              source: "TokenInsight",
              age: "TokenInsight, received 19 hours ago",
              because: "TokenInsight reports it",
              claimants: [],
              rule: null,
            },
          ],
        },
        {
          title: "Supply",
          rows: [
            {
              label: "Maximum supply",
              stated: "1,000,000,000",
              standing: "established",
              standingStated: "Established",
              source: "TokenInsight",
              age: "TokenInsight, received 19 hours ago",
              because: "coherent",
              claimants: ["TokenInsight"],
              rule: null,
            },
            {
              label: "Circulating supply",
              stated: null,
              standing: "conflicted",
              standingStated: "Sources conflict",
              source: null,
              age: null,
              because:
                "credible sources disagree beyond observation-timing tolerance (1%).",
              claimants: [],
              rule: null,
            },
            {
              label: "Share of maximum supply circulating",
              stated: null,
              standing: "absent",
              standingStated: "Not computed",
              source: null,
              age: null,
              because: "not computed",
              claimants: [],
              rule: null,
            },
          ],
        },
      ],
      rejected: [],
    },
    protocol: {
      entities: [
        {
          key: "hyperliquid-protocol",
          name: "Hyperliquid",
          kind: "protocol",
          measures: "the venue",
          mappingBasis: "",
          mappingSettled: true,
          facts: [
            {
              metric: "fees",
              label: "Fees paid by users",
              family: "value_generation",
              stated: "$3.1m",
              window: "24h",
              standing: "claimed",
              standingStated: "Provider claim",
              availability: "available",
              availabilityStated: "Available",
              source: "DefiLlama",
              age: "DefiLlama, 19 hours ago",
              providerMethodology: null,
              because: null,
            },
            {
              metric: "open_interest",
              label: "Open interest",
              family: "activity",
              stated: "$13.89bn",
              window: null,
              standing: "claimed",
              standingStated: "Provider claim",
              availability: "available",
              availabilityStated: "Available",
              source: "DefiLlama",
              age: "DefiLlama, 19 hours ago",
              providerMethodology: null,
              because: null,
            },
            {
              metric: "dex_volume",
              label: "DEX volume",
              family: "activity",
              stated: null,
              window: null,
              standing: "absent",
              standingStated: "Not reported",
              availability: "absent",
              availabilityStated: "Absent",
              source: null,
              age: null,
              providerMethodology: null,
              because: null,
            },
          ],
        },
      ],
      derived: [],
      unmappedBecause: null,
    },
    market: {
      returns: [
        {
          label: "Price return",
          interval: "1h",
          intervalStated: "over 1 hour",
          stated: "-2.50%",
          standingStated: "Provider claim",
          derived: false,
          universe: null,
          source: null,
          because: null,
        },
        {
          label: "Price return",
          interval: "24h",
          intervalStated: "over 24 hours",
          stated: "-0.94%",
          standingStated: "Provider claim",
          derived: false,
          universe: null,
          source: null,
          because: null,
        },
        {
          label: "Price return",
          interval: "7d",
          intervalStated: "over 7 days",
          stated: "+33.10%",
          standingStated: "Provider claim",
          derived: false,
          universe: null,
          source: null,
          because: null,
        },
        {
          label: "Price return",
          interval: "30d",
          intervalStated: "over 30 days",
          stated: "+36.60%",
          standingStated: "Provider claim",
          derived: false,
          universe: null,
          source: null,
          because: null,
        },
      ],
    },
    intelligence: {
      drivers: [
        {
          stated: "Economic activity is reaching the token itself.",
          directionStated: "Supportive",
          supportStated: "Observed",
          mattersBecause: null,
          claims: ["network.fees.hyperliquid-protocol"],
        },
        {
          stated: "The asset has moved +37% over a month.",
          directionStated: "Supportive",
          supportStated: "Observed",
          mattersBecause: null,
          claims: [],
        },
        {
          stated: "Regulatory: Hyperliquid explores US markets.",
          directionStated: "Adverse",
          supportStated: "Supported",
          mattersBecause: null,
          claims: [],
        },
        {
          stated: "Token economics: strong revenue reported.",
          directionStated: "Context",
          supportStated: "Supported",
          mattersBecause: null,
          claims: [],
        },
        {
          stated: "A fourth non-adverse driver.",
          directionStated: "Context",
          supportStated: "Supported",
          mattersBecause: null,
          claims: [],
        },
      ],
      events: [
        {
          headline: "Hyperliquid Explores US Markets and Tokenized Equities",
          family: "regulatory",
          status: "completed",
          sources: ["CoinGecko Insights", "Elfa AI"],
          isMultiSource: true,
          age: ", 20 hours ago",
          facts: [],
          interpretations: [
            {
              stated:
                "Hyperliquid is engaging with the CFTC regarding tokenized US equities.",
              source: "CoinGecko Insights",
              isCausal: false,
            },
          ],
        },
        {
          headline: "Second development",
          family: "token_economics",
          status: "completed",
          sources: ["CoinGecko Insights"],
          isMultiSource: false,
          age: ", 21 hours ago",
          facts: [],
          interpretations: [],
        },
        {
          headline: "Third development",
          family: "market",
          status: "completed",
          sources: ["Elfa AI"],
          isMultiSource: false,
          age: null,
          facts: [],
          interpretations: [],
        },
        {
          headline: "Fourth development that must not render",
          family: "market",
          status: "completed",
          sources: ["Elfa AI"],
          isMultiSource: false,
          age: null,
          facts: [],
          interpretations: [],
        },
      ],
      watchNext: [
        {
          stated: "Whether the fee economy holds up.",
          measuredBy: "the next daily fee and holder-revenue reading",
          because: ["network.fees.hyperliquid-protocol"],
        },
      ],
    },
    ...overrides,
  };

  return base as unknown as CryptoDossier;
}

// ── tabs ────────────────────────────────────────────────────────────

describe("the view parameter", () => {
  it("selects a known view and defaults everything else to overview", () => {
    expect(viewFromParam("economics")).toBe("economics");
    expect(viewFromParam("evidence")).toBe("evidence");
    expect(viewFromParam(undefined)).toBe("overview");
    expect(viewFromParam("nonsense")).toBe("overview");
    expect(viewFromParam(["tokenomics", "evidence"])).toBe("tokenomics");
    expect(viewFromParam("")).toBe("overview");
  });
});

// ── hero ────────────────────────────────────────────────────────────

describe("the hero", () => {
  it("leads with the asset, its role, the established price and the course", () => {
    const hero = heroModel(dossier(), "Hyperliquid");

    expect(hero.symbol).toBe("HYPE");
    expect(hero.name).toBe("Hyperliquid");
    expect(hero.role).toBe("Exchange network");
    expect(hero.price?.stated).toBe("$79.14");
    expect(hero.price?.standingStated).toBe("Established");
    expect(hero.state).toBe("INVESTIGATE");
    expect(hero.courseLine).toBe("No capital action is suggested.");
  });

  it("shows 24h, 7d and 30d returns and never the 1h reading", () => {
    const hero = heroModel(dossier(), null);

    expect(hero.returns.map((r) => r.short)).toEqual(["24h", "7d", "30d"]);
    expect(hero.returns.map((r) => r.stated)).toEqual([
      "-0.94%",
      "+33.10%",
      "+36.60%",
    ]);
  });

  it("omits what is not held rather than inventing it", () => {
    const hero = heroModel(
      dossier({ market: null, facts: null }),
      null,
    );

    expect(hero.price).toBeNull();
    expect(hero.returns).toEqual([]);
  });

  it("offers no course line where the brief states none", () => {
    const bare = dossier();
    const hero = heroModel(
      dossier({ brief: { ...bare.brief, courseMeans: "" } }),
      null,
    );

    expect(hero.courseLine).toBeNull();
  });

  it("takes the course and its meaning from the brief, never from two places", () => {
    const hero = heroModel(dossier(), null);

    expect(hero.state).toBe("INVESTIGATE");
    expect(hero.courseLine).toBe("No capital action is suggested.");
    expect(hero.setup).toContain("Economic activity is reaching the token itself");
  });

  it("renders the brief's own account where no setup could be composed", () => {
    const bare = dossier();
    const hero = heroModel(
      dossier({
        brief: {
          ...bare.brief,
          setup: null,
          setupAbsent: "Nothing is currently established either way.",
        },
      }),
      null,
    );

    expect(hero.setup).toBeNull();
    expect(hero.setupAbsent).toBe("Nothing is currently established either way.");
  });
});

// ── summary widgets ─────────────────────────────────────────────────

describe("the CIO brief", () => {
  it("passes the backend's blocks through in order, adding only headings", () => {
    const blocks = briefBlocks(dossier().brief);

    expect(blocks.map((block) => block.title)).toEqual([
      "Current view",
      "What blocks progress",
      "What would change the view",
    ]);

    expect(blocks[0].lines[0].stated).toBe(
      "Economic activity is reaching the token itself",
    );
  });

  it("carries the owner and the qualification with every line", () => {
    const [view, blocked] = briefBlocks(dossier().brief);

    expect(view.lines[0].owner).toBe("Intelligence");
    expect(blocked.lines[0].owner).toBe("Supply Governance Committee");
    expect(blocked.lines[0].qualification).toContain("what this platform has read");
  });

  it("reports what a capped block holds back", () => {
    const blocks = briefBlocks(dossier().brief);

    expect(blocks[1].withheld).toBe(2);
    expect(blocks[0].withheld).toBe(0);
  });

  it("renders a stated absence rather than an empty block", () => {
    const brief = {
      ...dossier().brief,
      currentView: [],
      currentViewAbsent: "No driver is currently held for this asset.",
    };

    const [view] = briefBlocks(brief);

    expect(view.lines).toHaveLength(0);
    expect(view.absent).toBe("No driver is currently held for this asset.");
  });
});

describe("the market setup", () => {
  it("shows every measured window, including the 1h the hero omits", () => {
    const setup = marketSetup(dossier());
    const windows = setup.returns.map((item) => item.short);

    expect(setup.returns.length).toBeGreaterThan(0);
    expect(windows).toContain("1h");
    expect(windows).toContain("30d");
  });

  it("carries no price, because the hero already leads with it", () => {
    expect(Object.keys(marketSetup(dossier()))).not.toContain("price");
  });

  it("names what is not held instead of deriving a range from a return", () => {
    const setup = marketSetup(dossier());

    expect(setup.unavailable).toHaveLength(2);
    expect(setup.unavailable.join(" ")).toContain("no high or low is held");
    expect(setup.unavailable.join(" ")).toContain("no baseline");
  });

  it("words no conditional scenario, because no layer establishes one", () => {
    const setup = marketSetup(dossier());
    const prose = [...setup.unavailable].join(" ").toLowerCase();

    for (const forecast of ["would be", "continuation", "if momentum", "expect"]) {
      expect(prose).not.toContain(forecast);
    }
  });
});

describe("portfolio exposure", () => {
  const portfolio = {
    observed: "eToro account response received at 2026-08-24 17:35 UTC",
    holdings: [
      { symbol: "BTC", marketValueUsd: 24726.47, weightPct: 23.124 },
      { symbol: "SOL", marketValueUsd: 387.1, weightPct: null },
    ],
  } as never;

  it("states a recorded share with the cycle's own receipt wording", () => {
    const exposure = exposureModel("BTC", portfolio);

    expect(exposure).toEqual({
      held: true,
      weightStated: "23.1%",
      valueStated: "$24,726",
      observed: "eToro account response received at 2026-08-24 17:35 UTC",
    });
  });

  it("treats an uncomputable share as absent, never as no position", () => {
    expect(exposureModel("SOL", portfolio)?.weightStated).toBeNull();
    expect(exposureModel("SOL", portfolio)?.held).toBe(true);
  });

  it("distinguishes not-held from no-readable-cycle", () => {
    expect(exposureModel("HYPE", portfolio)?.held).toBe(false);
    expect(exposureModel("HYPE", null)).toBeNull();
  });

  it("never states a zero for an asset the portfolio does not contain", () => {
    const exposure = exposureModel("HYPE", portfolio);

    expect(exposure?.weightStated).toBeNull();
    expect(exposure?.valueStated).toBeNull();
  });
});

describe("the key facts widget", () => {
  it("keeps a conflict a conflict and never serves a number for it", () => {
    const facts = keyFacts(dossier());
    const marketValue = facts.find((fact) => fact.label === "Market value");

    expect(marketValue).toBeDefined();
    expect(marketValue?.stated).toBeNull();
    expect(marketValue?.standingStated).toBe("Sources conflict");
    expect(marketValue?.because).toContain("credible sources disagree");
  });

  it("never resolves a conflicted market value from the established price", () => {
    const facts = keyFacts(dossier());
    const marketValue = facts.find((fact) => fact.label === "Market value");

    // The price is established and the market value is conflicted, and
    // the widget must not let one repair the other.
    expect(marketValue?.stated).toBeNull();
  });

  it("omits absent facts entirely", () => {
    const facts = keyFacts(dossier());

    expect(
      facts.find((f) => f.label === "Share of maximum supply circulating"),
    ).toBeUndefined();
    expect(facts.find((f) => f.label === "DEX volume")).toBeUndefined();
  });

  it("does not duplicate the hero's price", () => {
    const facts = keyFacts(dossier());

    expect(facts.find((fact) => fact.label === "Price")).toBeUndefined();
  });

  it("labels protocol figures with their economic entity", () => {
    const facts = keyFacts(dossier());
    const protocolFact = facts.find((fact) => fact.entity !== null);

    expect(protocolFact?.entity).toBe("Hyperliquid");
    expect(protocolFact?.stated).not.toBeNull();
  });

  it("shows six metrics at most", () => {
    expect(keyFacts(dossier()).length).toBeLessThanOrEqual(KEY_FACT_LIMIT);
    expect(KEY_FACT_LIMIT).toBe(6);
  });

  it("shows one row per quantity, never one per mapped entity", () => {
    const labels = keyFacts(dossier()).map((fact) => fact.label);

    expect(new Set(labels).size).toBe(labels.length);
  });

  it("keeps the fee and holder-revenue detail for Economics", () => {
    const labels = keyFacts(dossier()).map((fact) => fact.label);

    expect(labels).not.toContain("Fees paid by users");
    expect(labels).not.toContain("Holder revenue");
  });

  it("surfaces no raw metric identifier", () => {
    const blob = JSON.stringify(keyFacts(dossier()));

    for (const identifier of ["value_generation", "open_interest", "dex_volume"]) {
      expect(blob).not.toContain(identifier);
    }
  });

  it("is empty where nothing is held", () => {
    expect(keyFacts(dossier({ facts: null, protocol: null }))).toEqual([]);
  });
});

// ── latest developments ─────────────────────────────────────────────

describe("latest developments", () => {
  it("shows at most three, in the served order", () => {
    const developments = latestDevelopments(dossier());

    expect(developments).toHaveLength(3);
    expect(
      developments.find((d) => d.headline.startsWith("Fourth")),
    ).toBeUndefined();
  });

  it("carries category, age, one relevance sentence and source coverage", () => {
    const [first] = latestDevelopments(dossier());

    expect(first.category).toBe("Regulatory");
    expect(first.age).toBe("20 hours ago");
    expect(first.relevance).toContain("CFTC");
    expect(first.sourceCoverage).toBe("Reported by 2 sources");
  });

  it("counts repeated coverage as sources, never as confirmation", () => {
    const developments = latestDevelopments(dossier());

    expect(developments[1].sourceCoverage).toBe("One source");
  });

  it("never turns multi-source coverage into a claim of verification", () => {
    // Repeated reporting is coverage. Two outlets carrying one account
    // are two reports of it and not a check on it, and no typed carrier
    // reaching here establishes that anything was verified. The field
    // is named for what it holds so a later reader cannot borrow a
    // stronger claim from a looser name.
    const multiSource = latestDevelopments(dossier())[0];

    expect(multiSource.sourceCoverage).toBe("Reported by 2 sources");
    expect(multiSource.sources).toHaveLength(2);

    const blob = JSON.stringify(latestDevelopments(dossier())).toLowerCase();

    for (const claim of [
      "verified",
      "verification",
      "confirmed",
      "corroborated",
      "independently",
      "source agreement",
    ]) {
      expect(blob).not.toContain(claim);
    }

    // And the carrier itself offers no field a claim of verification
    // could be written into.
    expect(Object.keys(multiSource)).not.toContain("verification");
  });
});
