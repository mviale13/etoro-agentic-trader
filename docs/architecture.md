# MOVRvest Architecture v4.0

> "An Artificial Chief Investment Officer (ACIO)"

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