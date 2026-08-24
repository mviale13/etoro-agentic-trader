import { describe, expect, it } from "vitest";

import {
  CycleContractError,
  parseCycleReview,
  type CycleReview,
} from "./cycle-review";

/**
 * The parser must fail closed.
 *
 * It used to coerce: a missing `stream_complete` became `true`, missing
 * numbers became `0`, missing arrays became `[]`, and an unrecognised
 * execution string was cast straight into the enum. Each of those turns
 * a broken contract into a plausible fact — a page reporting a
 * complete, quiet, empty review because the payload was malformed.
 *
 * Every case below fails on the permissive parser and passes on this
 * one, which is what makes them discriminating rather than decorative.
 */

function valid(): Record<string, unknown> {
  return {
    execution: "complete",
    cycle_id: "c1",
    started_at: "2026-08-20T12:00:00Z",
    finished_at: "2026-08-20T12:05:00Z",
    stages: [{ name: "decisions", outcome: "ran", because: "" }],
    comparison_outcome: "initial_baseline",
    comparison_prior_cycle_id: "",
    comparison_because: "",
    securities_asked: 2,
    securities_priced: 2,
    refusals: [],
    newly_produced: [],
    changed: [],
    unchanged: [],
    attention: [],
    courses: [
      {
        symbol: "KO",
        disposition: "PREPARE",
        rationale: "held basis",
        conviction: null,
        conviction_basis: "",
        evidence_as_of: "",
        action_kind: "hold",
        action_statement: "Keep the position as it is.",
        action_because: "nothing moved",
        asks_for_something: false,
        envelope: null,
        blocker: null,
      },
    ],
    no_action_suggested: null,
    stream_complete: true,
    unreadable_records: 0,
    unsupported_schemas: 0,
    lifecycle_anomalies: 0,
    last_known: null,
    portfolio: null,
    candidates: [],
    candidates_ranked: true,
  };
}

function without(field: string): Record<string, unknown> {
  const body = valid();
  delete body[field];

  return body;
}

function withField(field: string, value: unknown): Record<string, unknown> {
  return { ...valid(), [field]: value };
}

describe("a well-formed response", () => {
  it("parses, and carries the contract's own values", () => {
    const review: CycleReview = parseCycleReview(valid());

    expect(review.execution).toBe("complete");
    expect(review.streamComplete).toBe(true);
    expect(review.courses).toHaveLength(1);
    expect(review.courses[0].symbol).toBe("KO");
    expect(review.noActionSuggested).toBeNull();
  });

  it("permits null exactly where the backend contract does", () => {
    const review = parseCycleReview({
      ...valid(),
      cycle_id: null,
      started_at: null,
      finished_at: null,
      comparison_outcome: null,
      no_action_suggested: null,
      last_known: null,
    });

    expect(review.cycleId).toBeNull();
    expect(review.comparisonOutcome).toBeNull();
  });
});

describe("a contract-invalid response yields no review", () => {
  it("rejects an omitted candidates_ranked rather than assuming ranked", () => {
    // Assuming `true` would let a page present an order of merit the
    // backend never claimed — prerequisite 2 of the owner's ruling of
    // 2026-08-21, failing closed like every other field here.
    expect(() => parseCycleReview(without("candidates_ranked"))).toThrow(
      CycleContractError,
    );
  });

  it("rejects an omitted stream_complete rather than assuming true", () => {
    // The permissive parser answered `true` here — a page reporting a
    // complete history because the field was missing.
    expect(() => parseCycleReview(without("stream_complete"))).toThrow(
      CycleContractError,
    );
  });

  it("rejects a non-boolean stream_complete", () => {
    expect(() => parseCycleReview(withField("stream_complete", "yes"))).toThrow(
      CycleContractError,
    );
  });

  it("rejects an unknown execution rather than casting it", () => {
    expect(() => parseCycleReview(withField("execution", "sideways"))).toThrow(
      CycleContractError,
    );
  });

  it("rejects a missing execution", () => {
    expect(() => parseCycleReview(without("execution"))).toThrow(
      CycleContractError,
    );
  });

  it("rejects an unknown comparison outcome", () => {
    expect(() =>
      parseCycleReview(withField("comparison_outcome", "maybe")),
    ).toThrow(CycleContractError);
  });

  it("rejects an unparseable timestamp rather than wording it away", () => {
    expect(() => parseCycleReview(withField("started_at", "not a date"))).toThrow(
      CycleContractError,
    );
  });

  it.each([
    "unreadable_records",
    "unsupported_schemas",
    "lifecycle_anomalies",
  ])("rejects a malformed %s count", (field) => {
    expect(() => parseCycleReview(without(field))).toThrow(CycleContractError);
    expect(() => parseCycleReview(withField(field, -1))).toThrow(
      CycleContractError,
    );
    expect(() => parseCycleReview(withField(field, 1.5))).toThrow(
      CycleContractError,
    );
  });

  it.each(["refusals", "attention", "changed", "newly_produced", "unchanged"])(
    "rejects a malformed %s list rather than emptying it",
    (field) => {
      expect(() => parseCycleReview(without(field))).toThrow(
        CycleContractError,
      );
      expect(() => parseCycleReview(withField(field, [1, 2]))).toThrow(
        CycleContractError,
      );
    },
  );

  it("rejects malformed stages", () => {
    expect(() => parseCycleReview(without("stages"))).toThrow(
      CycleContractError,
    );
    expect(() => parseCycleReview(withField("stages", [{ name: "x" }]))).toThrow(
      CycleContractError,
    );
  });

  it("rejects a course missing its identity or course fields", () => {
    const course = valid().courses as Record<string, unknown>[];

    for (const field of [
      "symbol",
      "disposition",
      "action_kind",
      "action_statement",
      "asks_for_something",
    ]) {
      const broken = { ...course[0] };
      delete broken[field];

      expect(() => parseCycleReview(withField("courses", [broken]))).toThrow(
        CycleContractError,
      );
    }
  });

  it("rejects a malformed courses container", () => {
    expect(() => parseCycleReview(without("courses"))).toThrow(
      CycleContractError,
    );
    expect(() => parseCycleReview(withField("courses", "none"))).toThrow(
      CycleContractError,
    );
  });

  it("rejects a malformed envelope shape", () => {
    const course = (valid().courses as Record<string, unknown>[])[0];

    expect(() =>
      parseCycleReview(
        withField("courses", [{ ...course, envelope: { kind: "upward_bounded" } }]),
      ),
    ).toThrow(CycleContractError);

    expect(() =>
      parseCycleReview(withField("courses", [{ ...course, envelope: 7 }])),
    ).toThrow(CycleContractError);
  });

  it("rejects malformed last_known, including an invalid date", () => {
    expect(() => parseCycleReview(withField("last_known", { cycle_id: "c0" }))).toThrow(
      CycleContractError,
    );

    expect(() =>
      parseCycleReview(
        withField("last_known", {
          cycle_id: "c0",
          finished_at: "yesterday-ish",
          status: "complete",
          courses: [],
        }),
      ),
    ).toThrow(CycleContractError);
  });

  it("rejects a non-object response", () => {
    for (const payload of [null, 7, "ok", []]) {
      expect(() => parseCycleReview(payload)).toThrow(CycleContractError);
    }
  });
});

describe("the recorded portfolio and candidates", () => {
  it("parses a whole portfolio, preserving absence", () => {
    const review = parseCycleReview({
      ...valid(),
      portfolio: {
        total_value: 100000,
        available_cash_usd: null,
        cash_pct: null,
        observed: "eToro account response received at 2026-08-20 12:00 UTC",
        compliant: null,
        holdings: [
          { symbol: "KO", market_value_usd: 50000, weight_pct: 50 },
          { symbol: "PG", market_value_usd: 25000, weight_pct: null },
        ],
        allocations: [
          {
            asset: "cash",
            current_pct: null,
            target_pct: 15,
            difference_pct: null,
          },
        ],
      },
    });

    expect(review.portfolio).not.toBeNull();
    expect(review.portfolio?.availableCashUsd).toBeNull();
    expect(review.portfolio?.holdings[1].weightPct).toBeNull();
    expect(review.portfolio?.allocations[0].differencePct).toBeNull();
    expect(review.portfolio?.compliant).toBeNull();
  });

  it("carries a refused allocation policy and states no target", () => {
    // The owner's amendment: `CapitalPolicyService` refused the plan,
    // so the record states no target at all. A target of 0 here would
    // be a plan this platform invented — the exact defect the backend
    // stopped producing, arriving through the parser instead.
    const review = parseCycleReview({
      ...valid(),
      portfolio: {
        total_value: 10000,
        available_cash_usd: 5407,
        cash_pct: 54.07,
        observed: "eToro account response received at 2026-08-24 12:00 UTC",
        compliant: null,
        holdings: [],
        allocation_policy_refused:
          "the owner strategy is contradictory: the four strategic targets " +
          "must total 100%, and they total 105%",
        allocations: [
          {
            asset: "cash",
            current_pct: 54.07,
            target_pct: null,
            difference_pct: null,
          },
        ],
      },
    });

    expect(review.portfolio?.allocationPolicyRefused).toContain("105%");
    expect(review.portfolio?.allocations[0].targetPct).toBeNull();

    // The account itself survives the refusal.
    expect(review.portfolio?.allocations[0].currentPct).toBe(54.07);
    expect(review.portfolio?.cashPct).toBe(54.07);
  });

  it("reads no policy refusal where the backend stated none", () => {
    const review = parseCycleReview({
      ...valid(),
      portfolio: {
        total_value: 10000,
        available_cash_usd: 5407,
        cash_pct: 54.07,
        observed: "",
        compliant: true,
        holdings: [],
        allocations: [
          {
            asset: "cash",
            current_pct: 54.07,
            target_pct: 25,
            difference_pct: 29.07,
          },
        ],
      },
    });

    expect(review.portfolio?.allocationPolicyRefused).toBe("");
    expect(review.portfolio?.allocations[0].targetPct).toBe(25);
  });

  it("rejects a malformed portfolio rather than dropping the account", () => {
    expect(() =>
      parseCycleReview(withField("portfolio", { total_value: 1 })),
    ).toThrow(CycleContractError);

    expect(() => parseCycleReview(withField("portfolio", 7))).toThrow(
      CycleContractError,
    );
  });

  it("rejects a missing or malformed candidates list", () => {
    expect(() => parseCycleReview(without("candidates"))).toThrow(
      CycleContractError,
    );
    expect(() => parseCycleReview(withField("candidates", "none"))).toThrow(
      CycleContractError,
    );
  });

  it("keeps the server's ranking rather than reordering it", () => {
    const course = (valid().courses as Record<string, unknown>[])[0];

    const review = parseCycleReview(
      withField("candidates", [
        { ...course, symbol: "BBB", conviction: 88 },
        { ...course, symbol: "AAA", conviction: 41 },
      ]),
    );

    expect(review.candidates.map((c) => c.symbol)).toEqual(["BBB", "AAA"]);
  });
});
