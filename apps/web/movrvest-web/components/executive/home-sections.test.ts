import { describe, expect, it } from "vitest";

import {
  GROUP_ROWS,
  askingCourses,
  blockedCases,
  blockerCell,
  convictionCell,
  isComparable,
  movementLabel,
  strategyCardShape,
  targetTotal,
} from "./HomeSections";
import type {
  CycleCourse,
  CycleReview,
  RecordedPortfolio,
} from "@/lib/api/cycle-review";

/**
 * The rules the homepage encodes, each one a place it could invent a
 * finding: calling an uncompared security "Unchanged", reordering a
 * ranking the CIO produced, printing an em dash over a live blocker,
 * or printing a conviction with nothing to say what it is.
 */

function review(overrides: Partial<CycleReview> = {}): CycleReview {
  return {
    execution: "complete",
    cycleId: "c1",
    startedAt: null,
    finishedAt: null,
    stages: [],
    comparisonOutcome: "compared",
    comparisonPriorCycleId: "c0",
    comparisonBecause: "",
    securitiesAsked: 0,
    securitiesPriced: 0,
    refusals: [],
    newlyProduced: ["NEW"],
    changed: ["CHG"],
    unchanged: ["SAME"],
    attention: [],
    courses: [],
    noActionSuggested: null,
    streamComplete: true,
    unreadableRecords: 0,
    unsupportedSchemas: 0,
    lifecycleAnomalies: 0,
    lastKnown: null,
    portfolio: null,
    candidates: [],
    ...overrides,
  };
}

function course(
  symbol: string,
  overrides: Partial<CycleCourse> = {},
): CycleCourse {
  return {
    symbol,
    disposition: "PREPARE",
    rationale: "",
    conviction: null,
    convictionBasis: "",
    evidenceAsOf: "",
    actionKind: "wait",
    actionStatement: "Wait.",
    actionBecause: "",
    asksForSomething: false,
    envelope: null,
    blocker: null,
    ...overrides,
  };
}

describe("movement is only claimed where it was measured", () => {
  it("labels each measured movement from the record", () => {
    const current = review();

    expect(movementLabel(current, "NEW")).toBe("New");
    expect(movementLabel(current, "CHG")).toBe("Changed");
    expect(movementLabel(current, "SAME")).toBe("Unchanged");
  });

  it("never says Unchanged when the history is incomplete", () => {
    const current = review({ streamComplete: false });

    expect(isComparable(current)).toBe(false);

    for (const symbol of ["NEW", "CHG", "SAME"]) {
      expect(movementLabel(current, symbol)).toBe("Not compared");
    }
  });

  it.each(["initial_baseline", "refused"] as const)(
    "never says Unchanged on a %s comparison",
    (outcome) => {
      const current = review({ comparisonOutcome: outcome });

      expect(movementLabel(current, "SAME")).toBe("Not compared");
    },
  );

  it("never says Unchanged when no comparison was recorded at all", () => {
    expect(movementLabel(review({ comparisonOutcome: null }), "SAME")).toBe(
      "Not compared",
    );
  });
});

describe("what the CIO evaluated is two groups, not one ranking", () => {
  /** The live five, as the recorded cycle produced them. */
  const evaluated = [
    course("GRE.MC", {
      disposition: "INVESTIGATE",
      asksForSomething: true,
      actionStatement: "Research GRE.MC before the thesis can progress.",
      conviction: 61,
      convictionBasis: "the mean of the 5 scores measured",
    }),
    course("AMD", {
      disposition: "REJECT",
      actionKind: "none",
      actionStatement: "No action on AMD.",
      conviction: 40,
      convictionBasis: "capped at 40 by the REJECT state",
      blocker: {
        kind: "risk_gate",
        stated: "Blocked by the current risk policy: risk 85 against 70.",
        despite: ["Growth is strong."],
        doesNotSay: "This is a risk ruling.",
      },
    }),
    course("UUUU", { disposition: "REJECT", actionKind: "none" }),
    course("MSFT", { disposition: "PREPARE" }),
    course("HYPE", { disposition: "INVESTIGATE", asksForSomething: true }),
  ];

  it("splits on the platform's own bit, never on the state string", () => {
    expect(askingCourses(evaluated).map((c) => c.symbol)).toEqual([
      "GRE.MC",
      "HYPE",
    ]);

    expect(blockedCases(evaluated).map((c) => c.symbol)).toEqual([
      "AMD",
      "UUUU",
      "MSFT",
    ]);
  });

  it("keeps the server's order inside each group", () => {
    const many = ["A", "B", "C", "D"].map((symbol) =>
      course(symbol, { asksForSomething: true }),
    );

    expect(
      askingCourses(many)
        .slice(0, GROUP_ROWS)
        .map((c) => c.symbol),
    ).toEqual(["A", "B", "C"]);
  });
});

describe("a blocked case never renders an em dash", () => {
  it("prints the deciding layer's own sentence", () => {
    const amd = course("AMD", {
      blocker: {
        kind: "risk_gate",
        stated:
          "Blocked by the current risk policy: annualised volatility was " +
          "71.8%, placing AMD in this platform's severe-risk band and " +
          "producing risk 85 against a maximum of 70.",
        despite: ["Growth is strong — Revenue growth is 50.1%."],
        doesNotSay: "This is a risk ruling. It does not say AMD is a weak business.",
      },
    });

    const cell = blockerCell(amd);

    expect(cell).toContain("71.8%");
    expect(cell).toContain("85");
    expect(cell).not.toBe("—");
  });

  it("says a record carries no blocker rather than that nothing blocks", () => {
    expect(blockerCell(course("OLD"))).toBe("Not recorded for this review");
  });
});

describe("a conviction is never shown alone", () => {
  it("shows the number with its state once a basis exists", () => {
    expect(
      convictionCell(
        course("AMD", {
          disposition: "REJECT",
          conviction: 40,
          convictionBasis: "capped at 40 by the REJECT state",
        }),
      ),
    ).toBe("40 (REJECT)");
  });

  it("withholds the number where nothing says what it is", () => {
    expect(convictionCell(course("AMD", { conviction: 40 }))).toBe("Not stated");
  });

  it("carries the withholding reason where the CIO stated none", () => {
    expect(
      convictionCell(
        course("BTC", {
          convictionBasis: "No conviction is stated: this case cites no support.",
        }),
      ),
    ).toBe("No conviction is stated: this case cites no support.");
  });
});

/**
 * The owner's amendment to #247: a refused allocation policy must not
 * still render a plan.
 *
 * `strategyCardShape` is the branch the card takes and the only one it
 * takes, so these are assertions about what an investor sees — not a
 * re-implementation of it. The defect: `CapitalPolicyService` refused
 * targets totalling 105% while `InvestmentPolicyMapper` mapped those
 * same 105% onto the page, and the refusal reached no reader.
 */
function recordedPortfolio(
  overrides: Partial<RecordedPortfolio> = {},
): RecordedPortfolio {
  return {
    totalValue: 10_000,
    availableCashUsd: 5_407,
    cashPct: 54.07,
    observed: "",
    holdings: [],
    allocations: [
      {
        asset: "stocks",
        currentPct: 10.3,
        targetPct: 35,
        differencePct: -24.7,
        minimumPct: 25,
        maximumPct: 45,
        standing: "below_range",
        stated: "Below the operating range.",
      },
      {
        asset: "cash",
        currentPct: 54.07,
        targetPct: 25,
        differencePct: 29.07,
        minimumPct: 15,
        maximumPct: 45,
        standing: "above_range",
        stated: "Above the operating range.",
      },
    ],
    compliant: false,
    allocationGuidance: "Cash is above its operating range.",
    allocationGuidanceRefused: "",
    allocationPolicyRefused: "",
    ...overrides,
  };
}

/** The record a refused policy produces: measured, and with no plan. */
function refusedPortfolio(): RecordedPortfolio {
  return recordedPortfolio({
    allocations: [
      {
        asset: "stocks",
        currentPct: 10.3,
        targetPct: null,
        differencePct: null,
        minimumPct: null,
        maximumPct: null,
        standing: "",
        stated: "",
      },
      {
        asset: "cash",
        currentPct: 54.07,
        targetPct: null,
        differencePct: null,
        minimumPct: null,
        maximumPct: null,
        standing: "",
        stated: "",
      },
    ],
    compliant: null,
    allocationGuidance: "",
    allocationPolicyRefused:
      "the owner strategy is contradictory: the four strategic targets must " +
      "total 100%, and they total 105%",
  });
}

describe("a refused allocation policy shows no plan", () => {
  it("renders the refusal instead of the strategic target table", () => {
    expect(strategyCardShape(refusedPortfolio())).toBe("policy-refused");
  });

  it("renders the plan where the policy validated", () => {
    expect(strategyCardShape(recordedPortfolio())).toBe("plan");
  });

  it("keeps a review that recorded no allocation distinct from a refusal", () => {
    expect(strategyCardShape(recordedPortfolio({ allocations: [] }))).toBe(
      "no-comparison",
    );
    expect(strategyCardShape(null)).toBe("no-comparison");
  });

  it("prefers the refusal even where allocations were recorded", () => {
    // The measured shares are still there — refusing the plan must not
    // erase the account — and they are still not a plan.
    const portfolio = refusedPortfolio();

    expect(portfolio.allocations).toHaveLength(2);
    expect(strategyCardShape(portfolio)).toBe("policy-refused");
  });
});

describe("the strategic targets total, or state no total", () => {
  it("adds the four targets up where every one is stated", () => {
    expect(targetTotal(recordedPortfolio().allocations)).toBe(60);
  });

  it("states no total rather than 0% where a target is missing", () => {
    // The misleading "Total 0%" the amendment forbids: four absent
    // targets summed as four zeros would read as a plan allocating
    // nothing, which is not what a refused policy means.
    expect(targetTotal(refusedPortfolio().allocations)).toBeNull();

    expect(
      targetTotal([
        ...recordedPortfolio().allocations,
        {
          asset: "crypto",
          currentPct: 35.63,
          targetPct: null,
          differencePct: null,
          minimumPct: null,
          maximumPct: null,
          standing: "",
          stated: "",
        },
      ]),
    ).toBeNull();
  });
});
