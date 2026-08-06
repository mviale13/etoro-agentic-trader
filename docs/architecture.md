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

# The Evidence Pipeline

Reading a primary source has independent failure modes, and each needs
its own guarantee. Conflating them is easy, because a failure of any one
of them produces a confident, well-cited, wrong answer — and every one of
these was found in production, not in design.

Each boundary answers one question, prevents one class of failure, and
**assumes the boundary above it has already discharged its own**. That is
what lets each stage be simple: grounding never asks whose company this
is, and applicability never asks whether the words are really there.

```text
  ┌─────────────────────────────────────────────────────────────────┐
  │ IDENTITY          Does this document belong to the security?    │
  │                   Prevents: a perfect reading of the wrong      │
  │                   company. Nothing downstream can detect it.    │
  └─────────────────────────────────────────────────────────────────┘
                                  ↓
  ┌─────────────────────────────────────────────────────────────────┐
  │ GROUNDING         Do these facts come from this document?       │
  │                   Prevents: assertion dressed as extraction —   │
  │                   words the document never printed.             │
  └─────────────────────────────────────────────────────────────────┘
                                  ↓
  ┌─────────────────────────────────────────────────────────────────┐
  │ APPLICABILITY     Does the cited content support the claim it   │
  │                   was cited for?                                │
  │                                                                 │
  │   quantitative    Prevents: a column header cited as a          │
  │                   segment's revenue. Real words, real number,   │
  │                   no relationship between them.                 │
  │                                                                 │
  │   narrative       Prevents: one sentence about restated figures │
  │                   cited as three segments' business.            │
  └─────────────────────────────────────────────────────────────────┘
                                  ↓
                             KNOWLEDGE
                    Facts, each carrying its own evidence
                                  ↓
                     TRANSLATION  →  COMMUNICATION
```

**Why the platform prefers explicit absence.** Each boundary can only
refuse; none can repair. A refused claim leaves an absence with its
reason attached, and every surface reports that absence rather than
filling it — because the alternative is a plausible figure or a fluent
description that reads exactly like a measurement and is not one. An
absence is a fact about this platform's reach. A plausible substitute is
a claim about a company.

## Evidence has kinds, and they are not equally strong

The boundaries above say what a citation must survive. This says what a
citation *is*, and the difference turned out to matter more than either
alone. It was not designed up front; it emerged from production, and the
schema 5 → 6 migration measured it.

```text
Structured evidence        →  table coordinates
        ↓
Semi-structured evidence   →  document regions
        ↓
Unstructured evidence      →  grounded spans
```

**An address is not a reading.** A table coordinate names a cell: the
platform goes to that address in a document it parsed itself and reads
what is there. A narrative description is a *choice* of words made by
whatever read the filing. Those are different kinds of evidence, and the
difference is not one of confidence — it is one of nature.

**Reproducibility is therefore a property of the evidence, not of the
reader.** Re-reading seven companies under a new schema, every measured
size came back identical to the digit and every quoted span moved. The
sizes are addresses, so two independent readings resolve to the same
cell. The spans are readings, so two independent readings legitimately
choose different words while both remain true. Neither is a defect. A
platform that expects a span to be stable has misunderstood what a span
is.

### The acquisition principle

> **Always prefer the strongest structural evidence the document
> actually offers.**

In practice, and in this order:

- a **table coordinate** before a numeric span
- a **document region** before positional proximity
- **positional proximity** before an unsupported absence

This is not a tenth invariant. The invariants say what a claim must
establish; this says how the platform should go about establishing it,
and it is a matter of acquisition rather than of truth. A weaker
mechanism is not wrong — proximity is sound evidence on a document that
offers nothing better — it is simply what to fall back to, never what to
reach for first.

The corollary is what keeps it honest: **preferring stronger evidence
must never mean accepting more**. Every mechanism, strong or weak,
discharges the identical boundaries above. A structurally selected span
passes the same grounding and applicability checks a positionally
selected one does; what changes is which span is offered, never what it
has to survive.

The boundaries are also **independent**, which is why they are separate
stages rather than one validator. A reading can be perfectly grounded and
about the wrong company; perfectly applicable and quoting words the
document never printed; identified, grounded, and attached to a number it
does not support. Passing one says nothing about the others.

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

**Applicability validation** proves that the cited content supports the
specific fact asserted. Nothing about grounding can establish this
either: the quoted words can be exactly present and say nothing about
the number attached to them, or about the segment they were attached to.
It is enforced in `app/domain/tabular_evidence.py` for quantities and
`app/domain/prose_evidence.py` for descriptions, over the shared
vocabulary in `app/domain/evidence.py`. The distinction that names it is
worth keeping in these words:

- **Evidence existence** — the cited content is in the source. What
  grounding establishes.
- **Evidence applicability** — the cited content supports the fact it
  was cited for. What grounding cannot reach.

The boundaries are complementary rather than overlapping, and each was
demonstrated by a distinct live failure:

| | Identity failure | Grounding failure | Applicability failure |
|---|---|---|---|
| Live case | `BTC` resolved against the SEC to a trust issuing shares that track Bitcoin | Extraction paraphrased across a table boundary, reading text on either side of a cell edge as continuous prose | Reading Volkswagen's segment table, the extraction cited a *column header* for two of three segments |
| Document | Genuine | Genuine | Genuine |
| Extraction | Grounded, citations correct | Ungrounded | Grounded, citations verbatim |
| Subject | **Wrong** | Correct | Correct |
| Number | — | — | Correct |
| What was proven | Everything except whose company it was | — | That the words exist, and nothing else |
| Detected by | Nothing downstream — the answer looks correct | The grounding contract, which rejected it | Nothing downstream — the shares were right |
| Fix | Structural: never ask a token or a fund for company accounts | Contract held, question narrowed: five to fifteen words from one run of prose, retried under the identical rule | Structural: a quantitative citation is an address into a table this platform parsed, not a span a model copied |

The identity failure is the more instructive of the three, because **no
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

## How a quantitative fact discharges applicability

The identity boundary is enforced upstream of the reading because no
prompt could ever fix it. The applicability boundary is the same lesson
one level down: **no prompt can fix it either**, and the wording was
tried. The extraction was told, in as many words, not to join text across
a table cell — and the instruction is unenforceable, because by the time
the model sees the document the cell boundary has been stripped out of
it. A rule nothing can check is a wish.

So the evidence changed shape rather than the prompt changing wording.
Three moves, and each is structural:

**The document keeps its tables.** `SourceDocument` carries
`performance_tables` alongside the prose, parsed by `app/providers/
document_text.py` from the same markup, so a filing is read as words
*and* as the grid it printed. The prose reduction is byte-for-byte the
one the platform always used — the sections are located by searching it,
and a different reduction would silently locate different sections.

**A citation is an address, not a span.** The reading names a table, a
row and a column, and states what it believes is printed there. This
platform reads that cell itself and compares. A model cannot cite a
column header for a segment's revenue, because the address resolves to a
cell whose contents the validator reads for itself — and a header prints
no number, so the citation is refused before anyone has to notice that
the number happened to be right.

**A share is arithmetic this platform performs.** A revenue share is not
a fact a filing states; it is one number over another. Asking a model for
the share and a quote to go with it asks it to compute and then evidence
the computation with a span, which no span can do. So both figures are
cited, both are checked, and `MeasuredShare` divides. `BusinessSegment`
has no field for a bare share — the size exists only as the two printed
figures it came from, which makes an unevidenced share unrepresentable
rather than merely discouraged.

The invariant tying the two figures together is that they sit in one
table and agree on exactly one coordinate. The shared coordinate is what
makes them comparable; the coordinate they differ on is what names the
part and the whole. One table also means one scale, so a numerator in
millions over a denominator in thousands cannot arise without this
platform having to parse a caption to discover what the scale was.

**Both layouts are normal, and assuming one of them is a bug.** The first
design required the two figures to share a *column* — right for Disney's
10-K, where segments run down the page and the columns are periods, and
wrong for Volkswagen's IFRS segment note, where the segments run across
the top and the shared coordinate is the row. Fitting the rule to the
American layout would have left every European filing's sizes
permanently unmeasurable, and the failure would have looked like honest
absence rather than like a bug.

Verified against both, live:

| | Disney 10-K, via EDGAR | Volkswagen annual report, via Investor Relations |
|---|---|---|
| Layout | Segments as rows, periods as columns | Segments as columns, line items as rows |
| Shared coordinate | The column, `"2025"` | The row, `"Umsatzerlöse"` |
| Measured | 45% / 19% / 38% | 76% / 13% / 19% |
| Sums to | 102% of consolidated revenue | 108.5% of consolidated revenue |

The sums are above 100% and both are correct: consolidated revenue is the
segments *less* what they sold each other. How far above depends on how
much business the parts do with one another, which no constant predicts —
so the sum check is now a backstop against a total that is not a total,
not the guard it once was. What catches a misread figure is the cell it
was read from.

## The same boundary for a description

A quantity needs its row and its column. A description needs to be about
the thing it is attached to, and the failure looks identical: reading
Volkswagen's segment note, all three segments were cited with one
sentence — *"Die Vorjahreswerte entsprechen der geänderten
Berichtsstruktur"*, the prior-year figures correspond to the changed
reporting structure. Exactly present, about accounting, describing no
segment at all.

**The invariant is unambiguous ownership: a narrative citation must
establish that the cited text belongs to the claim it supports.** That
is what the boundary requires, and it is deliberately stated without
naming a mechanism — position is the best evidence available today, and
structural section boundaries, document markup or the filer's own tagging
may be better evidence tomorrow. An architecture document that named the
mechanism as the invariant would have to be weakened to accept its own
improvement.

**Position is the current mechanism.** What a table gives a number, prose
gives a description: a figure belongs to the row whose label leads it, so
a description belongs to the segment whose name most recently precedes
it. The document's own naming of its segments partitions the prose the
way row labels partition a table, and that partition is something this
platform computes rather than accepts.

Two positional rules discharge it, both measured rather than chosen:

- **Ownership by naming** — the span sits under this segment's name and
  no other's. On Volkswagen this refuses two of three outright.
- **Proximity** — it sits within `NEARBY` characters of that naming.
  This refuses the third, which passes the naming rule *by accident*
  because the footnote follows the last segment the document names.
  Sound citations measured 0, 23 and 51 characters from their naming;
  the boilerplate measured 814 and 1474.

Both are implementation. Replacing them with something that establishes
ownership more directly is an improvement to this section, not a
contradiction of it.

**What an owner is, stated apart from how one is found.** A structural
owner is *the smallest region of the document that can be shown to
correspond uniquely to the claim*. Every word of that carries weight:

- **smallest** — a region that covers the whole filing owns nothing in
  particular, and a claim owned by everything is unowned.
- **shown** — computed by this platform from the document, never
  accepted from whatever read it.
- **uniquely** — if two regions could own the claim, none does.
  Ambiguity is not resolved by preference or by order; it means there is
  no structural owner, and the platform falls back to the weaker
  mechanism or reports the absence.

Today such a region is introduced by a heading. Tomorrow it may come
from XBRL narrative blocks, tagged document regions, semantic anchors,
or a filer's explicit section markup. Each of those would be a stronger
mechanism for the same concept, and none of them changes the concept —
which is the test of whether this section is written at the right
altitude.

**Why a stronger mechanism is now needed, measured rather than argued.**
Meta's 10-K is not an ambiguous document; this platform's ownership
model is. The only exact occurrences of the stored names `Family of Apps
(FoA)` and `Reality Labs (RL)` sit twenty-five characters apart, in one
summary sentence, *after* all the descriptive prose — which lives under
the headings `Family of Apps Products` and `Reality Labs Products`. So
"the segment whose name most recently precedes it" hands nearly the
whole document to whichever segment that late sentence names last. The
partition is not imprecise. It is inverted.

That is a different class of failure from a poorly chosen span, and it
is why a targeted repair recovered nothing: asking again for a better
citation cannot correct a region model. The document's structure is
machine-readable — both headings are one short bold span inside a block
element, and `Flattened.markup_span` already maps prose back to the
markup that carries them.

What is deliberately **not** a rule is that the span contain the
segment's name. Two of Disney's three sound citations do not — the name
is the sentence's subject and the span its predicate — so requiring it
would reject good evidence and drive a reading toward quoting headings.

### Three claims, three contracts, degrading apart

The rule's first consequence was that Volkswagen lost everything: one
span used to prove both that a segment existed and what it did, so an
inapplicable citation took the segment's identity and its measured size
with it — facts established by something else entirely. So a segment is
now three independent claims:

| Claim | Evidenced by | When it fails |
|---|---|---|
| **Identity** — the company has a part it calls this | the document naming it, which this platform locates | the whole reading is discarded |
| **Size** — what it earned, as a share of a printed total | two cells of one table, checked against the document | the size is absent |
| **Description** — what it does and how it earns | a span the document prints under this segment's name | the description is absent, with its reason |

Volkswagen therefore keeps its three segments and their measured sizes,
and reports what they do as absent. That is the honest outcome, and it
is more than the platform could say before the slice rather than less.

### Two defects only a live document exposes

**A name inside another word is not a naming.** Disney's Entertainment
section contains the phrase "non-sports focused global film". Normalised
to letters, that phrase contains "sports" — read as a naming it opens the
Sports region in the middle of Entertainment's, and Entertainment's own
description is refused as belonging to Sports. Silently, because an
inapplicable description is an absence rather than an error.

**Case folding changes a string's length.** German "ß" folds to "ss", so
folding a document before indexing it shifts every position after the
first one. The boundary check then read the wrong character, concluded
that Volkswagen's report never names "Pkw und leichte Nutzfahrzeuge", and
discarded the entire reading — identity, sizes and all.

### What this does not close

The current mechanism is positional, so it cannot tell a description from
a note that happens to sit exactly where a description would.
Volkswagen's footnote was caught at 814 characters; the same sentence one
line below a segment's description would pass. Closing that means judging
what a sentence is *about*, which is a different kind of evidence for the
same invariant — and the reason the invariant is worded as ownership
rather than as distance.

Nor is a description retried. An inapplicable span is an absence rather
than a rejection, so it does not trigger the reread that a failed
grounding contract does — and that is deliberate. Reading again until
something passes would change the reader's objective from *read this
document* to *find something acceptable*, which are not the same
activity. If coverage proves unacceptable in production, the answer is a
better evidence model, not more attempts under this one.

Coverage did prove unacceptable — the archetype rules classify two
companies in eight — and the response holds that line rather than
crossing it. **Repairing the evidence for a claim already extracted is
not retrying the reading.** A targeted repair asks one bounded question
about one existing claim — same segment, same document, same period, no
new factual content — and accepts an explicit absence as an answer. It
cannot drift into *find something acceptable*, because it is not
permitted to change what is being claimed, only to evidence it or fail.
A repaired span records that it came from a repair, so a reader never
sees a second attempt presented as a first reading.

Built, and it recovered nothing. Across every filing holding a refused
citation to repair, each repair was either refused again on identical
grounds or answered honestly that the document contains no such words.
That is the mechanism working and the boundary holding — and it is also
the measurement that names the real defect. Meta's 10-K introduces both
segments together and then describes them in order, so the description
of the first falls after the naming of the second, and Reality Labs'
own sits 402 characters from its naming against a `NEARBY` of 300. The
citation was never the problem; the partition was. A second request
cannot repair an ownership model, which is why what follows replaces the
model rather than asking a third time.

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

**The reviewed hash turned out to separate two claims that look like one.**
It is not a cache key and not merely a change detector. It proves that the
bytes being read are the bytes a person approved — and *authenticity and
approval are different claims*. When Volkswagen publishes its 2026 report
at the same address, those bytes will be entirely genuine, correctly
signed by their own LEI, and still refused, because nobody has reviewed
them. A provider that treated "authentic" as "approved" would have no way
to express the difference, and would follow a moving document forever
without ever being wrong in a way it could detect.

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
hand — and the citations do not demonstrate them. The first is recorded
in `PROJECT_STATE.md` as a gap; the second became its own slice, and is
the third validation boundary below.

## The backbone

Primary sources are one link in a longer chain, and the chain is the
Artificial CIO:

```text
Identity  →  Primary Source Resolution  →  Grounding  →  Applicability  →  Knowledge
                                                                                ↓
                                                                            Archetype
                                                                                ↓
             Communication  ←  Decision  ←  Reasoning  ←───────────────────────┘
```

**Knowledge → Archetype is where facts become understanding**, and it is
the only link on the chain that concludes rather than checks. Everything
above it narrows what may be assumed about a document; the archetype
rules read what survived and answer a question no document is asked —
what kind of business is this. They are deterministic and they never ask
a model, because a model would answer from what it knows about the
company, and that is the industry taxonomy this link replaces
(`app/services/archetype_engine.py`).

It concludes but does not decide. What kind of business a company is
still reaches the Artificial CIO as evidence, exactly as an analyst's
assessment does.

Each arrow is a narrowing of what the next stage is allowed to assume,
and every stage exists because the one before it can fail in a way the
one after it cannot detect. New capabilities — providers, analysts,
playbooks, committees — belong somewhere on this chain. A capability that
bypasses a link is not a shortcut; it is a claim made without the check
that link performs.

## This is an evidence graph, not a retrieval system

Worth naming, because the difference decides what gets built next.

A retrieval system fetches text that is *relevant* to a question and
hands it to something that writes an answer. Relevance is the only
relationship it models, it is unverifiable after the fact, and a
retrieved passage that turns out not to support the sentence beside it
leaves no trace that it did not.

What this platform has accumulated instead is a graph in which every
claim carries its relationships explicitly:

```text
                    ┌──────────────────┐
                    │ Source document  │
                    └────────┬─────────┘
                             │ identity — whose company this is
                    ┌────────┴─────────┐
                    │     Document     │
                    └────┬────────┬────┘
              table ─────┘        └───── region
                    │                    │
              ┌─────┴─────┐        ┌─────┴─────┐
              │   Cell    │        │   Span    │
              └─────┬─────┘        └─────┬─────┘
                    │  applicability     │  ownership
                    └────────┬───────────┘
                             ↓
                          Claim
```

Each edge is a checkable assertion rather than a similarity score, and
each is checked by a different boundary: identity says the document is
this company's, ownership says the region is this claim's, applicability
says the cell or the span supports what it was cited for. A claim
missing an edge is not weakly supported — it is *absent*, and says so.

Two consequences follow, and both have already been paid for. An edge
can be strengthened without the graph changing shape, which is why
replacing positional ownership with structural ownership is an
improvement rather than a redesign. And a claim can be walked backwards
from a dashboard to a cell in a filing a reader can open, which is what
the platform sells: not an answer that sounds well-sourced, but one
whose sources can be checked.

