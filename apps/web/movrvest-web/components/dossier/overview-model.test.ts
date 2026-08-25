import { describe, expect, it } from "vitest";

import type { CycleCourse, CycleReview } from "@/lib/api/cycle-review";
import type { DossierViewModel } from "@/lib/api/dossier";

import {
  capitalModel,
  courseModel,
  heroModel,
  historyLine,
  snapshotModel,
  statedInstant,
  summaryWidgets,
  viewFromParam,
  whatChangesTheView,
  whatCouldGoWrong,
  whyItQualifies,
} from "./overview-model";

/**
 * The redesign's rules, tested at the selector layer.
 *
 * Fixtures follow the live acceptance specimens — DIS (held,
 * capital-asking, filing evidence), MSFT (valuation blocker, no
 * envelope), AMD (blocker with strong counterweights), UUUU (sparse) and
 * BNP.PA (non-US, EUR) — trimmed to the fields the selectors read.
 */

function dossier(overrides: Record<string, unknown> = {}): DossierViewModel {
  const base = {
    symbol: "DIS",
    decisionState: "RECOMMEND",
    rationale:
      "The investment case satisfies quality, evidence, valuation, risk, and portfolio gates.",
    action: {
      kind: "add",
      statement: "Consider adding to DIS.",
      because:
        "The investment case satisfies quality, evidence, valuation, risk, and portfolio gates.",
      checkpoint: "Reports earnings in 79 days (Nov 12).",
    },
    conviction: 75,
    convictionLabel: "High Conviction",
    committeeAgreement: 1,
    classification: {
      industry: {
        label: "Entertainment",
        sector: "Communication Services",
        stated: "The data provider files this company under 'Entertainment'.",
        read: { source: "Yahoo Finance", age: "Yahoo Finance, 22 hours ago" },
      },
    },
    decisionCourse: {
      reviews: 21,
      changes: 9,
      stated: "The decision changed 9 times between 2026-08-02 and 2026-08-25.",
      transitions: [],
      absentBecause: null,
    },
    synthesis: {
      because: [
        { statement: "Large-cap company.", origin: "assessed", committee: null },
        { statement: "Positive earnings.", origin: "assessed", committee: null },
        {
          statement: "Dividend-paying business.",
          origin: "assessed",
          committee: null,
        },
      ],
      despite: [
        {
          statement: "The provider-reported growth signal is declining.",
          origin: "assessed",
          committee: null,
        },
      ],
      reviewIf: [],
    },
    strengths: [
      "Large-cap company.",
      "Positive earnings.",
      "Dividend-paying business.",
      "Cash flow is excellent.",
    ],
    risks: ["The provider-reported growth signal is declining."],
    invalidationConditions: [
      "The provider-reported growth signal is declining.",
    ],
    catalysts: ["Reports earnings in 79 days (Nov 12)."],
    // Account and market context — must reach none of the widgets.
    contextStrengths: ["The account holds ample cash."],
    contextRisks: ["The portfolio is concentrated in technology."],
    fundamentals: {
      explained: "Filing-established figures come from the filing itself.",
      rows: [
        {
          label: "Revenue growth — FY filing",
          stated: "+3.4%",
          value: 0.0335,
          standing: "filing_evidence",
          asOf: "computed by this platform from the income statement",
          currency: null,
          period: null,
          unit: "fraction",
          metric: "revenue_growth",
          source: "10-K 0001744489-25-000155, via SEC EDGAR",
          because: null,
        },
        {
          label: "Earnings growth — FY filing",
          stated: "+132.7%",
          value: 1.3265,
          standing: "filing_evidence",
          asOf: "computed by this platform from the income statement",
          currency: null,
          period: null,
          unit: "fraction",
          metric: "earnings_growth",
          source: "10-K 0001744489-25-000155, via SEC EDGAR",
          because: null,
        },
        {
          label: "Operating cash flow",
          stated: "$17.0B",
          value: 16988999680,
          standing: "provider_fallback",
          asOf: "received 2026-08-24",
          currency: "USD",
          period: null,
          unit: "currency",
          metric: "operating_cash_flow",
          source: "Yahoo Finance",
          because: null,
        },
        {
          label: "Forward P/E",
          stated: null,
          value: null,
          standing: "refused",
          asOf: null,
          currency: null,
          period: null,
          unit: null,
          metric: "forward_pe",
          source: null,
          because: "No valuation benchmark is held.",
        },
      ],
    },
    ...overrides,
  };

  return base as unknown as DossierViewModel;
}

function envelope(): CycleCourse {
  return {
    symbol: "DIS",
    disposition: "RECOMMEND",
    actionKind: "add",
    actionStatement: "Consider adding to DIS.",
    envelope: {
      kind: "upward_bounded",
      stated:
        "MOVRvest's course is ADD. The current policy permits consideration up to a 2% portfolio weight, subject to the binding portfolio-capacity constraint.",
      finalPct: 2.0,
      liquidity: "Liquidity is unmeasured for equities on this platform.",
    },
    blocker: { kind: "none", stated: "Nothing blocks progress.", despite: [] },
  } as unknown as CycleCourse;
}

function review(): CycleReview {
  return {
    execution: "complete",
    streamComplete: true,
    finishedAt: "2026-08-24 17:35 UTC",
    portfolio: {
      holdings: [
        { symbol: "DIS", marketValueUsd: 336.34, weightPct: 0.3145 },
        { symbol: "META", marketValueUsd: 900, weightPct: 0.84 },
      ],
    },
  } as unknown as CycleReview;
}

// ── views ───────────────────────────────────────────────────────────

describe("the view parameter", () => {
  it("selects a known view and defaults everything else to overview", () => {
    expect(viewFromParam("financials")).toBe("financials");
    expect(viewFromParam("thesis")).toBe("thesis");
    expect(viewFromParam("evidence")).toBe("evidence");
    expect(viewFromParam(undefined)).toBe("overview");
    expect(viewFromParam("nonsense")).toBe("overview");
    expect(viewFromParam(["developments", "evidence"])).toBe("developments");
  });
});

// ── the course ──────────────────────────────────────────────────────

describe("the course", () => {
  it("travels from the action carrier, verbatim", () => {
    const course = courseModel(dossier());

    expect(course?.statement).toBe("Consider adding to DIS.");
    expect(course?.disposition).toBe("RECOMMEND");
    expect(course?.checkpoint).toBe("Reports earnings in 79 days (Nov 12).");
  });

  it("words the wait case from the carrier and not from the state", () => {
    const course = courseModel(
      dossier({
        decisionState: "PREPARE",
        action: {
          kind: "wait",
          statement:
            "Wait before opening MSFT. The case is credible but not yet actionable.",
          because:
            "The company is attractive, but valuation does not currently support action.",
          checkpoint: null,
        },
      }),
    );

    expect(course?.statement).toBe(
      "Wait before opening MSFT. The case is credible but not yet actionable.",
    );
    expect(course?.disposition).toBe("PREPARE");
  });

  it("refuses to manufacture a course where no action is carried", () => {
    // The whole point: a disposition is not an action. With no action
    // carrier there is no course, and nothing here turns RECOMMEND into
    // "buy" or PREPARE into "wait".
    expect(courseModel(dossier({ action: null }))).toBeNull();
    expect(
      courseModel(dossier({ action: { kind: "add", statement: "" } })),
    ).toBeNull();
  });

  it("explains with the decision's own sentence, never a score comparison", () => {
    const course = courseModel(
      dossier({
        decisionState: "PREPARE",
        action: {
          kind: "wait",
          statement: "Wait before opening MSFT.",
          because:
            "The company is attractive, but valuation does not currently support action.",
          checkpoint: null,
        },
      }),
    );

    expect(course?.because).toContain("valuation does not currently support");
    expect(course?.because).not.toMatch(/\b55\b|\b60\b/);
  });
});

// ── capital consideration ───────────────────────────────────────────

describe("the capital consideration", () => {
  it("carries the recorded course and its review time", () => {
    const capital = capitalModel({
      course: envelope(),
      finishedAt: "2026-08-24 17:35 UTC",
    });

    expect(capital?.finishedAt).toBe("2026-08-24 17:35 UTC");
    expect(capital?.course.envelope?.stated).toContain("up to a 2% portfolio");
  });

  it("renders nothing for a non-capital course rather than a shell", () => {
    const withoutEnvelope = {
      ...envelope(),
      envelope: null,
    } as unknown as CycleCourse;

    expect(
      capitalModel({ course: withoutEnvelope, finishedAt: "whenever" }),
    ).toBeNull();
  });

  it("renders nothing where no completed cycle covered the security", () => {
    // No stale fallback: an older envelope is older policy and older
    // account guidance, and placing it beside a newer decision would
    // present stale sizing as current.
    expect(capitalModel(null)).toBeNull();
  });

  it("never reads the envelope's number", () => {
    const capital = capitalModel({
      course: envelope(),
      finishedAt: "2026-08-24 17:35 UTC",
    });

    // The selector hands the whole course to the domain's own renderer.
    // It does not decide what 2.0 means, and no field it produces is
    // derived from it.
    expect(JSON.stringify(capital)).not.toContain('"derivedPct"');
    expect(capital?.course.envelope?.stated).toBeTruthy();
  });
});

// ── the three widgets ───────────────────────────────────────────────

describe("the three summary widgets", () => {
  it("leads with what the decision owns, then tops up from the analyst", () => {
    const items = whyItQualifies(dossier());

    expect(items).toHaveLength(3);
    expect(items.every((item) => item.origin === "decision")).toBe(true);
    expect(items[0].stated).toBe("Large-cap company.");
  });

  it("never prints the same statement twice under two origins", () => {
    // `synthesis.because` is drawn from `strengths`, so a naive
    // concatenation would repeat every item and label the second copy a
    // different kind of evidence.
    const items = whyItQualifies(dossier());
    const stated = items.map((item) => item.stated);

    expect(new Set(stated).size).toBe(stated.length);
  });

  it("tops up from analyst prose only when the decision runs out", () => {
    const items = whyItQualifies(
      dossier({
        synthesis: { because: [], despite: [], reviewIf: [] },
      }),
    );

    expect(items).toHaveLength(3);
    expect(items.every((item) => item.origin === "assessed")).toBe(true);
  });

  it("keeps account and market context out of every company widget", () => {
    const blob = JSON.stringify([
      whyItQualifies(dossier()),
      whatCouldGoWrong(dossier()),
      whatChangesTheView(dossier()),
    ]);

    // An account-wide condition is not a reason to revisit a company.
    expect(blob).not.toContain("The account holds ample cash.");
    expect(blob).not.toContain("The portfolio is concentrated in technology.");
  });

  it("never renders one list under two headings", () => {
    // AMD forced this. Its `invalidationConditions` are the same three
    // sentences as its `risks`, so widgets computed independently
    // printed one list twice — under "What could go wrong" and again
    // under "What changes the view". Two headings over identical
    // content implies two findings where there is one.
    const amd = dossier({
      synthesis: { because: [], despite: [], reviewIf: [] },
      strengths: [],
      risks: [
        "AMD declined -3.28% in its most recent reading.",
        "Short-term price momentum is strongly negative.",
        "Annualised volatility is 71.8% over the past year.",
      ],
      invalidationConditions: [
        "AMD declined -3.28% in its most recent reading.",
        "Short-term price momentum is strongly negative.",
        "Annualised volatility is 71.8% over the past year.",
      ],
    });

    const widgets = summaryWidgets(amd);

    expect(widgets.wrong.map((i) => i.stated)).toEqual([
      "AMD declined -3.28% in its most recent reading.",
      "Short-term price momentum is strongly negative.",
      "Annualised volatility is 71.8% over the past year.",
    ]);

    // Nothing additional is held about what would change the view, so
    // the widget is empty and will be omitted. That is the honest
    // answer; a repeated list would not be saying anything either.
    expect(widgets.changes).toEqual([]);

    const all = [...widgets.qualifies, ...widgets.wrong, ...widgets.changes].map(
      (i) => i.stated,
    );

    expect(new Set(all).size).toBe(all.length);
  });

  it("still shows a genuinely distinct review condition", () => {
    const widgets = summaryWidgets(
      dossier({
        risks: ["Growth is slowing."],
        invalidationConditions: ["The dividend is cut."],
        synthesis: { because: [], despite: [], reviewIf: [] },
        strengths: [],
      }),
    );

    expect(widgets.wrong.map((i) => i.stated)).toEqual(["Growth is slowing."]);
    expect(widgets.changes.map((i) => i.stated)).toEqual([
      "The dividend is cut.",
    ]);
  });

  it("caps each widget at three", () => {
    const many = Array.from({ length: 9 }, (_, i) => `Risk ${i}.`);
    const items = whatCouldGoWrong(dossier({ risks: many }));

    expect(items).toHaveLength(3);
  });

  it("omits a widget rather than filling it with absence", () => {
    const sparse = dossier({
      synthesis: { because: [], despite: [], reviewIf: [] },
      strengths: [],
      risks: [],
      invalidationConditions: [],
    });

    expect(whyItQualifies(sparse)).toEqual([]);
    expect(whatCouldGoWrong(sparse)).toEqual([]);
    expect(whatChangesTheView(sparse)).toEqual([]);
  });

  it("keeps a blocker's counterweights distinct from its risks", () => {
    // AMD's shape: the case is blocked on quality while several strong
    // facts stand for it. The two must not merge — the counterweights
    // are why the case qualifies, the risks are what could go wrong.
    const amd = dossier({
      decisionState: "PREPARE",
      action: {
        kind: "wait",
        statement: "Wait before opening AMD.",
        because:
          "The investment case is credible, but quality conviction is not yet sufficient.",
        checkpoint: null,
      },
      synthesis: {
        because: [
          { statement: "Large-cap company.", origin: "assessed", committee: null },
          {
            statement: "The provider-reported growth signal is strong.",
            origin: "assessed",
            committee: null,
          },
        ],
        despite: [
          {
            statement: "AMD declined -3.28% in its most recent reading.",
            origin: "assessed",
            committee: null,
          },
        ],
        reviewIf: [],
      },
      strengths: ["Large-cap company."],
      risks: ["AMD declined -3.28% in its most recent reading."],
    });

    const qualifies = whyItQualifies(amd).map((item) => item.stated);
    const wrong = whatCouldGoWrong(amd).map((item) => item.stated);

    expect(qualifies).toContain("The provider-reported growth signal is strong.");
    expect(wrong).toContain("AMD declined -3.28% in its most recent reading.");
    expect(qualifies.some((item) => wrong.includes(item))).toBe(false);
  });
});

// ── history ─────────────────────────────────────────────────────────

describe("the one history line", () => {
  it("states the backend's own sentence where the decision moved", () => {
    expect(historyLine(dossier())).toBe(
      "The decision changed 9 times between 2026-08-02 and 2026-08-25.",
    );
  });

  it("counts reviews rather than implying a duration where nothing moved", () => {
    expect(
      historyLine(
        dossier({
          decisionCourse: {
            reviews: 4,
            changes: 0,
            stated: "",
            transitions: [],
            absentBecause: null,
          },
        }),
      ),
    ).toBe("Unchanged across 4 recorded reviews.");
  });

  it("says nothing where no history is recorded", () => {
    expect(historyLine(dossier({ decisionCourse: null }))).toBeNull();
  });
});

// ── the financial snapshot ──────────────────────────────────────────

describe("the financial snapshot", () => {
  it("keeps filing evidence and a provider fallback apart", () => {
    const snapshot = snapshotModel(dossier());
    const byLabel = new Map(snapshot.facts.map((f) => [f.label, f]));

    expect(byLabel.get("Earnings growth — FY filing")?.authority).toBe(
      "Filing evidence",
    );
    expect(byLabel.get("Operating cash flow")?.authority).toBe(
      "Provider reported",
    );
  });

  it("never turns a provider fallback into filing evidence", () => {
    const snapshot = snapshotModel(dossier());

    for (const fact of snapshot.facts) {
      if (fact.authorityKey === "provider_fallback") {
        expect(fact.authority).not.toContain("Filing");
      }
    }
  });

  it("keeps the two growth metrics separately named and never compared", () => {
    // Disney's filing earnings growth is +132.7% and the provider's
    // reading is -48.3%: different periods, different formulas, and the
    // backend names them apart. No arithmetic between them is offered.
    const mixed = snapshotModel(
      dossier({
        fundamentals: {
          explained: "",
          rows: [
            {
              label: "Earnings growth — FY filing",
              stated: '"Net income" 13,431 under "2025" against 5,773 under "2024"',
              value: 1.3265,
              unit: "fraction",
              standing: "filing_evidence",
              asOf: null,
              currency: null,
              period: null,
            },
            {
              label: "Provider-reported earnings growth — period not stated",
              stated: "",
              value: -0.483,
              unit: "fraction",
              standing: "provider_fallback",
              asOf: "received 2026-08-24",
              currency: null,
              period: null,
            },
          ],
        },
      }),
    );

    expect(mixed.facts.map((f) => f.label)).toEqual([
      "Earnings growth — FY filing",
      "Provider-reported earnings growth — period not stated",
    ]);
    expect(mixed.facts[0].authority).toBe("Filing evidence");
    expect(mixed.facts[1].authority).toBe("Provider reported");
    expect(mixed.facts[0].stated).toBe("132.7%");
    expect(mixed.facts[1].stated).toBe("-48.3%");
    expect(JSON.stringify(mixed)).not.toContain("difference");

    // And the arithmetic sentence stays out of the figure slot: it is
    // evidence, it belongs in Financials, and rendering it as a value
    // put a sentence where the reader expected a number.
    expect(mixed.facts[0].stated).not.toContain("Net income");
  });

  it("carries currency and never infers one", () => {
    const snapshot = snapshotModel(dossier());
    const byLabel = new Map(snapshot.facts.map((f) => [f.label, f]));

    expect(byLabel.get("Operating cash flow")?.currency).toBe("USD");
    expect(byLabel.get("Earnings growth — FY filing")?.currency).toBeNull();
  });

  it("keeps a zero, which is a value", () => {
    const snapshot = snapshotModel(
      dossier({
        fundamentals: {
          explained: "",
          rows: [
            {
              label: "Dividend yield",
              stated: "",
              value: 0,
              unit: "fraction",
              standing: "provider_fallback",
              asOf: null,
              currency: null,
              period: null,
            },
          ],
        },
      }),
    );

    expect(snapshot.facts).toHaveLength(1);
    expect(snapshot.facts[0].stated).toBe("0.0%");
    expect(snapshot.coverage).toBeNull();
  });

  it("counts what is not held once instead of printing absent cards", () => {
    const snapshot = snapshotModel(dossier());

    expect(snapshot.facts).toHaveLength(3);
    expect(snapshot.coverage).toBe(
      "1 of 4 figures are not held. Each one, and why, is in Financials.",
    );
  });

  it("stays compact for a sparse security", () => {
    const snapshot = snapshotModel(
      dossier({
        fundamentals: {
          explained: "",
          rows: Array.from({ length: 12 }, (_, i) => ({
            label: `Metric ${i}`,
            stated: null,
            value: null,
            standing: "unavailable",
            asOf: null,
            currency: null,
            period: null,
          })),
        },
      }),
    );

    // No wall of absent metrics: twelve absences become one sentence.
    expect(snapshot.facts).toEqual([]);
    expect(snapshot.coverage).toContain("12 of 12");
  });
});

// ── the hero ────────────────────────────────────────────────────────

describe("the hero", () => {
  it("carries the ticker, the industry line and the review time", () => {
    const hero = heroModel(
      dossier(),
      review(),
      "2026-08-24T17:35:54.333901Z",
    );

    expect(hero.symbol).toBe("DIS");
    expect(hero.industry?.label).toBe("Entertainment");
    expect(hero.industry?.sector).toBe("Communication Services");
    expect(hero.industry?.age).toBe("Yahoo Finance, 22 hours ago");

    // The store's ISO timestamp, read by a person rather than printed raw.
    expect(hero.reviewedAt).toBe("24 Aug 2026, 17:35 UTC");
  });

  it("reads ownership from the same completed cycle, never an account call", () => {
    const hero = heroModel(dossier(), review(), "2026-08-24 17:35 UTC");

    expect(hero.holding?.weightPct).toBeCloseTo(0.3145);
  });

  it("shows no holding for a security that cycle did not hold", () => {
    // Absent, not zero.
    const hero = heroModel(
      dossier({ symbol: "MSFT" }),
      review(),
      "2026-08-24 17:35 UTC",
    );

    expect(hero.holding).toBeNull();
  });

  it("invents no price, name or return", () => {
    // Stage 0: `CompanyFacts` (which carries name, current_price and
    // daily_change_pct) is imported nowhere in `app/brain/`, the dossier
    // route holds a `CompanyRecommendation` instead, and
    // `InvestmentCase.company_name` is assigned nowhere. So the hero
    // shows the ticker alone — and carries no field a later reader could
    // mistake for a held price.
    const hero = heroModel(dossier(), review(), null);
    const keys = Object.keys(hero);

    expect(keys).not.toContain("price");
    expect(keys).not.toContain("name");
    expect(keys).not.toContain("companyName");
    expect(keys).not.toContain("return");
    expect(hero.symbol).toBe("DIS");
  });

  it("omits the industry line rather than inventing one", () => {
    const hero = heroModel(dossier({ classification: null }), null, null);

    expect(hero.industry).toBeNull();
    expect(hero.holding).toBeNull();
    expect(hero.reviewedAt).toBeNull();
  });
});

// ── the review instant ──────────────────────────────────────────────

describe("the review instant", () => {
  it("formats the recorded timestamp for a reader, in the zone it was recorded in", () => {
    // The store carries an ISO timestamp and the backend words no
    // sentence for it, so the page printed "completed
    // 2026-08-24T17:35:54.333901Z" verbatim. Formatting, not
    // computation: the same instant, to the minute.
    expect(statedInstant("2026-08-24T17:35:54.333901Z")).toBe(
      "24 Aug 2026, 17:35 UTC",
    );
  });

  it("uses no locale, so a server and a browser cannot disagree", () => {
    const stated = statedInstant("2026-01-05T04:07:00Z");

    expect(stated).toBe("5 Jan 2026, 04:07 UTC");
  });

  it("returns an unparseable value untouched rather than guessing", () => {
    expect(statedInstant("whenever")).toBe("whenever");
    expect(statedInstant(null)).toBeNull();
  });

  it("offers no relative phrasing, which would age between render and reading", () => {
    const stated = statedInstant("2026-08-24T17:35:54.333901Z") ?? "";

    for (const relative of ["ago", "just now", "today", "yesterday"]) {
      expect(stated.toLowerCase()).not.toContain(relative);
    }
  });
});
