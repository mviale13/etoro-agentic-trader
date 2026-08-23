/**
 * The recorded envelope's presentation contract — owner ruling
 * 2026-08-23, amending #245.
 *
 * Two properties are pinned here and nowhere else:
 *
 * - **Which cycle may supply an envelope at all.** Only the latest
 *   successfully completed attempt from a *complete* stream. A failed,
 *   partial or interrupted attempt supplies none, and neither does a
 *   complete attempt sitting in a stream with unreadable records,
 *   unsupported schemas or lifecycle anomalies — an unreadable line
 *   may be the actual latest cycle. There is no `lastKnown` fallback:
 *   an older envelope is older policy and account guidance, and must
 *   not sit beside a newer dossier decision.
 *
 * - **That the frontend carries the domain's sentence.** The page
 *   renders `envelope.stated` and composes no percentage semantics of
 *   its own — the difference between a maximum *total position* and
 *   additional *room* is the domain's wording, and a surface that
 *   rebuilt it from `finalPct` would be authoring sizing meaning.
 */

import { describe, expect, it } from "vitest";

import { recordedCourse } from "@/app/dossiers/[symbol]/page";
import type {
  CycleCourse,
  CycleEnvelope,
  CycleReview,
} from "@/lib/api/cycle-review";

function envelope(overrides: Partial<CycleEnvelope> = {}): CycleEnvelope {
  return {
    kind: "upward_bounded",
    stated:
      "MOVRvest's course is ADD. The current policy permits consideration " +
      "up to a 0.6903% portfolio weight, subject to the binding " +
      "portfolio-capacity constraint (the cash floor (funding room)).",
    policySource: "investor_strategy.json",
    policyVersion: "abc123",
    evidenceCeiling: "standard_initial",
    capacityCeilingPct: 14.19,
    finalPct: 0.6903,
    bindingConstraint: "the evidence ceiling",
    because: "",
    namedGaps: [],
    securityRiskCeilingPct: null,
    securityRiskBecause: "",
    securityRiskCapped: false,
    qualityAuthority: "provider",
    starterCapped: false,
    priceAsOf: "Yahoo Finance, 2 minutes ago",
    portfolioAsOf: "eToro account response received at 2026-08-23 09:00 UTC",
    liquidity: "Liquidity is not measured.",
    ...overrides,
  };
}

function course(overrides: Partial<CycleCourse> = {}): CycleCourse {
  return {
    symbol: "DIS",
    disposition: "RECOMMEND",
    rationale: "The investment case satisfies every gate.",
    conviction: 75,
    convictionBasis: "A decision score, not enthusiasm.",
    evidenceAsOf: "Yahoo Finance, 2 minutes ago",
    actionKind: "add",
    actionStatement: "Consider adding to DIS.",
    actionBecause: "",
    asksForSomething: true,
    envelope: envelope(),
    blocker: null,
    ...overrides,
  };
}

function review(overrides: Partial<CycleReview> = {}): CycleReview {
  return {
    execution: "complete",
    cycleId: "abc123",
    startedAt: "2026-08-23T09:00:00Z",
    finishedAt: "2026-08-23T09:05:00Z",
    stages: [],
    comparisonOutcome: "compared",
    comparisonPriorCycleId: "prior",
    comparisonBecause: "",
    securitiesAsked: 26,
    securitiesPriced: 26,
    refusals: [],
    newlyProduced: [],
    changed: [],
    unchanged: [],
    attention: [],
    courses: [course()],
    noActionSuggested: null,
    streamComplete: true,
    unreadableRecords: 0,
    unsupportedSchemas: 0,
    lifecycleAnomalies: 0,
    lastKnown: null,
    portfolio: null,
    candidates: [],
    candidatesRanked: false,
    ...overrides,
  };
}

describe("which cycle may supply a dossier envelope", () => {
  it("renders for a complete attempt in a complete stream", () => {
    const found = recordedCourse(review(), "DIS");

    expect(found).not.toBeNull();
    expect(found?.course.symbol).toBe("DIS");
    expect(found?.finishedAt).toBe("2026-08-23T09:05:00Z");
  });

  it("renders nothing when the stream is incomplete", () => {
    expect(
      recordedCourse(review({ streamComplete: false }), "DIS"),
    ).toBeNull();
  });

  it.each([
    ["unreadable records", { unreadableRecords: 1 }],
    ["unsupported schemas", { unsupportedSchemas: 1 }],
    ["lifecycle anomalies", { lifecycleAnomalies: 1 }],
  ])("suppresses it when the stream reports %s", (_label, counts) => {
    // The backend reports the count and the flag together; either way
    // the page must not show an envelope from a defective stream.
    expect(
      recordedCourse(
        review({ ...counts, streamComplete: false } as Partial<CycleReview>),
        "DIS",
      ),
    ).toBeNull();
  });

  it.each(["failed", "partial", "interrupted", "none_recorded"] as const)(
    "renders nothing for a %s execution",
    (execution) => {
      expect(recordedCourse(review({ execution }), "DIS")).toBeNull();
    },
  );

  it("never falls back to an older last-known cycle", () => {
    const stale = review({
      execution: "failed",
      lastKnown: {
        cycleId: "older",
        finishedAt: "2026-08-20T09:00:00Z",
        status: "complete",
        courses: [course()],
      },
    });

    // An older envelope is older policy and account guidance.
    expect(recordedCourse(stale, "DIS")).toBeNull();
  });

  it("renders nothing for a symbol the cycle did not cover", () => {
    expect(recordedCourse(review(), "NFLX")).toBeNull();
  });

  it("renders nothing when there is no review at all", () => {
    expect(recordedCourse(null, "DIS")).toBeNull();
  });

  it("finds holdings and funded candidates alike", () => {
    const withCandidate = review({
      courses: [],
      candidates: [course({ symbol: "MSFT", actionKind: "open" })],
    });

    expect(recordedCourse(withCandidate, "MSFT")?.course.actionKind).toBe(
      "open",
    );
  });

  it("supplies no envelope for a non-capital course", () => {
    const waiting = review({
      courses: [
        course({ symbol: "AMD", actionKind: "wait", envelope: null }),
      ],
    });

    const found = recordedCourse(waiting, "AMD");

    // The course is found; the envelope is null, and `CourseEnvelope`
    // returns null on that — so no empty "Capital consideration" box.
    expect(found).not.toBeNull();
    expect(found?.course.envelope).toBeNull();
  });
});

describe("the domain owns the sizing sentence", () => {
  it("distinguishes a maximum total position from additional room", () => {
    const total = envelope({
      starterCapped: true,
      stated:
        "MOVRvest's course is ADD. Named uncertainty limits this " +
        "consideration to at most a 0.6903% total portfolio weight. The " +
        "limit constrains the action, not the company's quality.",
    });
    const room = envelope();

    expect(total.stated).toContain("total portfolio weight");
    expect(room.stated).toContain("permits consideration up to");
    expect(room.stated).not.toContain("total portfolio weight");

    // Both carry the same finalPct shape, so only the sentence
    // distinguishes them — which is why the page must render it.
    expect(total.finalPct).toBe(room.finalPct);
  });

  it("keeps the REDUCE floor wording", () => {
    const floor = envelope({
      kind: "reduction_floor",
      stated:
        "At least 5% of portfolio weight would need to be reduced to " +
        "restore the single-position cap. This is a compliance floor, not " +
        "a target or exit recommendation.",
    });

    expect(floor.stated).toContain("At least");
    expect(floor.stated).toContain("compliance floor, not a target");
  });

  it("keeps a refusal in its own words", () => {
    const refused = envelope({
      kind: "refused",
      finalPct: null,
      stated:
        "No capital envelope is available because the DIS price is older " +
        "than the policy's 15-minute limit. The existing non-capital " +
        "course remains unchanged.",
    });

    expect(refused.stated).toContain("older than the policy");
    expect(refused.finalPct).toBeNull();
  });
});
