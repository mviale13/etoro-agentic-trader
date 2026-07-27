# MOVRvest Architecture

## Vision

MOVRvest is an explainable AI investment operating system.

It helps investors understand:

- what deserves attention,
- how their portfolio is evolving,
- why a recommendation exists,
- and how their investment behaviour changes over time.

The core philosophy is:

> Deterministic reasoning first.  
> AI communication second.

AI must not invent portfolio facts, signals, scores, or investment decisions.

Large Language Models may support:

- explanation,
- summarisation,
- coaching,
- scenario discussion,
- and natural-language communication.

---

## System Overview

```text
eToro API
    ↓
EtoroAccountBroker
    ↓
AccountSnapshot
    ↓
PortfolioService
    ↓
PortfolioSnapshot
    ↓
Timeline Repository
    ↓
SignalService
    ↓
InvestorObservationService
    ↓
DashboardService
    ↓
FastAPI Dashboard API
    ↓
movrvest-web Morning Brief
```

---

## Repository Structure

```text
etoro-agentic-trader/
├── app/
│   ├── api/
│   │   ├── main.py
│   │   ├── models/
│   │   └── routes/
│   ├── brokers/
│   ├── committees/
│   ├── domain/
│   ├── memory/
│   ├── repositories/
│   ├── services/
│   └── renderers/
├── data/
├── docs/
├── movrvest-web/
└── tests/
```

---

## Core Layers

### 1. Broker Layer

The broker layer retrieves external account data.

Current implementation:

```text
EtoroAccountBroker
```

It produces an `AccountSnapshot` containing:

- connection status,
- account mode,
- cash,
- invested value,
- unrealised profit and loss,
- equity,
- positions,
- pending orders,
- copy portfolios,
- timestamp,
- and latency.

Business services must not parse raw eToro responses directly.

---

### 2. Domain Layer

The domain layer contains framework-independent business objects.

Important domain models include:

```text
AccountSnapshot
PortfolioSnapshot
PortfolioHealth
MarketSnapshot
Opportunity
Observation
Signal
DailyReflection
InvestorDNA
DailySnapshot
Decision
Explanation
MorningBrief
```

Domain objects must not depend on:

- FastAPI,
- Pydantic API responses,
- React,
- HTTP,
- or broker-specific JSON.

---

### 3. Service Layer

Services contain application and business logic.

Current important services include:

```text
AccountService
PortfolioService
PortfolioHealthService
BriefService
DashboardService
OpportunityService
DailyReflectionService
InvestorDNAService
InvestorObservationService
SignalService
ExplanationService
```

Responsibilities remain separated:

```text
AccountService
    → retrieves account truth

PortfolioService
    → converts account data into portfolio analysis

SignalService
    → identifies facts that deserve attention

InvestorObservationService
    → turns portfolio facts into a human observation

DashboardService
    → composes the complete Morning Brief response
```

Routes remain thin and delegate work to services.

---

## Morning Brief Composition

The frontend consumes a unified dashboard response.

```text
GET /dashboard/
```

`DashboardService` composes:

- today's brief,
- portfolio,
- portfolio observation,
- daily reflection,
- Investor DNA,
- and top opportunities.

The backend owns composition.

The frontend owns presentation.

Individual endpoints remain available for testing and independent use.

---

## Timeline and Memory

MOVRvest stores one portfolio snapshot per day.

```text
data/portfolio_snapshots/
├── 2026-07-27.json
├── 2026-07-28.json
└── ...
```

The snapshot repository supports:

```text
save
latest
previous
history
```

This enables:

- daily comparisons,
- weekly and monthly changes,
- portfolio history,
- investment journaling,
- behavioural learning,
- and evolving Investor DNA.

A snapshot records facts.

Interpretation is performed by services above the repository.

---

## Signals Pipeline

Signals are deterministic facts that deserve attention.

```text
Current PortfolioSnapshot
        +
Previous PortfolioSnapshot
        ↓
SignalService
        ↓
Signal[]
```

Examples include:

- high cash allocation,
- concentrated portfolio,
- material cash reduction,
- position-count changes,
- new risk flags,
- or significant portfolio-value changes.

Signals are not recommendations.

They become inputs for:

- observations,
- insights,
- recommendations,
- reflections,
- and the Morning Brief.

---

## Committee and Decision Pipeline

Investment committees analyse distinct perspectives such as:

- value,
- momentum,
- risk,
- cash,
- and diversification.

```text
Market and Portfolio Context
        ↓
Specialist Committees
        ↓
Committee Opinions
        ↓
Committee Chairman
        ↓
Decision or Recommendation
        ↓
Explanation
```

Every recommendation should eventually answer:

- What should I do?
- Why?
- Why now?
- Why for me?
- Why not the obvious alternative?
- What could make this recommendation wrong?
- How certain is the system?

---

## Frontend

`movrvest-web` is the Next.js presentation layer.

Its main product experience is the Morning Brief.

Current dashboard components include:

```text
Header
ReflectionCard
TopOpportunitiesCard
PortfolioCard
PortfolioHealthCard
ObservationCard
InvestorDNACard
DoctorCard
ExplainCard
ChangesCard
NextActionCard
```

Frontend components must handle:

- loading,
- success,
- empty,
- and error states.

A failure in one capability must not crash the complete Morning Brief.

---

## Architectural Rules

1. Reuse existing services before creating new ones.
2. Never replace tested behaviour without understanding its consumers.
3. Routes call services, not other routes.
4. Domain objects remain independent from API and UI frameworks.
5. Broker-specific parsing remains inside the broker layer.
6. Facts, signals, observations, and recommendations remain separate concepts.
7. Memory stores evidence; services produce interpretations.
8. AI may communicate reasoning but must not invent deterministic facts.
9. Every recommendation must be explainable.
10. The system must be allowed to say, “I’m not sure.”
11. The system may recommend doing nothing.
12. Extend the proven architecture instead of introducing duplicate abstractions.

---

## Current Evolution

```text
Raw broker data
    ↓
Account facts
    ↓
Portfolio snapshot
    ↓
Historical timeline
    ↓
Signals
    ↓
Observations
    ↓
Insights
    ↓
Recommendations
    ↓
Actions
    ↓
Memory events
    ↓
Improved Investor DNA
```

The long-term objective is not merely to remember transactions.

It is to understand:

> the investor the user is becoming.