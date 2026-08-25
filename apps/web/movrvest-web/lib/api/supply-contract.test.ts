import { describe, expect, it } from "vitest";

import { parseSupply } from "./crypto-dossier";

/**
 * The supply wire contract, at its boundary.
 *
 * A verdict is a closed enum. An unrecognised value means a backend
 * this parser does not understand, and treating it as anything — least
 * of all as a conflict — would report a disagreement to an investor on
 * the strength of a word nobody here has read.
 */

function wire(overrides: Record<string, unknown> = {}) {
  return {
    figures: [
      {
        concept: "max_supply",
        concept_stated: "Protocol maximum",
        stated: "21,000,000 tokens",
        defined_by: "The protocol",
        methodology: "As published.",
        disclosed: true,
        excludes: [],
        source: "TokenInsight",
        age: "TokenInsight, yesterday",
        standing_stated: "Provider claim",
        authority_stated: "Provider aggregate",
        because: null,
        caveats: [],
      },
    ],
    comparisons: [
      {
        verdict: "corroborated",
        verdict_stated: "Agree",
        left_source: "A",
        left_stated: "21m",
        right_source: "B",
        right_stated: "21m",
        left_concept: "max_supply",
        right_concept: "max_supply",
        because: "Same quantity, same figure.",
      },
    ],
    methodology_disagreement: false,
    unresolved: [{ stated: "No chain reading for BTC.", concept: null }],
    unavailable_because: null,
    ...overrides,
  };
}

describe("the supply wire contract", () => {
  it("accepts each of the three verdicts", () => {
    for (const verdict of ["corroborated", "conflicted", "coexist"]) {
      const parsed = parseSupply(
        wire({
          comparisons: [{ ...wire().comparisons[0], verdict }],
        }),
      );

      expect(parsed.comparisons[0].verdict).toBe(verdict);
    }
  });

  it("fails the contract on an unknown verdict rather than guessing", () => {
    for (const rogue of ["agrees", "CORROBORATED", "unknown", "", null, 7]) {
      expect(() =>
        parseSupply(
          wire({ comparisons: [{ ...wire().comparisons[0], verdict: rogue }] }),
        ),
      ).toThrow(/corroborated, conflicted, coexist/);
    }
  });

  it("never silently degrades an unknown verdict to a conflict", () => {
    let parsed: ReturnType<typeof parseSupply> | null = null;

    try {
      parsed = parseSupply(
        wire({
          comparisons: [{ ...wire().comparisons[0], verdict: "probably_agrees" }],
        }),
      );
    } catch {
      parsed = null;
    }

    expect(parsed).toBeNull();
  });

  it("carries both concepts and the typed unresolved shape", () => {
    const parsed = parseSupply(wire());

    expect(parsed.comparisons[0].leftConcept).toBe("max_supply");
    expect(parsed.comparisons[0].rightConcept).toBe("max_supply");
    expect(parsed.unresolved[0]).toEqual({
      stated: "No chain reading for BTC.",
      concept: null,
    });
  });

  it("requires a concept key on every comparison", () => {
    const missing = { ...wire().comparisons[0] } as Record<string, unknown>;

    delete missing.left_concept;

    expect(() => parseSupply(wire({ comparisons: [missing] }))).toThrow();
  });
});
