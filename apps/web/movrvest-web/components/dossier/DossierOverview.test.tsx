import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { CycleCourse, CycleReview } from "@/lib/api/cycle-review";
import type { DossierViewModel } from "@/lib/api/dossier";

import {
  DossierCourseBlock,
  DossierHero,
  DossierOverviewView,
  DossierSummaryRow,
} from "./DossierOverview";
import { courseModel, heroModel, historyLine } from "./overview-model";

/**
 * What the default Overview actually renders.
 *
 * The selector tests pin what is *chosen*; these pin what reaches the
 * markup — the rules that are properties of the composition rather than
 * of the model: what the hero refuses to show, what the Overview
 * refuses to invoke, and the order the sections fall into when the
 * columns collapse.
 */

function dossier(overrides: Record<string, unknown> = {}): DossierViewModel {
  return {
    symbol: "DIS",
    decisionState: "RECOMMEND",
    rationale: "The investment case satisfies every gate.",
    action: {
      kind: "add",
      statement: "Consider adding to DIS.",
      because: "The investment case satisfies every gate.",
      checkpoint: "Reports earnings in 79 days (Nov 12).",
    },
    conviction: 75,
    convictionLabel: "High Conviction",
    committeeAgreement: 1,
    evidenceAsOf: {
      source: "Yahoo Finance",
      age: "Yahoo Finance, 22 hours ago",
    },
    scores: {
      quality: { value: 71 },
      valuation: { value: 55 },
      evidence: { value: 80 },
      safety: { value: 35 },
      portfolioFit: { value: 60 },
    },
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
    strengths: ["Large-cap company."],
    risks: ["The provider-reported growth signal is declining."],
    invalidationConditions: ["Growth reverses."],
    catalysts: [],
    contextStrengths: ["The account holds ample cash."],
    contextRisks: ["The portfolio is concentrated in technology."],
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
      ],
    },
    ...overrides,
  } as unknown as DossierViewModel;
}

function recorded() {
  return {
    course: {
      symbol: "DIS",
      disposition: "RECOMMEND",
      actionKind: "add",
      actionStatement: "Consider adding to DIS.",
      envelope: {
        kind: "upward_bounded",
        stated:
          "MOVRvest's course is ADD. The current policy permits consideration up to a 2% portfolio weight.",
        finalPct: 2.0,
        capacityCeilingPct: 19.6855,
        bindingConstraint: "the evidence ceiling",
        because: "",
        namedGaps: [],
        liquidity: "Liquidity is unmeasured for equities on this platform.",
        priceAsOf: "Yahoo Finance, just now",
        portfolioAsOf: "eToro account response received at 2026-08-24 17:35 UTC",
        securityRiskBecause: "MODERATE volatility adds no security-risk ceiling.",
        securityRiskCeilingPct: null,
        securityRiskCapped: false,
        starterCapped: false,
        qualityAuthority: "grounded",
        evidenceCeiling: "max_add_change",
        policySource: "investor_strategy.json",
        policyVersion: "1f0e1bc15292",
      },
      blocker: { kind: "none", stated: "Nothing blocks progress.", despite: [] },
    } as unknown as CycleCourse,
    finishedAt: "2026-08-24 17:35 UTC",
  };
}

function review(): CycleReview {
  return {
    execution: "complete",
    streamComplete: true,
    finishedAt: "2026-08-24 17:35 UTC",
    portfolio: {
      holdings: [{ symbol: "DIS", marketValueUsd: 336.34, weightPct: 0.3145 }],
    },
  } as unknown as CycleReview;
}

const NEWS = <div data-testid="news">Ticker News</div>;

// ── the hero ────────────────────────────────────────────────────────

describe("the hero", () => {
  it("leads with the ticker, where it operates, and the review time", () => {
    const markup = renderToStaticMarkup(
      <DossierHero hero={heroModel(dossier(), review(), "2026-08-24 17:35 UTC")} />,
    );

    expect(markup).toContain("DIS");
    expect(markup).toContain("Entertainment");
    expect(markup).toContain("Communication Services");
    expect(markup).toContain("Last CIO review");
    expect(markup).toContain("0.31% of the account");
  });

  it("shows no conviction, agreement, score or provider evidence line", () => {
    const markup = renderToStaticMarkup(
      <DossierHero hero={heroModel(dossier(), review(), "2026-08-24 17:35 UTC")} />,
    );

    // The hero used to read "CONVICTION 75/100 · COMMITTEE AGREEMENT
    // 100% · EVIDENCE READ Yahoo Finance". A score is how this platform
    // reached a view; it is not the view. And naming one provider quote
    // beside filing-established figures let the weaker claim borrow the
    // stronger's authority.
    expect(markup).not.toContain("Conviction");
    expect(markup).not.toContain("75");
    expect(markup).not.toContain("Committee agreement");
    expect(markup).not.toContain("Evidence read");
    expect(markup).not.toContain("100%");
  });

  it("shows the ticker alone where no industry line is carried", () => {
    const markup = renderToStaticMarkup(
      <DossierHero hero={heroModel(dossier({ classification: null }), null, null)} />,
    );

    expect(markup).toContain("DIS");
    expect(markup).not.toContain("Last CIO review");
    expect(markup).not.toContain("of the account");
  });
});

// ── the course ──────────────────────────────────────────────────────

describe("the course block", () => {
  it("makes the course primary and the disposition secondary", () => {
    const markup = renderToStaticMarkup(
      <DossierCourseBlock
        course={courseModel(dossier())}
        disposition="RECOMMEND"
        history={historyLine(dossier())}
      />,
    );

    const coursePos = markup.indexOf("Consider adding to DIS.");
    const dispositionPos = markup.indexOf("RECOMMEND");

    expect(coursePos).toBeGreaterThan(-1);
    expect(dispositionPos).toBeGreaterThan(coursePos);
    expect(markup).toContain("Reports earnings in 79 days");
  });

  it("states the absence rather than wording an action from the state", () => {
    const markup = renderToStaticMarkup(
      <DossierCourseBlock
        course={null}
        disposition="RECOMMEND"
        history={null}
      />,
    );

    expect(markup).toContain("RECOMMEND");
    expect(markup).toContain("A disposition is not");
    for (const word of ["buy", "sell", "add to", "reduce", "open a"]) {
      expect(markup.toLowerCase()).not.toContain(word);
    }
  });
});

// ── the Overview composition ────────────────────────────────────────

describe("the Overview", () => {
  it("never renders the executive narrative", () => {
    // `ExecutiveNarrative` is a client component that fetches on mount,
    // so leaving it out of this view *is* the mechanism: the Overview
    // issues no narrative request and the case never waits on a model.
    const markup = renderToStaticMarkup(
      <DossierOverviewView
        dossier={dossier()}
        recorded={recorded()}
        news={NEWS}
      />,
    );

    expect(markup).not.toContain("Executive narrative");
    expect(markup).not.toContain("AI-written");
    expect(markup).not.toContain("narrative-heading");
  });

  it("shows no score, conviction or committee mechanics", () => {
    const markup = renderToStaticMarkup(
      <DossierOverviewView
        dossier={dossier()}
        recorded={recorded()}
        news={NEWS}
      />,
    );

    for (const platformMechanic of [
      "Conviction",
      "Committee agreement",
      "Quality score",
      "Evidence read",
    ]) {
      expect(markup).not.toContain(platformMechanic);
    }
  });

  it("puts the course first in the DOM, before the capital consideration", () => {
    // Meaningful order when the two-column row collapses to one column:
    // the course is what the investor came for and stays on top.
    const markup = renderToStaticMarkup(
      <DossierOverviewView
        dossier={dossier()}
        recorded={recorded()}
        news={NEWS}
      />,
    );

    const order = [
      "dossier-course",
      "dossier-capital",
      "dossier-qualifies",
      "dossier-snapshot",
    ].map((id) => markup.indexOf(id));

    expect(order.every((position) => position > -1)).toBe(true);
    expect(order).toEqual([...order].sort((a, b) => a - b));
  });

  it("places the capital consideration beside the course, with its own sentence", () => {
    const markup = renderToStaticMarkup(
      <DossierOverviewView
        dossier={dossier()}
        recorded={recorded()}
        news={NEWS}
      />,
    );

    expect(markup).toContain("What the latest review allowed");
    expect(markup).toContain("up to a 2% portfolio weight");
    expect(markup).toContain("Liquidity is unmeasured for equities");
    expect(markup).toContain("not an order");
  });

  it("renders no envelope shell for a non-capital course", () => {
    const markup = renderToStaticMarkup(
      <DossierOverviewView dossier={dossier()} recorded={null} news={NEWS} />,
    );

    expect(markup).not.toContain("What the latest review allowed");
    expect(markup).not.toContain("dossier-capital");
  });

  it("renders the deterministic case around whatever news is passed in", () => {
    // News arrives as a node the page wraps in Suspense, so the
    // deterministic Overview is complete before the paced request is.
    const markup = renderToStaticMarkup(
      <DossierOverviewView
        dossier={dossier()}
        recorded={recorded()}
        news={<div>pending</div>}
      />,
    );

    expect(markup).toContain("Consider adding to DIS.");
    expect(markup).toContain("132.7%");
    expect(markup).toContain("Filing evidence");

    // The arithmetic is evidence and lives in Financials; a compact row
    // shows the figure. Rendering the sentence here overflowed the
    // viewport by 180px on a 1280px screen.
    expect(markup).not.toContain("under &quot;2025&quot;");
  });

  it("stays compact and honest for a sparse security", () => {
    const markup = renderToStaticMarkup(
      <DossierOverviewView
        dossier={dossier({
          synthesis: { because: [], despite: [], reviewIf: [] },
          strengths: [],
          risks: [],
          invalidationConditions: [],
          fundamentals: { explained: "", rows: [] },
          decisionCourse: null,
        })}
        recorded={null}
        news={NEWS}
      />,
    );

    // Sparse information must not look like poor business quality.
    expect(markup).toContain("Consider adding to DIS.");
    expect(markup).not.toContain("dossier-qualifies");
    expect(markup).not.toContain("dossier-snapshot");
    expect(markup).not.toContain("not established");
  });
});

// ── widgets, rendered ───────────────────────────────────────────────

describe("the summary widgets, rendered", () => {
  it("omits an empty widget rather than rendering an empty card", () => {
    const markup = renderToStaticMarkup(
      <DossierSummaryRow
        dossier={dossier({
          synthesis: { because: [], despite: [], reviewIf: [] },
          strengths: [],
          risks: [],
        })}
      />,
    );

    expect(markup).not.toContain("Why the case qualifies");
    expect(markup).not.toContain("What could go wrong");
    expect(markup).toContain("What changes the view");
  });

  it("prints a currency once, inside the figure", () => {
    // Rendered twice it read "USD 16.99bnUSD": the shared formatter
    // already prefixes the currency for a currency-unit row.
    const markup = renderToStaticMarkup(
      <DossierOverviewView
        dossier={dossier({
          fundamentals: {
            explained: "",
            rows: [
              {
                label: "Operating cash flow",
                stated: "",
                value: 16988999680,
                unit: "currency",
                currency: "USD",
                standing: "provider_fallback",
                asOf: null,
                period: null,
              },
            ],
          },
        })}
        recorded={null}
        news={NEWS}
      />,
    );

    expect(markup).toContain("USD 16.99bn");
    expect(markup).not.toContain("USD 16.99bnUSD");
    expect(markup.match(/USD/g)?.length).toBe(1);
  });

  it("keeps account and market context off the company widgets", () => {
    const markup = renderToStaticMarkup(<DossierSummaryRow dossier={dossier()} />);

    expect(markup).not.toContain("The account holds ample cash.");
    expect(markup).not.toContain("The portfolio is concentrated in technology.");
  });
});
