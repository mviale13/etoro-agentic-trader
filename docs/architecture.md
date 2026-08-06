# MOVRvest Architecture

> "An Artificial Chief Investment Officer (ACIO)"

**The current architecture is Cognitive Architecture v5.0**, at the end of
this document. Read that section for how the platform works today.

Everything between here and there is **v4.0, retained for history**. It
describes a Facts → Scorecards → Committees → Executive Board pipeline that
was never built in that shape: the platform reasons through analysts and an
Artificial CIO instead. Where v4.0 and v5.0 disagree, v5.0 is correct.

For which packages implement v5.0, see
[`architecture/REPOSITORY_INVENTORY.md`](architecture/REPOSITORY_INVENTORY.md).

---

<!-- ─────────────────────────────────────────────────────────────────────
     HISTORICAL — v4.0. Superseded by Cognitive Architecture v5.0 below.
     ───────────────────────────────────────────────────────────────── -->

# Architecture v4.0 (historical)

---

# Vision

MOVRvest is not a trading bot.

MOVRvest is an Artificial Chief Investment Officer whose mission is to help investors make better long-term investment decisions through transparent, explainable, evidence-based and continuously improving intelligence.

The investor always remains in control.

MOVRvest recommends.

The investor decides.

---

# Architectural North Star

MOVRvest transforms verified facts into transparent investment decisions through independent expert committees.

Every recommendation must be:

- Evidence-based
- Explainable
- Personalized
- Consistent
- Auditable

---

# Core Principles

Facts before opinions.

Committees reason.

Executive Board decides.

Executive Brief explains.

Learning improves future decisions.

Every component has exactly one responsibility.

---

# High-Level Architecture

```
                        External World

 eToro     Yahoo     FRED     ECB     News     Future Sources

                           │
                           ▼

                    Connectors / Providers

                           │
                           ▼

────────────────────────────────────────────────────────────
                     FACTS LAYER
────────────────────────────────────────────────────────────

PortfolioFacts

MarketFacts

InvestorFacts

OpportunityFacts

RiskFacts

                           │
                           ▼

────────────────────────────────────────────────────────────
                  DISCOVERY LAYER
────────────────────────────────────────────────────────────

Market Scanner

↓

Market Opportunities

↓

Opportunity Facts

↓

Opportunity Scorecards

                           │
                           ▼

────────────────────────────────────────────────────────────
                  COMMITTEE LAYER
────────────────────────────────────────────────────────────

Portfolio Committee

Market Committee

Opportunity Committee

Risk Committee

Policy Committee

Behaviour Committee

                           │

                   Committee Votes

                           │
                           ▼

────────────────────────────────────────────────────────────
                 EXECUTIVE BOARD
────────────────────────────────────────────────────────────

Executive Decision

↓

Executive Summary

↓

Executive Brief

                           │
                           ▼

────────────────────────────────────────────────────────────
                PRESENTATION LAYER
────────────────────────────────────────────────────────────

Dashboard

API

Mobile

Chat

Email

Notifications
```

---

# Layer Responsibilities

## 1. Connectors

Purpose

Retrieve data from external systems.

Examples

- eToro
- Yahoo Finance
- FRED
- ECB
- News APIs

Rules

Never perform reasoning.

Never generate recommendations.

Output

Raw external information.

---

## 2. Facts Layer

Purpose

Transform external information into normalized business facts.

Examples

PortfolioFacts

Contains

- Portfolio value
- Cash
- Allocation
- Positions
- Pending orders

MarketFacts

Contains

- Market mood
- Volatility
- Major indices
- Crypto
- Commodities

InvestorFacts

Contains

- Investment Policy
- Investor DNA
- Behaviour
- Objectives

OpportunityFacts

Contains

- Price
- Daily performance
- Asset class
- Metadata

RiskFacts

Contains

Portfolio risks.

Policy risks.

Market risks.

Rules

Facts are deterministic.

Facts never contain opinions.

---

## 3. Discovery Layer

Purpose

Identify assets worthy of analysis.

Pipeline

Universe

↓

Market Scanner

↓

Candidate Opportunities

↓

Opportunity Facts

↓

Opportunity Scorecards

Responsibilities

Discover.

Never recommend.

---

## 4. Scorecard Layer

Purpose

Transform facts into measurable investment quality.

Example

```
Opportunity Scorecard

Momentum

Quality

Valuation

Growth

Volatility

Liquidity

Overall Score
```

Rules

Scorecards evaluate.

They never decide.

---

## 5. Committee Layer

Purpose

Independent expert reasoning.

Each committee owns exactly one domain.

Portfolio Committee

Mission

Improve portfolio construction.

Consumes

PortfolioFacts

InvestorFacts

Produces

CommitteeVote

---

Market Committee

Mission

Interpret current market conditions.

Consumes

MarketFacts

Produces

CommitteeVote

---

Opportunity Committee

Mission

Evaluate investment attractiveness.

Consumes

OpportunityScorecard

Produces

CommitteeVote

---

Risk Committee

Mission

Protect downside.

Consumes

RiskFacts

PortfolioFacts

Produces

CommitteeVote

---

Policy Committee

Mission

Ensure recommendations respect the Investment Policy.

Consumes

InvestorFacts

PortfolioFacts

Produces

CommitteeVote

---

Behaviour Committee

Mission

Protect the investor from behavioural mistakes.

Consumes

InvestorFacts

Recommendation History

Produces

CommitteeVote

---

Every committee is independent.

Committees never call external APIs.

Committees never communicate with one another.

---

## 6. Executive Board

Purpose

Transform committee opinions into one executive decision.

Consumes

CommitteeVote[]

Produces

ExecutiveDecision

Responsibilities

- Aggregate votes
- Resolve disagreements
- Handle ties
- Calculate confidence
- Produce rationale

Rules

Executive Board never accesses facts.

Executive Board only knows committee votes.

---

## 7. Communication Layer

Purpose

Explain executive decisions.

Components

ExecutiveSummaryService

ExecutiveBriefService

Dashboard Renderers

Responsibilities

Explain

- What changed?
- Why does it matter?
- Why does it matter for me?
- What should I do?
- Why should I trust this?

---

## 8. Presentation Layer

Interfaces

Dashboard

REST API

Mobile

Chat

Email

Notifications

Future

Voice

Wearables

Automations

---

# Domain Model

PortfolioFacts

Represents the investor's current portfolio.

---

MarketFacts

Represents current market conditions.

---

InvestorFacts

Represents investor objectives, preferences and policy.

---

OpportunityFacts

Represents one investment candidate.

---

OpportunityScorecard

Represents numerical investment quality.

---

CommitteeVote

Represents one expert opinion.

---

ExecutiveDecision

Represents the Executive Board decision.

---

ExecutiveBrief

Represents the explanation delivered to the investor.

---

# System Pipeline

```
External World

↓

Connectors

↓

Facts

↓

Scanner

↓

Opportunity Facts

↓

Scorecards

↓

Committees

↓

Executive Board

↓

Executive Decision

↓

Executive Brief

↓

Dashboard
```

---

# Dependency Rules

Allowed

```
Connector

↓

Facts Service

↓

Facts

↓

Scorecard

↓

Committee

↓

Executive Board

↓

Executive Brief

↓

Dashboard
```

Forbidden

Committee

↓

Yahoo

Forbidden

Committee

↓

eToro

Forbidden

Executive Board

↓

Facts

Forbidden

Dashboard

↓

Broker

Every dependency must flow downward.

---

# Explainability

Every recommendation must answer

What changed?

↓

Why?

↓

Evidence?

↓

Confidence?

↓

Recommendation

Every recommendation must cite supporting facts.

---

# Learning Layer (Roadmap)

Future pipeline

```
Recommendation

↓

Execution

↓

Outcome

↓

Lesson

↓

Memory

↓

Behaviour

↓

Future Decisions
```

Future capabilities

- Recommendation history
- Outcome analysis
- Replay engine
- Behaviour coaching
- Confidence calibration
- Continuous learning

---

# Engineering Principles

Facts are deterministic.

Reasoning is modular.

Committees are independent.

Executive Board is transparent.

Learning is continuous.

The investor always remains in control.

Every recommendation is explainable.

Every service has one responsibility.

---

# Project Structure

```
app/

api/

brokers/

providers/

domain/

services/

    connectors/

    facts/

    scanner/

    scorecards/

    committees/

    executive/

    communication/

repositories/

tests/
```

---

# Development Roadmap

## Phase 1 ✅ Foundation

- FastAPI
- Next.js
- eToro integration
- Portfolio
- Dashboard

---

## Phase 2 ✅ Executive Brain

- PortfolioFacts
- MarketFacts
- Executive Board
- Committee Votes

---

## Phase 3 🚧 Intelligence

- Opportunity Scanner
- Opportunity Scorecards
- Risk Committee
- Policy Committee
- Behaviour Committee

---

## Phase 4 🚧 Learning

- Recommendation Memory
- Outcome Analysis
- Replay Engine
- Behaviour Coaching

---

## Phase 5 🚧 Artificial CIO

Daily Executive Meeting

↓

Committee Votes

↓

Executive Decision

↓

Executive Brief

↓

Continuous Learning

---

# Long-Term Vision

MOVRvest is an Artificial Chief Investment Officer.

Its mission is not to predict markets.

Its mission is to help investors consistently make better investment decisions by transforming verified facts into transparent, explainable and trustworthy executive recommendations.

Trust is the product.

Everything else exists to support it.
---

<!-- ─────────────────────────────────────────────────────────────────────
     END OF HISTORICAL v4.0. The current architecture follows.
     ───────────────────────────────────────────────────────────────── -->

# Cognitive Architecture v5.0

**This is the current architecture.**

MOVRvest models how an investment executive thinks.

Every execution cycle follows the same immutable pipeline:

Reality
    ↓
Evidence
    ↓
Perception
    ↓
Brain (Working Memory)
    ↓
Reasoning
    ↓
Executive Committee
    ↓
Artificial CIO
    ↓
Communication
    ↓
Executive Brief
    ↓
Investor

The investor always remains in control.


---

# Brain

The Brain is the canonical working memory of MOVRvest.

It never performs reasoning.

It never makes recommendations.

It never renders UI.

Its only responsibility is to represent the current investment reality.

Contains:

- Portfolio
- Market
- Macro
- Investor
- Investment Policy
- Evidence
- Memory
- Timeline

Question answered:

"What is true?"


---

# Reasoning

Reasoning is distributed.

Each analyst owns one domain.

Examples:

- Portfolio Analyst
- Market Analyst
- Risk Analyst
- Valuation Analyst
- Behaviour Analyst
- Macro Analyst

Each produces an immutable Assessment.

Assessments never contain investment decisions.


---

# Artificial CIO

The Artificial CIO owns investment judgment.

Input:

- Assessments
- Committee opinions
- Investment Policy

Output:

ExecutiveDecision

Decision States

- REJECT
- INVESTIGATE
- MONITOR
- PREPARE
- RECOMMEND

Only the Artificial CIO may produce investment recommendations.


---

# Communication

Communication never reasons.

Communication explains.

It transforms ExecutiveDecision into ExecutiveBrief.

Every Executive Brief answers:

1. What changed?
2. Why does it matter?
3. Why does it matter for me?
4. What should I do?
5. Why should I trust this?


---

# Engineering Constitution

These principles are architectural invariants.

1. Evidence before inference.
2. The Brain stores facts, never conclusions.
3. Analysts produce assessments, never decisions.
4. The Executive Committee debates.
5. The Artificial CIO owns judgment.
6. Communication explains decisions.
7. The Dashboard presents information but never reasons.
8. One business concept equals one canonical model.
9. One canonical execution pipeline.
10. The investor always remains in control.
11. Absent evidence is reported as absent, never estimated.


---

# How v5.0 Is Implemented

The stages above map onto real packages. This section exists so the
architecture can be checked against the code rather than taken on trust.

| Stage | Package | Produces |
|---|---|---|
| Perception | `app/application/brain/perception` | Snapshots and per-security evidence |
| Brain | `app/brain` via `BrainBuilderService` | `Brain` |
| Reasoning | `app/application/brain/reasoning` | `ReasoningSnapshot` |
| Executive Committee | `app/application/committees` | `CommitteeOpinion[]` |
| Decision evidence | `app/application/executive` | `DecisionEvidence` |
| Artificial CIO | `app/cio` | `ExecutiveDecision` |
| Investment thesis | `app/application/thesis` | `InvestmentThesis` |
| Communication | `app/application/brief` | `ExecutiveBrief` |
| Presentation | `app/renderers` | View models |
| Delivery | `app/api`, `app/commands`, `apps/web` | Brief on a surface |

Orchestration lives in `app/application/workspace`: `ExecutivePipeline` for
one symbol, `PortfolioBriefingService` for every holding ranked by
conviction, and `BrainSnapshotService` for facts alone.

Package-level detail, including what was removed and what remains
transitional, is in
[`architecture/REPOSITORY_INVENTORY.md`](architecture/REPOSITORY_INVENTORY.md).

## Where the platform is honest about not knowing

Principle 11 is load-bearing, so the gaps are named rather than filled:

- A holding no watchlist can name keeps a visible `#id` identity instead of
  being dropped or guessed
- Investment cases carry no price targets or upside projections, because the
  platform cannot evidence them
- `consistency_score` reports the neutral midpoint until a Learning layer
  supplies decision history
- Asset-class policy targets are not scored while holdings are unclassified,
  since the drift would measure the missing classification
- Unrealized P&L, pending orders and the change feed are reported as absent
  when the backend does not publish them

---

# Two Validation Boundaries: Identity and Grounding

Reading a primary source has two independent failure modes, and they need
two independent guarantees. Conflating them is easy, because a failure of
either one produces a confident, well-cited, wrong answer.

```text
                    IDENTITY VALIDATION
        Does this document belong to the intended security?
                            ↓
                    GROUNDING VALIDATION
        Do these facts belong to this document?
```

**Grounding validation** proves that extracted facts belong to the document.
Every segment carries a verbatim span, the span is checked against the
source text, and an extraction quoting words that are not there is discarded
in full rather than in part. This is enforced in
`CompanyKnowledgeExtractor`.

**Identity validation** proves that the document belongs to the security.
Nothing about grounding can establish this: the quotes can be exact, the
document genuine, the citations correct, and the whole reading still be
about a different company. It is enforced *before* extraction begins, by
asking for structural knowledge only where the security's playbook expects
company accounts (`CompanyResearchService._structural_knowledge`).

The boundaries are complementary rather than overlapping, and each was
demonstrated by a distinct live failure:

| | Identity failure | Grounding failure |
|---|---|---|
| Live case | `BTC` resolved against the SEC to a trust issuing shares that track Bitcoin | Extraction paraphrased across a table boundary, reading text on either side of a cell edge as continuous prose |
| Document | Genuine | Genuine |
| Extraction | Grounded, citations correct | Ungrounded |
| Subject | **Wrong** | Correct |
| Detected by | Nothing downstream — the answer looks correct | The grounding contract, which rejected it |
| Fix | Structural: never ask a token or a fund for company accounts | Contract held, question narrowed: five to fifteen words from one run of prose, retried under the identical rule |

The identity failure is the more instructive of the two, because **no
amount of better prompting would ever solve it.** The model was asked to
read a real annual report and read it correctly; the error was in which
document it was handed. A validation layer that only checks the reading
cannot catch an error in the subject, so the invariant has to be enforced
upstream of the reading — which is why it lives in the seam that resolves
sources, not in the extractor.

Ticker namespaces are not global, and this generalises past the one case:
any new `PrimarySourceProvider` inherits the same obligation. A provider
that resolves the wrong issuer produces perfectly grounded knowledge about
the wrong business.

