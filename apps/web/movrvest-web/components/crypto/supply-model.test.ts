import { describe, expect, it } from "vitest";

import type { SupplyView } from "@/lib/api/crypto-dossier";

import { supplyModel } from "./supply-model";

/**
 * The supply summary's rules, at the selector layer.
 *
 * Fixtures mirror the live corpus measured in Stage 0: HYPE (14
 * figures, 10 same-concept comparisons, 4 circulating readings), BTC
 * (all corroborated, no exclusions), TAO (conflicted, caveats) and ADA
 * (the live `coexist` cross-concept case).
 */

function figure(
  concept: string,
  conceptStated: string,
  source: string,
  stated: string,
  overrides: Record<string, unknown> = {},
) {
  return {
    concept,
    conceptStated,
    stated,
    definedBy: `${source} defines it.`,
    methodology: "As published.",
    disclosed: true,
    excludes: [],
    source,
    age: `${source}, yesterday`,
    standingStated: "Provider claim",
    authorityStated: "Provider aggregate",
    because: null,
    caveats: [],
    ...overrides,
  };
}

function comparison(
  verdict: "corroborated" | "conflicted" | "coexist",
  verdictStated: string,
  leftConcept: string,
  rightConcept: string,
  overrides: Record<string, unknown> = {},
) {
  return {
    verdict,
    verdictStated,
    leftSource: "A",
    leftStated: "1",
    rightSource: "B",
    rightStated: "2",
    leftConcept,
    rightConcept,
    because: `${leftConcept} vs ${rightConcept}.`,
    ...overrides,
  };
}

function supply(overrides: Partial<SupplyView> = {}): SupplyView {
  return {
    figures: [],
    comparisons: [],
    methodologyDisagreement: false,
    unresolved: [],
    unavailableBecause: null,
    ...overrides,
  } as unknown as SupplyView;
}

/** HYPE as Stage 0 measured it. */
function hype(): SupplyView {
  return supply({
    figures: [
      figure("max_supply", "Protocol maximum", "Hyperliquid info API", "1,000,000,000 HYPE"),
      figure("max_supply", "Protocol maximum", "TokenInsight", "1,000,000,000 tokens"),
      figure("max_supply", "Protocol maximum", "CoinGecko", "1,000,000,000 tokens"),
      figure("emitted_supply", "Emitted supply", "Hyperliquid info API", "586,861,713 HYPE"),
      figure("emitted_supply", "Emitted supply", "CoinGecko", "955,307,079 tokens"),
      figure("future_emissions", "Future unissued supply", "Hyperliquid info API", "412,138,286 HYPE"),
      figure("circulating_estimate", "Circulating supply", "Hyperliquid info API", "298,748,584 HYPE"),
      figure("circulating_estimate", "Circulating supply", "TokenInsight", "336,685,219 tokens"),
      figure("circulating_estimate", "Circulating supply", "CoinGecko", "222,445,714 tokens"),
      figure("circulating_estimate", "Circulating supply", "Yahoo Finance", "1,500,000,000 tokens"),
      figure("excluded_balance", "Excluded balance", "Hyperliquid info API", "1 HYPE"),
      figure("excluded_balance", "Excluded balance", "Hyperliquid info API", "2 HYPE"),
      figure("excluded_balance", "Excluded balance", "Hyperliquid info API", "3 HYPE"),
      figure("excluded_balance", "Excluded balance", "Hyperliquid info API", "4 HYPE"),
    ],
    comparisons: [
      comparison("conflicted", "Conflict", "emitted_supply", "emitted_supply"),
      // 4 circulating readings → C(4,2) = 6 conflicts.
      ...Array.from({ length: 6 }, () =>
        comparison("conflicted", "Conflict", "circulating_estimate", "circulating_estimate"),
      ),
      ...Array.from({ length: 3 }, () =>
        comparison("corroborated", "Agree", "max_supply", "max_supply"),
      ),
    ],
    unresolved: [
      {
        stated:
          "The exclusion set behind CoinGecko is not published, so this platform cannot say whether it counts the same tokens as anyone else's.",
        concept: "circulating_estimate",
      },
    ],
  });
}

// ── the corrected settlement rule ───────────────────────────────────

describe("settlement keys on the typed verdict", () => {
  it("shows the agreed protocol maximum once, from three aligning reports", () => {
    // The regression this pin exists for: the backend's word for
    // agreement is "Agree", so matching `verdictStated` against
    // "corroborated" counted every corroboration as a conflict and this
    // row read "Not settled" — the exact opposite of the truth.
    const model = supplyModel(hype());
    const max = model.rows.find((row) => row.concept === "max_supply");

    expect(max?.stated).toBe("1,000,000,000 HYPE");
    expect(max?.status).toBe("3 reports align");
    expect(max?.sourceCount).toBe(3);
  });

  it("never reads a state out of the display sentence", () => {
    // Same typed verdicts, nonsense display prose: the answer must not
    // move.
    const wording = supply({
      figures: hype().figures.filter((f) => f.concept === "max_supply"),
      comparisons: Array.from({ length: 3 }, () =>
        comparison("corroborated", "Wörter die niemand liest", "max_supply", "max_supply"),
      ),
    });

    expect(supplyModel(wording).rows[0].stated).toBe("1,000,000,000 HYPE");
    expect(supplyModel(wording).rows[0].status).toBe("3 reports align");
  });

  it("leaves a conflicted quantity unsettled and picks no provider", () => {
    const model = supplyModel(hype());
    const circulating = model.rows.find(
      (row) => row.concept === "circulating_estimate",
    );

    expect(circulating?.stated).toBeNull();
    expect(circulating?.status).toBe("Reported figures conflict");

    // No figure from any of the four readings leaks into the row.
    const blob = JSON.stringify(circulating);

    for (const reading of ["298,748,584", "336,685,219", "222,445,714", "1,500,000,000"]) {
      expect(blob).not.toContain(reading);
    }
  });

  it("does not call several uncompared facts a disagreement", () => {
    // HYPE's four excluded balances are four *addresses* from one
    // source — 241.4m, 46.7m, 1,673.8 and 2.7 HYPE — and the domain
    // never compared them, because they are not rival claims to one
    // quantity. Reading "multiple figures, no agreement" as a conflict
    // manufactured a controversy nobody observed and then told the
    // investor a quantity was unsettled.
    const model = supplyModel(hype());
    const excluded = model.rows.find(
      (row) => row.concept === "excluded_balance",
    );

    expect(excluded?.unsettledKind).toBe("several");
    expect(excluded?.status).toBe("4 reported values");
    expect(excluded?.stated).toBeNull();

    // ...and it is therefore NOT in the unsettled panel.
    expect(
      model.unsettled.some((item) => item.stated.startsWith("Excluded")),
    ).toBe(false);
  });

  it("totals nothing for a grouped concept", () => {
    const model = supplyModel(hype());
    const excluded = model.rows.find(
      (row) => row.concept === "excluded_balance",
    );

    // The four balances sum to something; the backend owns no total, so
    // neither does this.
    expect(excluded?.because).toBe(
      "Listed separately below; this platform totals nothing.",
    );
    expect(JSON.stringify(excluded)).not.toMatch(/288|sum|total(?!s nothing)/i);
  });

  it("marks a real conflict as conflicted, not as several", () => {
    const model = supplyModel(hype());

    expect(
      model.rows.find((row) => row.concept === "circulating_estimate")
        ?.unsettledKind,
    ).toBe("conflicted");
    expect(
      model.rows.find((row) => row.concept === "emitted_supply")?.unsettledKind,
    ).toBe("conflicted");
    expect(
      model.rows.find((row) => row.concept === "max_supply")?.unsettledKind,
    ).toBeNull();
  });

  it("requires the complete comparison graph before claiming alignment", () => {
    // Three reports, only one pair examined. Saying "3 reports align"
    // would recruit the third into an agreement nobody tested and
    // present its figure as corroborated on the strength of the other
    // two. C(3,2) = 3 pairs are required.
    const partial = supply({
      figures: [
        figure("max_supply", "Protocol maximum", "A", "21m"),
        figure("max_supply", "Protocol maximum", "B", "21m"),
        figure("max_supply", "Protocol maximum", "C", "21m"),
      ],
      comparisons: [
        comparison("corroborated", "Agree", "max_supply", "max_supply"),
      ],
    });

    const row = supplyModel(partial).rows[0];

    expect(row.unsettledKind).toBe("incomplete");
    expect(row.stated).toBeNull();
    expect(row.status).toBe("1 of 3 pairs compared");
    expect(row.because).toContain("were not compared");
  });

  it("claims alignment once every pair is examined and agrees", () => {
    const complete = supply({
      figures: [
        figure("max_supply", "Protocol maximum", "A", "21m"),
        figure("max_supply", "Protocol maximum", "B", "21m"),
        figure("max_supply", "Protocol maximum", "C", "21m"),
      ],
      comparisons: Array.from({ length: 3 }, () =>
        comparison("corroborated", "Agree", "max_supply", "max_supply"),
      ),
    });

    const row = supplyModel(complete).rows[0];

    expect(row.unsettledKind).toBeNull();
    expect(row.status).toBe("3 reports align");
    expect(row.stated).toBe("21m");
  });

  it("an incomplete graph is not a disagreement", () => {
    const partial = supply({
      figures: [
        figure("max_supply", "Protocol maximum", "A", "21m"),
        figure("max_supply", "Protocol maximum", "B", "21m"),
        figure("max_supply", "Protocol maximum", "C", "21m"),
      ],
      comparisons: [
        comparison("corroborated", "Agree", "max_supply", "max_supply"),
      ],
    });

    const model = supplyModel(partial);

    // It still cannot be presented as one figure, so it is named — but
    // never as sources disagreeing.
    expect(model.unsettled).toHaveLength(1);
    expect(JSON.stringify(model.unsettled)).not.toMatch(/conflict|disagree/i);
  });

  it("presents a lone report as exactly that", () => {
    const model = supplyModel(hype());
    const future = model.rows.find((row) => row.concept === "future_emissions");

    expect(future?.stated).toBe("412,138,286 HYPE");
    expect(future?.status).toBe("One report");
  });

  it("computes no range, total, midpoint or dilution anywhere", () => {
    const blob = JSON.stringify(supplyModel(hype()));

    for (const invented of ["dilution", "midpoint", "average", "range", "total of"]) {
      expect(blob.toLowerCase()).not.toContain(invented);
    }
  });

  it("never upgrades a provider claim to established or verified", () => {
    const blob = JSON.stringify(supplyModel(hype())).toLowerCase();

    expect(blob).not.toContain("established");
    expect(blob).not.toContain("verified");
  });
});

// ── grouping by the typed concept ───────────────────────────────────

describe("grouping", () => {
  it("puts every figure under its own concept, in reading order", () => {
    const model = supplyModel(hype());

    expect(model.groups.map((group) => group.concept)).toEqual([
      "max_supply",
      "emitted_supply",
      "circulating_estimate",
      "future_emissions",
      "excluded_balance",
    ]);

    const counts = Object.fromEntries(
      model.groups.map((group) => [group.concept, group.figures.length]),
    );

    expect(counts).toEqual({
      max_supply: 3,
      emitted_supply: 2,
      circulating_estimate: 4,
      future_emissions: 1,
      excluded_balance: 4,
    });
  });

  it("assigns a comparison to a concept only when both sides claim it", () => {
    const model = supplyModel(hype());
    const byConcept = Object.fromEntries(
      model.groups.map((group) => [group.concept, group.comparisons.length]),
    );

    expect(byConcept.circulating_estimate).toBe(6);
    expect(byConcept.max_supply).toBe(3);
    expect(byConcept.emitted_supply).toBe(1);
  });

  it("keeps a cross-concept coexist comparison out of both groups", () => {
    // ADA's live case: TokenInsight reports the ledger's `supply` and
    // Yahoo its `circulation`. Filing that under either quantity would
    // name a winner between two things that are not rivals.
    const ada = supply({
      figures: [
        figure("emitted_supply", "Emitted supply", "TokenInsight", "36bn"),
        figure("circulating_estimate", "Circulating supply", "Yahoo Finance", "35bn"),
      ],
      comparisons: [
        comparison(
          "coexist",
          "Measure different things",
          "emitted_supply",
          "circulating_estimate",
        ),
      ],
    });

    const model = supplyModel(ada);

    for (const group of model.groups) {
      expect(group.comparisons).toHaveLength(0);
    }

    // ...and it is still reachable, in the audit.
    expect(model.audit).toHaveLength(1);
    expect(model.audit[0].verdict).toBe("coexist");
  });

  it("keeps every comparison reachable in the audit", () => {
    const model = supplyModel(hype());

    expect(model.audit).toHaveLength(10);
  });

  it("omits a concept the token has no evidence for", () => {
    // BTC's control: no future emissions, no excluded balances. Those
    // groups must not appear as empty shells.
    const btc = supply({
      figures: [
        figure("max_supply", "Protocol maximum", "TokenInsight", "21,000,000 tokens"),
        figure("max_supply", "Protocol maximum", "CoinGecko", "21,000,000 tokens"),
        figure("emitted_supply", "Emitted supply", "CoinGecko", "19.9m"),
      ],
      comparisons: [comparison("corroborated", "Agree", "max_supply", "max_supply")],
    });

    const model = supplyModel(btc);

    expect(model.groups.map((group) => group.concept)).toEqual([
      "max_supply",
      "emitted_supply",
    ]);
    expect(model.rows.map((row) => row.concept)).toEqual([
      "max_supply",
      "emitted_supply",
    ]);
  });

  it("surfaces a concept this module's order does not name — in the summary too", () => {
    // A quantity added to the corpus after this constant was written
    // must not vanish, and must not appear only in the source detail:
    // evidence never falls out of the *answer* because a frontend
    // constant predates it.
    const exotic = supply({
      figures: [
        figure("max_supply", "Protocol maximum", "A", "21m"),
        figure("staked_balance", "Staked balance", "Chain", "5m"),
      ],
    });

    const model = supplyModel(exotic);

    expect(model.groups.map((group) => group.concept)).toContain("staked_balance");
    expect(model.rows.map((row) => row.concept)).toContain("staked_balance");

    // Known concepts keep their preferred order; the unknown one is
    // appended in served order rather than interleaved.
    expect(model.rows.map((row) => row.concept)).toEqual([
      "max_supply",
      "staked_balance",
    ]);
  });
});

// ── what remains unsettled ──────────────────────────────────────────

describe("the unsettled panel", () => {
  it("names each unsettled quantity and this platform's consequence", () => {
    const model = supplyModel(hype());
    const stated = model.unsettled.map((item) => item.stated);

    expect(stated).toContain("Circulating supply is not settled.");
    expect(stated).toContain("Emitted supply is not settled.");

    // Where the backend owns an account of the quantity, that account
    // *is* the consequence; where it does not, this layer states its
    // own. Either way there is exactly one per concept.
    const circulating = model.unsettled.find((item) =>
      item.stated.startsWith("Circulating"),
    );

    expect(circulating?.consequence).toContain("The exclusion set behind");

    const emitted = model.unsettled.find((item) =>
      item.stated.startsWith("Emitted"),
    );

    expect(emitted?.consequence).toBe(
      "MOVRvest therefore does not present one emitted supply figure.",
    );
  });

  it("draws no investment implication", () => {
    const blob = JSON.stringify(supplyModel(hype()).unsettled).toLowerCase();

    for (const forbidden of [
      "risk",
      "dilut",
      "attractive",
      "quality",
      "concern",
      "warning",
    ]) {
      expect(blob).not.toContain(forbidden);
    }
  });

  it("gives one canonical statement per unsettled concept", () => {
    // Two accounts of circulating supply used to stand side by side —
    // this layer's "not settled" and the backend's exclusion-set
    // sentence — and an investor counted the problem twice. The
    // backend's account is folded in **by its typed concept**, never by
    // comparing sentences, and becomes the row's reason.
    const model = supplyModel(hype());
    const circulating = model.unsettled.filter((item) =>
      item.stated.startsWith("Circulating"),
    );

    expect(circulating).toHaveLength(1);
    expect(circulating[0].consequence).toContain("The exclusion set behind");

    // ...and the original wording is not lost.
    expect(JSON.stringify(model.unsettled)).toContain(
      "cannot say whether it counts the same tokens",
    );

    // The load-bearing half: the backend's account appears **only** as
    // that row's reason, never as a second entry beside it. Filtering
    // on "Circulating" alone missed this, because the backend's
    // sentence opens with "The exclusion set behind".
    expect(model.unsettled).toHaveLength(2); // emitted + circulating
    expect(
      model.unsettled.filter((item) =>
        item.stated.includes("The exclusion set behind"),
      ),
    ).toHaveLength(0);
  });

  it("keeps a whole-picture gap as its own entry", () => {
    const model = supplyModel(
      supply({
        figures: [figure("max_supply", "Protocol maximum", "A", "21m")],
        unresolved: [
          { stated: "No chain reading for BTC.", concept: null },
        ],
      }),
    );

    expect(model.unsettled.map((item) => item.stated)).toEqual([
      "No chain reading for BTC.",
    ]);
  });

  it("is empty where everything is settled", () => {
    const settled = supply({
      figures: [
        figure("max_supply", "Protocol maximum", "A", "21m"),
        figure("max_supply", "Protocol maximum", "B", "21m"),
      ],
      comparisons: [comparison("corroborated", "Agree", "max_supply", "max_supply")],
    });

    expect(supplyModel(settled).unsettled).toEqual([]);
  });
});

// ── nothing is lost ─────────────────────────────────────────────────

describe("preservation", () => {
  it("keeps all fourteen figures and all ten comparisons reachable", () => {
    const model = supplyModel(hype());
    const figures = model.groups.flatMap((group) => group.figures);

    expect(figures).toHaveLength(14);
    expect(model.audit).toHaveLength(10);
  });

  it("keeps a figure's caveats attached to its own source row", () => {
    const withCaveat = supply({
      figures: [
        figure("max_supply", "Protocol maximum", "TokenInsight", "45bn", {
          caveats: ["Dated 15 days ago."],
          age: "TokenInsight, 15 days ago",
        }),
      ],
    });

    const group = supplyModel(withCaveat).groups[0];

    expect(group.figures[0].caveats).toEqual(["Dated 15 days ago."]);
    expect(group.figures[0].age).toBe("TokenInsight, 15 days ago");
  });

  it("carries the backend's absence sentence where nothing is held", () => {
    const nothing = supply({
      unavailableBecause: "No supply evidence is held for this asset.",
    });

    const model = supplyModel(nothing);

    expect(model.rows).toEqual([]);
    expect(model.groups).toEqual([]);
    expect(model.unavailableBecause).toBe(
      "No supply evidence is held for this asset.",
    );
  });
});
