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

## How the ESEF provider discharges it

The first provider to inherit the obligation, and the one that shows what
discharging it costs. Europe indexes filers by LEI rather than by ticker,
so `EsefProvider` cannot ask its register anything until it knows who the
security belongs to. Identity is therefore established in three steps,
none of which is a resemblance:

```text
symbol  →  ISIN            →  LEI       →  the filing  →  the filing's own LEI
          reviewed list       GLEIF        the index       checked before reading
```

Only the first step is written down, because only the first step has no
authority to ask, and that step is a reviewed list rather than a lookup
for a demonstrated reason. `yfinance` will answer `Ticker("ASML.AS").isin`
with `AR0725224551` — an Argentine CEDEAR that tracks ASML rather than
ASML — and `Ticker("BNP.PA").isin` with nothing. The first answer is the
dangerous one: it is a real security of a real issuer that files real
reports, so every downstream check passes and the reading is confidently
about the wrong company.

The last step is the same invariant enforced a second time, on the other
side of the fetch. ESEF requires a filer to identify itself by LEI in
every context of its own document, so the document can be asked whether
it belongs to the issuer it was fetched for — and a register that served
the wrong file is caught before a single word of it is read. Cheap, and
worth doing precisely because the failure it catches is the one nothing
downstream can see.

---

# The Primary Source Ecosystem

The platform no longer has "a filings provider". It has an ecosystem, and
the shape of it is what makes the next jurisdiction cheap:

```text
Security
        ↓
Identity Resolution
        ↓
Primary Source Resolver
        ↓
Primary Source Providers
        ├── EDGAR                 the SEC's own record                      built
        ├── ESEF                  Europe's mechanisms, via filings.xbrl.org built
        ├── Investor Relations    the company's own published report        built
        └── Manual Documents      a document handed to the platform         next
        ↓
Grounded Knowledge Extraction
        ↓
Company Knowledge Store
```

**New jurisdictions should require new providers, not new reasoning.**

That is a claim the repository can now be checked against rather than an
intention. ESEF is a genuinely different regulatory ecosystem from EDGAR —
no single regulator, no ticker index, no `Item 1`, a separate national
mechanism per member state, and documents in any EEA language. Adding it
changed nothing downstream of `PrimarySourceResolver`, and changed
`PrimarySourceResolver` itself only by naming a second provider in its
default order. The canonical `PrimarySource`, the extraction, the
grounding contract, the schema versioning, the store and the cache-first
policy were all untouched. `PrimarySourceResolver` still builds its
default providers in a single small block, and that block is the whole of
what a jurisdiction costs the pipeline.

## Every provider answers three questions

Before extraction begins, and in this order:

```text
1. Can I retrieve the document?
2. Can I prove whose document it is?
3. Can I prove this issuer belongs to the requested security?
```

Only when all three answer yes does anything get read. **Extraction never
becomes responsible for identity** — it cannot be, because a reading of
the wrong company's report is indistinguishable from a reading of the
right one at the point where extraction happens.

What the three providers show is that the *questions* are constant and the
*authorities* are not:

| | EDGAR | ESEF | Investor Relations |
|---|---|---|---|
| Retrieve | the register's archive | the register's index | a reviewed location, and the hash it was reviewed against |
| Whose document | the register's index | the index, and the document's own LEI | the document's own LEI, alone |
| Which security | the register's ticker index | the reviewed issuer list and GLEIF | the reviewed issuer list and GLEIF |

Each cell is delegated where an authority exists and reviewed where none
does. Nothing is inferred in any of them.

## Authority, provenance, verification

Three separate facts, carried on `PrimarySource`, because collapsing them
loses information a reader needs:

- **`authority`** — what kind of source this is. `REGULATOR_FILED` or
  `ISSUER_PUBLISHED`. Descriptive, deliberately *not* ranked: no number,
  no ordering. A score invites arithmetic on it and an ordering invites
  comparison without knowing what actually differs. What differs is
  written down here, once, and a reader is owed the fact rather than a
  number derived from it.
- **`provider`** — provenance. Who supplied it: "SEC EDGAR", "ESEF",
  "Official Investor Relations".
- **`verification`** — which identity checks actually succeeded on the
  way to this document.

Authority belongs to the **source**, never to the provider. The Investor
Relations provider proves why: Volkswagen publishes the very ESEF package
it filed, so that provider returns a regulated artefact — and could
equally return a PDF that nobody received on a dated record. One provider,
two authorities, and the distinction has to live where the difference is.

The three facts are independent, and `verification` is what stops
`authority` being read as a ranking. EDGAR is `REGULATOR_FILED` and yet
the only check it can offer is `REGISTER_INDEXED`: a 10-K declares no LEI,
so the document never independently confirms whose it is. A Volkswagen
package obtained from Volkswagen is `ISSUER_PUBLISHED` and carries four
checks including `DOCUMENT_LEI`. Neither statement contradicts the other,
and neither would survive being flattened into a score.

## What a provider owes the ecosystem

| Obligation | Why it belongs to the provider |
|---|---|
| Establish the security's identity | Ticker namespaces are not global, and only the provider knows what its register indexes by |
| Resolve which document is current, cheaply | Knowledge is kept against a document's key, so a caller already holding it must not pay to discover that |
| Produce an immutable key | The same key must always mean the same bytes, or permanent knowledge is not permanent |
| Divide the document into the two passages read | Where those passages live is jurisdiction-specific; that there are two is not |
| Report a gap and an outage as different answers | Only one of them is worth asking about again |

Nothing on that list is about *meaning*. A provider is acquisition, never
interpretation, which is why SEDAR+, Companies House or the ASX should be
routine additions: each has a different index, a different identifier and
a different document convention, and none of them has a different idea of
what a business is.

## What production showed

Volkswagen was the first company read without a register, and it exercised
the model in four ways worth recording.

**The trust model held where it was designed to.** The reviewed hash, the
approved host, the document's own LEI and the GLEIF boundary all did the
job asked of them, and `VOW3.DE` reads as Pkw und leichte Nutzfahrzeuge
68%, Nutzfahrzeuge 13%, Finanzdienstleistungen 18% — a company that
resolved to a stated gap the day before.

**Requiring a document-declared LEI cost more coverage than expected, and
was still right.** Volkswagen's ESEF package holds three documents. Only
one is tagged. The other two are XHTML the regulation requires and the
taxonomy says nothing about — including a thirteen-megabyte management
report, which is where the *narrative* account of the business lives. So
the platform reads Volkswagen's segment note and not its business
description, because the business description cannot say whose it is.
That is the invariant working, not failing.

**An identity check found a real neighbour, not a hypothetical one.**
Volkswagen Financial Services N.V. publishes its own annual reports under
its own LEI, and its documents are genuine Volkswagen documents. Nothing
but the LEI comparison distinguishes them from the parent's.

**Two things production challenged, and neither is about trust.** First,
knowledge extracted from a German document is in German — the description
stored for `VOW3.DE` reads "Der Volkswagen Konzern berichtet die
Segmente…". Reading the original rather than a translation is the correct
behaviour and the surfaces are not yet ready for it. Second, the grounding
contract proves that a quoted span exists in the document; it does not
prove that the span evidences the number beside it. On a table-heavy
document the extraction quoted a column header for two of the three
segments. The shares were right — checked against the segment table by
hand — and the citations do not demonstrate them. Both are recorded in
`PROJECT_STATE.md` as gaps rather than fixed here, because neither is a
weakness in the trust model and both deserve their own slice.

## The backbone

Primary sources are one link in a longer chain, and the chain is the
Artificial CIO:

```text
Identity  →  Primary Source Resolution  →  Grounding  →  Knowledge
                                                              ↓
       Communication  ←  Decision  ←  Reasoning  ←────────────┘
```

Each arrow is a narrowing of what the next stage is allowed to assume,
and every stage exists because the one before it can fail in a way the
one after it cannot detect. New capabilities — providers, analysts,
playbooks, committees — belong somewhere on this chain. A capability that
bypasses a link is not a shortcut; it is a claim made without the check
that link performs.

