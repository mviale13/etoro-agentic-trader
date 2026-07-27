# MOVRvest Architecture

> Version: 0.6.x
>
> Explainable, agentic investment intelligence platform for eToro investors.

---

# Vision

MOVRvest is not a trading bot.

It is an AI investment operating system that continuously:

- observes markets
- understands the investor
- debates investment decisions
- explains every recommendation
- remembers past events
- learns from historical performance
- improves committee weighting over time

Every recommendation is explainable and fully auditable.

---

# High-Level Architecture

```
                Yahoo Finance
                      │
          Crypto Fear & Greed
                      │
                eToro Account
                      │
────────────────────────────────────────
          Data Acquisition Layer
────────────────────────────────────────
                      │
                      ▼
            Market Intelligence
                      │
                      ▼
             Portfolio Analysis
                      │
                      ▼
             Investment Committee
                      │
                      ▼
           Committee Chairman
                      │
                      ▼
             Recommendation
                      │
                      ▼
              Event Repository
                      │
         ┌────────────┴────────────┐
         ▼                         ▼
 Memory Engine             Committee Analytics
         │                         │
         ▼                         ▼
 Pattern Engine            Performance Engine
         │                         │
         └────────────┬────────────┘
                      ▼
               Investor DNA
                      │
                      ▼
             Executive Dashboard
```

---

# Layers

## Domain

Pure business objects.

Examples:

- Recommendation
- PortfolioSnapshot
- CommitteeDecision
- CommitteeOpinion
- CommitteeOutcome
- InvestorDNA
- MemoryEvent
- Event

Contains no infrastructure code.

---

## Providers

External market information.

Current:

- Yahoo Finance
- Crypto Fear & Greed

Future:

- Macro indicators
- SEC filings
- News providers
- Analyst consensus

---

## Brokers

External broker integrations.

Current:

- eToro

Future:

- Interactive Brokers
- Alpaca
- Binance

---

## Services

Business logic.

Current services include:

### Portfolio

- PortfolioService
- ExchangeRateService

### Market

- MarketService
- MarketIntelligenceService

### Signals

- SignalService

### Memory

- MemoryService
- MemoryBuilder

### Investor

- PatternEngine
- InvestorDNAService
- InvestorObservationService

### Committee

- CommitteeService
- CommitteeAnalyticsService
- CommitteeOutcomeService

### Dashboard

- DashboardService
- BriefService

---

# Investment Committee

Five independent experts evaluate every opportunity.

## Momentum

Trend following.

## Risk

Portfolio risk.

## Cash

Liquidity management.

## Diversification

Portfolio concentration.

## Value

Fundamental valuation.

Each member produces:

- vote
- confidence
- rationale

---

# Chairman

The Chairman aggregates committee opinions.

Current capabilities:

- majority voting
- confidence aggregation
- weighted voting support

Future:

- adaptive weights from historical performance

---

# Event Sourcing

Every important decision is persisted.

Current events:

- recommendation_generated
- recommendation_outcome_recorded
- memory_recorded

Future:

- order_executed
- portfolio_snapshot
- investor_action

---

# Memory System

Signals generate memories.

Example:

```
High Cash Position

↓

Memory

↓

Pattern

↓

Investor DNA
```

The system slowly learns investor behaviour.

---

# Pattern Engine

Converts memories into reusable patterns.

Examples:

- prefers holding cash
- frequently buys technology
- accumulates after corrections
- avoids volatility

---

# Investor DNA

Current outputs:

- confidence
- quality preference
- diversification preference
- value preference
- volatility preference

Confidence increases as more evidence is collected.

---

# Committee Analytics

Tracks committee behaviour.

Current metrics:

- recommendations
- BUY/HOLD/SELL distribution
- average confidence
- member statistics
- committee accuracy
- member accuracy

---

# Recommendation Outcomes

Recommendations can later be evaluated.

Each outcome records:

- entry price
- evaluation price
- return
- success

These outcomes feed committee analytics.

---

# Executive Dashboard

Aggregates high-level intelligence.

Current sections:

- committee statistics
- committee accuracy
- investor understanding

Future:

- portfolio summary
- recommendation history
- member leaderboard
- trend analysis
- performance charts

---

# API

Current endpoints include:

```
/today
/dashboard
/dashboard/executive
/portfolio
/portfolio/health
/observation
/investor-dna
/opportunities
/reflection
/committee/statistics
/health
```

---

# Persistence

JSON repositories.

Current:

```
data/events/
```

Future:

- PostgreSQL
- DuckDB
- Vector database
- Time-series storage

---

# Testing

Current quality gates:

- Ruff
- MyPy
- Pytest

Current status:

- ~150 typed Python source files
- 110+ automated tests
- strict static typing
- formatted codebase
- event-driven architecture

---

# Design Principles

- Explainability first
- Event-driven architecture
- Strong typing
- Immutable domain models
- Dependency inversion
- Small focused services
- Test-first development
- Human-in-the-loop investment intelligence

---

# Long-Term Roadmap

## Phase 1 ✅

Broker connectivity

## Phase 2 ✅

Portfolio intelligence

## Phase 3 ✅

Market intelligence

## Phase 4 ✅

Investment committee

## Phase 5 ✅

Persistent memory

## Phase 6 ✅

Investor DNA

## Phase 7 ✅

Committee analytics

## Phase 8 ✅

Recommendation outcome tracking

## Phase 9 ✅

Adaptive committee weighting

## Learning & Adaptive Intelligence

MOVRvest continuously improves its decision-making through an event-driven learning loop.

```text
Recommendation
        │
        ▼
Outcome
        │
        ▼
Performance Analytics
        │
        ▼
Learning Service
        │
        ▼
Regime Analytics
        │
        ▼
Adaptive Weighting
```

### Components

- CommitteeAnalyticsService
    - Global committee statistics
    - Member statistics
    - Committee performance
    - Member performance
    - Regime-specific performance

- LearningService
    - Generates learning insights
    - Suggests committee improvements

- RecommendationJournalService
    - Builds recommendation history
    - Human-readable investment journal

- RegimeWeightService
    - Computes committee weights
    - One weight table per market regime

Future versions will allow the Chairman to automatically use these adaptive weights.
```
## Next

- Recommendation backtesting
- Dynamic committee weighting
- Multi-agent debate
- Strategy benchmarking
- Autonomous portfolio management