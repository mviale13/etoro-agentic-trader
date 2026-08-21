import { describe, expect, it } from "vitest";

import {
  GROUP_ROWS,
  askingCourses,
  blockedCases,
  blockerCell,
  convictionCell,
  isComparable,
  movementLabel,
} from "./HomeSections";
import type { CycleCourse, CycleReview } from "@/lib/api/cycle-review";

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
