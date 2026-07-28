# MOVRvest Artificial Chief Investment Officer (ACIO)

## Vision

MOVRvest is an Artificial Chief Investment Officer.

Its purpose is not to predict markets.

Its purpose is to help investors make better decisions through transparent,
explainable and continuously improving reasoning.

The investor always remains in control.

---

# Core Questions

Every recommendation must answer:

1. What changed?

2. Why does it matter?

3. Why does it matter for me?

4. What should I do?

5. Why should I trust this recommendation?

---

# ACIO Architecture

External World

↓

Brokers

↓

Facts

↓

Signals

↓

Committees

↓

Executive Board

↓

Executive Brief

↓

Dashboard

---

# Layer 1 — Brokers

Responsibility:

Connect to external systems.

Examples:

- eToro
- Yahoo Finance
- SEC
- FRED
- News APIs

Rules:

- No business logic
- No recommendations
- Only retrieve data

---

# Layer 2 — Facts

Facts represent objective reality.

Examples:

- PortfolioFacts
- CompanyFacts
- MarketFacts
- MacroFacts
- NewsFacts

Facts never contain opinions.

---

# Layer 3 — Signals

Signals interpret facts.

Examples:

Forward PE = 32

↓

Valuation appears expensive

Revenue Growth accelerating

↓

Business quality improving

Signals remain deterministic and explainable.

---

# Layer 4 — Committees

Each committee represents a specialist.

Examples:

- Portfolio Committee
- Market Committee
- Value Committee
- Momentum Committee
- Quality Committee
- Risk Committee
- Diversification Committee
- Policy Committee

Each committee produces:

- Vote
- Confidence
- Evidence

Committees never make the final decision.

---

# Layer 5 — Executive Board

The Executive Board aggregates committee votes.

Output:

- BUY
- HOLD
- SELL
- WAIT

with supporting rationale.

---

# Layer 6 — Executive Brief

Communication layer.

Answers:

- What changed?
- Why?
- Recommendation
- Supporting evidence

No calculations occur here.

---

# Guiding Principles

## Human in control

MOVRvest advises.

The investor decides.

## Explainability

Every recommendation must be supported by evidence.

## Separation of concerns

Brokers retrieve.

Facts describe.

Signals interpret.

Committees evaluate.

Executive Board decides.

Executive Brief communicates.

## Continuous learning

Recommendations and outcomes are stored to improve future reasoning.

---

# Current Roadmap

## Completed

- eToro Account Broker
- Portfolio Facts
- eToro Watchlist Broker
- Watchlist Parser
- Watchlist Domain
- Executive Brief UI
- Executive Committee
- Dashboard

## In Progress

- Company Facts
- Market Broker
- Signal Engine v2

## Planned

- Multi-broker support
- Earnings analysis
- SEC filings
- Macro reasoning
- Learning Engine v2
- Autonomous research agents
