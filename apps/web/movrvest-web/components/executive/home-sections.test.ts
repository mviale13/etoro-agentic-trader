import { describe, expect, it } from "vitest";

import {
  isComparable,
  movementLabel,
  topOpportunities,
} from "./HomeSections";
import type { CycleCourse, CycleReview } from "@/lib/api/cycle-review";

/**
 * The two rules the homepage's tables encode.
 *
 * Both are places a page could quietly invent a finding: calling an
 * uncompared security "Unchanged", or reordering a ranking the CIO
 * produced. Neither is allowed.
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

function course(symbol: string): CycleCourse {
  return {
    symbol,
    disposition: "PREPARE",
    rationale: "",
    conviction: null,
    evidenceAsOf: "",
    actionKind: "wait",
    actionStatement: "Wait.",
    actionBecause: "",
    asksForSomething: false,
    envelope: null,
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

describe("the opportunities table", () => {
  it("shows five and keeps the CIO's order", () => {
    const ranked = ["A", "B", "C", "D", "E", "F", "G"].map(course);

    const top = topOpportunities(ranked);

    expect(top).toHaveLength(5);
    expect(top.map((c) => c.symbol)).toEqual(["A", "B", "C", "D", "E"]);
  });

  it("shows fewer without padding when fewer were evaluated", () => {
    expect(topOpportunities([course("A")])).toHaveLength(1);
    expect(topOpportunities([])).toHaveLength(0);
  });
});
