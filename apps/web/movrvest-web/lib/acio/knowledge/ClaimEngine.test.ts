import { describe, expect, it } from "vitest";

import { ClaimEngine } from "./ClaimEngine";
import type { Evidence } from "./types";

const evidence: Evidence = {
  id: "evidence-cash-allocation",
  type: "portfolio.cash-allocation",
  subjectId: "portfolio-main",
  statement: "Cash represents 100% of portfolio value.",
  value: 1,
  source: "portfolio",
  observedAt: "2026-07-30T08:00:00.000Z",
  recordedAt: "2026-07-30T08:00:00.000Z",
  reliability: 1,
  freshness: 1,
  metadata: {},
};

const createEngine = (): ClaimEngine =>
  new ClaimEngine({
    createId: () => "claim-1",
    now: () => "2026-07-30T08:30:00.000Z",
  });

describe("ClaimEngine", () => {
  it("creates a deterministic observation", () => {
    const claim = createEngine().observation({
      subjectId: "portfolio-main",
      statement: "The portfolio is highly liquid.",
      rationale:
        "All portfolio capital is currently held in cash.",
      confidence: 0.95,
      evidence: [evidence],
      createdBy: "PortfolioReasoner",
    });

    expect(claim).toEqual({
      id: "claim-1",
      category: "observation",
      subjectId: "portfolio-main",
      statement: "The portfolio is highly liquid.",
      rationale:
        "All portfolio capital is currently held in cash.",
      confidence: 0.95,
      evidenceIds: ["evidence-cash-allocation"],
      opposingEvidenceIds: [],
      assumptions: [],
      missingInformation: [],
      questions: [],
      createdBy: "PortfolioReasoner",
      createdAt: "2026-07-30T08:30:00.000Z",
      status: "generated",
    });
  });

  it("rejects confidence outside the valid range", () => {
    expect(() =>
      createEngine().hypothesis({
        subjectId: "investor-main",
        statement:
          "The investor may be waiting for a better entry point.",
        confidence: 1.2,
        createdBy: "BehaviorReasoner",
      }),
    ).toThrow("Claim confidence must be between 0 and 1.");
  });

  it("requires evidence for observations", () => {
    expect(() =>
      createEngine().observation({
        subjectId: "portfolio-main",
        statement: "The portfolio is highly liquid.",
        confidence: 0.8,
        createdBy: "PortfolioReasoner",
      }),
    ).toThrow(
      'Claim category "observation" requires at least one supporting evidence item.',
    );
  });

  it("allows hypotheses without evidence", () => {
    const claim = createEngine().hypothesis({
      subjectId: "investor-main",
      statement:
        "The investor may currently be in a transition period.",
      confidence: 0.4,
      assumptions: [
        "The lack of active positions is intentional.",
      ],
      missingInformation: [
        "The investor's deployment timeline.",
      ],
      questions: [
        "Are you currently waiting before deploying capital?",
      ],
      createdBy: "PortfolioReasoner",
    });

    expect(claim.category).toBe("hypothesis");
    expect(claim.evidenceIds).toEqual([]);
  });

  it("normalizes duplicate strings and evidence", () => {
    const claim = createEngine().observation({
      subjectId: "portfolio-main",
      statement: "The portfolio is highly liquid.",
      confidence: 0.9,
      evidence: [evidence, evidence],
      assumptions: [" Cash remains available. ", "Cash remains available."],
      createdBy: "PortfolioReasoner",
    });

    expect(claim.evidenceIds).toEqual([
      "evidence-cash-allocation",
    ]);
    expect(claim.assumptions).toEqual([
      "Cash remains available.",
    ]);
  });

  it("confirms a generated claim", () => {
    const engine = createEngine();

    const claim = engine.observation({
      subjectId: "portfolio-main",
      statement: "The portfolio is highly liquid.",
      confidence: 0.9,
      evidence: [evidence],
      createdBy: "PortfolioReasoner",
    });

    expect(engine.confirm(claim).status).toBe("confirmed");
  });

  it("supersedes a claim with a replacement", () => {
    let identifier = 0;

    const engine = new ClaimEngine({
      createId: () => {
        identifier += 1;
        return `claim-${identifier}`;
      },
      now: () => "2026-07-30T08:30:00.000Z",
    });

    const original = engine.observation({
      subjectId: "portfolio-main",
      statement: "The portfolio is highly liquid.",
      confidence: 0.9,
      evidence: [evidence],
      createdBy: "PortfolioReasoner",
    });

    const replacement = engine.observation({
      subjectId: "portfolio-main",
      statement:
        "The portfolio remains liquid but now has active exposure.",
      confidence: 0.92,
      evidence: [evidence],
      createdBy: "PortfolioReasoner",
    });

    const superseded = engine.supersede(
      original,
      replacement,
    );

    expect(superseded.status).toBe("superseded");
    expect(superseded.supersededBy).toBe(replacement.id);
  });
});
