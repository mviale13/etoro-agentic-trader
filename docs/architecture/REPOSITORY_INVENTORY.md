# MOVRvest Repository Inventory

> Living document tracking the canonical ownership of every major package.

Status: Living Architecture

---

# Purpose

This document records **what exists**, not what is intended.

Every entry below was verified against the import graph. A package is only
listed as canonical if something reachable from a real entry point —
`app/cli.py` or `app/api/main.py` — actually uses it.

> If this document and the code disagree, the code is right and this document
> is a bug.

---

# The Executable Pipeline

This is the path a decision actually travels today.

```
Reality                 eToro · Yahoo Finance
    ↓
Perception              app/application/brain/perception
    ↓
Brain                   app/brain  (via BrainBuilderService)
    ↓
Reasoning               app/application/brain/reasoning
    ↓                   → ReasoningSnapshot (5 assessments)
Executive Committee     app/application/committees
    ↓                   → CommitteeOpinion[]
Decision Evidence       app/application/executive
    ↓                   → DecisionEvidence
Artificial CIO          app/cio
    ↓                   → ExecutiveDecision
Decision Journal        app/application/learning
    ↓                   → recorded, then perceived by the next cycle
Investment Thesis       app/application/thesis
    ↓                   → InvestmentThesis
Communication           app/application/brief
    ↓                   → ExecutiveBrief
Presentation            app/renderers
    ↓
Delivery                app/api · app/commands · apps/web/movrvest-web
```

Orchestration lives in `app/application/workspace`:

| Orchestrator | Scope |
|---|---|
| `ExecutivePipeline` | One symbol, end to end |
| `PortfolioBriefingService` | Every holding, ranked by conviction |
| `CandidateResearchService` | Every evidenced watchlist candidate |
| `ExecutiveService` | Public entry point for the Artificial CIO |
| `BrainSnapshotService` | Facts only — what the Brain currently knows |

---

# Canonical Packages

| Package | Owns |
|---|---|
| `app/brain` | `Brain`, `BrainContext`, `BrainBuilder` — the working memory |
| `app/application/brain/perception` | Turning reality into facts |
| `app/application/brain/reasoning` | Analysts and `ReasoningSnapshot` |
| `app/application/committees` | `CommitteeService`, `CommitteeOpinion` |
| `app/application/executive` | `ExecutiveService`, `DecisionEvidenceBuilder` |
| `app/cio` | `ArtificialCIO`, `ExecutiveDecision`, `DecisionPolicy` |
| `app/application/learning` | `DecisionJournal` — what the CIO decided before |
| `app/application/market` | `MarketSnapshotArchive` — what the market read before |
| `app/application/change_feed` | `ChangeFeedService`, `MarketChangeService` — what changed |
| `app/application/thesis` | `InvestmentThesisBuilder` |
| `app/application/brief` | `ExecutiveBriefBuilder` — the Communication layer |
| `app/application/workspace` | Pipeline orchestration |
| `app/renderers` | Presentation models and console output |
| `app/api`, `app/commands` | Delivery |
| `app/domain` | Shared domain models |
| `app/providers` | Provider access, cached: `CachedValueProvider`, `CachedMarketProvider` |
| `app/providers/primary_source_provider.py` | The acquisition seam: `PrimarySourceResolver`, EDGAR first, ESEF second |
| `app/providers/edgar_provider.py`, `edgar_filings.py` | SEC filings — the regulator's own record |
| `app/providers/esef_provider.py`, `esef_filings.py` | European filings, read from the filer's IFRS tagging |
| `app/providers/issuer_identity.py`, `european_issuers.py` | Which company a European ticker means, before anything is read for it |
| `app/providers/investor_relations_provider.py`, `investor_relations_sources.py` | The company's own published report, from a reviewed location and a reviewed hash |
| `app/providers/document_text.py` | One reduction of a filing's markup, shared by every provider: the words as they were always read, plus the tables as a grid |
| `app/domain/evidence.py` | What every citation is held to: existence, applicability, and the comparison rule both use |
| `app/domain/tabular_evidence.py` | Applicability for a quantity: a number's address in a table, the cell read back out of the document, and the share computed from two checked figures |
| `app/domain/prose_evidence.py` | Applicability for a description: the document's own naming of its segments as a partition of the prose, and the span's position within it |
| `app/services/narrative_providers.py` | Building a model client, once, for both seams that use one |
| `app/services/company_knowledge_reader.py` | Which model reads a filing — configured apart from the one that words a case |
| `app/domain/company_archetype.py` | What kind of business a company is: the conclusion, every rule that reached it, and what was not established |
| `app/services/archetype_engine.py` | The rules themselves — a pure function over `CompanyKnowledge`, no model, no industry |
| `app/providers/section_locator.py` | Where a filing's numbered **items** are: candidates discovered typography-blind, scored on named structural evidence, resolved as the most coherent progression of items |
| `app/providers/statement_locator.py` | Where its audited **statements** are, by the same architecture pointed at a second vocabulary: a statement is selected because it belongs to the highest-quality structural run, never because its title matched first |
| `app/domain/financial_statements.py` | One reading of one primary statement: the statement vocabulary, the concepts, and the row labels each concept accepts |
| `app/domain/financial_statement_consensus.py` | What repeated readings of one statement agree the filer printed — the consensus architecture pointed at a second claim set |
| `app/services/financial_statement_extractor.py`, `financial_statement_service.py` | Reading one named statement of one document, and the counted spend that fills its quorum |
| `app/domain/financial_understanding.py` | What the statements **measure** — the layer `BusinessUnderstanding` occupies over narrative consensus. Facts and arithmetic; it never scores |
| `app/services/financial_engine.py` | The arithmetic itself: recipes over checked cells, deterministic, no model |
| `app/domain/financial_question.py` | Which financial questions are meaningful, who owns them, and `FinancialModel` — the second classification, kept apart from `PlaybookKind` |
| `app/services/financial_questions.py` | Executing a question a model chose against facts it did not read: answered, an evidence gap, or an explicit refusal |
| `app/analysts/filing_analysts.py` | The filing-grade analyst route, reading established facts and never a provider's. Legacy plumbing since the questions layer; retained until a second financial model exists |
| `app/infrastructure/cache` | `JsonCache` — what a provider already told us |
| `app/infrastructure/evidence` | `VersionedSnapshotStore` — every capture kept, and readable back |
| `app/services/*_signal_service.py` | Value, quality, momentum and risk signals per security |

## Perception components

| Component | Produces |
|---|---|
| `PortfolioPerception` | `PortfolioSnapshot`, including per-holding detail |
| `MarketPerception` | `MarketSnapshot`, and the record of it |
| `PolicyPerception` | `InvestmentPolicy` |
| `SecurityPerception` | Per-security evidence, keyed by symbol |
| `InvestorPerception` | `Observation`, `InvestorDNA` |
| `RecommendationPerception` | `Recommendation` |
| `OpportunityPerception` | `ResearchCandidate` — watched, not held |
| `MemoryPerception` | `DecisionHistory`, keyed by symbol |

## Analysts

`PortfolioAnalyst`, `MarketAnalyst`, `RiskAnalyst` and `BehaviorAnalyst`
assess the Brain. `OpportunityAnalyst` then synthesises their output, so it
runs last. All five results travel together in `ReasoningSnapshot`.

---

# Transitional

| Package | Note |
|---|---|
| `app/services` | ~69 modules. Mixed: some feed perception and are load-bearing, others are only reachable from a single CLI command. Migrate case by case, not wholesale. |
| `app/committee` (singular) | Live: backs `movrvest committee` via `app/commands/committee.py`. Not part of the Artificial CIO path. |
| `app/analysts` (top level) | Per-security fundamental analysis, reached only through `app/services/company_*`. Real logic; not yet part of the canonical reasoning layer. |
| `app/domain/brain_context.py` | The legacy `BrainContext`. Analysts still accept `Brain | BrainContext`; retire once those unions are narrowed. |

---

# Removed

Deleted after verifying no remaining references. Recorded so nobody
reintroduces them.

| Removed | Superseded by |
|---|---|
| `app/application/brain/brain_pipeline.py` and its stages | `BrainBuilderService` + `ExecutivePipeline` |
| `InvestmentBrain`, `BrainService` | `BrainSnapshotService` |
| `BrainContextBuilder` | Perception components directly |
| `ExecutiveReasoningService` | `ReasoningService` |
| `ExecutiveSummaryService` | `ExecutiveBriefBuilder` |
| `app/committees` (plural) | `app/committee` |
| `app/services/committees`, `ExecutiveCommitteeService` | `app/application/committees` |
| `app/services/executive` | `app/application/executive` |
| `app/services/reasoners` | `app/application/brain/reasoning` |
| `app/reasoning` | `app/cio` (the shim only re-exported it) |
| `ExecutiveCommittee`, `ExecutiveRecommendation`, `ExecutiveBriefService` | `DecisionEvidenceBuilder` → `ArtificialCIO` |
| `app/agents`, `app/strategy`, `app/models.py`, `app/risk.py`, `app/audit.py` | Nothing — orphaned |
| `app/page.tsx` | `apps/web/movrvest-web` |
| Python reasoning inside `apps/web/movrvest-web` | `app/application/brain/reasoning` |
| `OpportunityService`, `OpportunityDiscoveryService`, `GET /opportunities/` | `CandidateResearchService`, `GET /research/candidates` |
| `components/dashboard/*` (18 cards) and their 10 one-consumer API clients | `components/executive/*`, `components/decisions/DecisionCard`, typed `lib/api/*` clients |
| `lib/acio/*`, `lib/investor/*` (frontend reasoning engine, mock-fed) | `app/application/brain/reasoning` — the backend owns investment meaning |
| `/briefs/[symbol]` (hardcoded MSFT mock) and `components/brief/*` | `/dossiers/[symbol]` ← `GET /executive/{symbol}/dossier` |
| Frontend banding (`riskLevel`, `diversification`, liquidity recompute, conviction thresholds) | Backend-worded labels (`app/renderers/brief_language.py`) and measured fields |
| `/events/[slug]` placeholder | Nothing — removed until an event concept is evidenced |

---

# Dependency Rule

```
Reality → Evidence → Brain → Reasoning → Committees → CIO → Communication → Delivery
```

Dependencies flow one way. Two rules earn their keep:

- `app/application/executive/__init__.py` deliberately does **not** re-export
  `ExecutiveService`. It depends on `app/application/workspace`, which imports
  back into `executive`; eagerly exporting it made imports order-dependent.
- Analysts never fetch data. Perception never reasons. Communication never
  decides.

---

# Verification

Because the import graph is the source of truth, check it directly:

```bash
# Does anything actually use this?
grep -rln "app.services.committees" app --include="*.py" | grep -v __pycache__

# Is HEAD self-contained? (pre-commit does not stash untracked files, so
# hooks can pass on a tree the commit does not contain)
git archive HEAD | tar -x -C /tmp/headcheck && cd /tmp/headcheck \
  && python -m mypy app && python -m pytest -q
```

---

# Guiding Principles

1. One business concept = one implementation.
2. Verify the import graph before calling anything canonical.
3. Delete only after the replacement is live and callers are gone.
4. Backend owns financial calculation; the frontend renders.
5. Absent evidence is reported as absent, never estimated.
6. Leave the repository cleaner than you found it.
