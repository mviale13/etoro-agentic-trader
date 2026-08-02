# MOVRvest Migration Plan

> Living roadmap for converging the repository toward the canonical
> architecture.

Status: Active

---

# Mission

Every sprint must make the repository:

- Simpler
- More consistent
- More explainable
- Easier to extend

Rule:

> Migrate before deleting.
> Delete only after verification.

---

# Migration Principles

## 1. One Concept = One Owner

Every business concept has exactly one canonical implementation. If
duplicates exist: choose the canonical one, migrate callers, remove the rest.

## 2. Verify Before Believing

A package is canonical when the import graph says so, not when a document
does. Check with `grep -rln` from a real entry point before building on
something — and before deleting it.

## 3. Preserve Behaviour

Migrations improve structure, not functionality. Where behaviour must change,
say so explicitly.

## 4. Keep Quality Green

Ruff, mypy and pytest stay green after every migration. Verify the commit,
not just the working tree: pre-commit stashes unstaged changes but leaves
untracked files in place, so hooks can pass on a tree the commit does not
contain.

## 5. Never Estimate What You Cannot Measure

A plausible number on an investment dashboard reads as a measurement. Where
evidence is missing, report it as missing.

---

# Completed

## The canonical pipeline is live

Brain → Reasoning → Committees → Artificial CIO → Communication → Dashboard
now runs end to end, from `movrvest evaluate` and from `GET /executive/...`.

- Communication wired in: `ExecutiveBriefBuilder` populates
  `ExecutiveWorkspace.brief`, replacing a hardcoded "No urgent decision
  today" that no computation could change
- `BrainBuilderService` completed and reachable from a live entry point
- The dashboard consumes real data: the field-name mismatch that silently
  substituted demo values is fixed, and the last mock is gone
- Holdings are perceived per security: the broker reports each position, the
  watchlists name it, and per-security signals reach the Brain as evidence
- The Artificial CIO judges each holding on that evidence, so decisions
  differ per symbol rather than repeating one portfolio-level verdict
- `ReasoningSnapshot` carries all five assessments; `policy_alignment_score`
  is measured against the Investment Policy rather than hardcoded
- The legacy `BrainPipeline` chain and 45 superseded files are deleted

## The Artificial CIO has memory

Each decision is recorded once per symbol, per day, per state, and the next
cycle perceives it:

```
ArtificialCIO → ExecutiveDecision → DecisionJournal → EventRepository
                                          ↓
                        MemoryPerception → Brain.decision_history
                                          ↓
                        InvestmentThesis.previous_decisions → CLI · API · web
```

- `MemoryPerception` was an empty class; it now reads the journal
- A symbol the CIO has never judged reports an empty history, and the
  investment case says nothing rather than "no change"
- The pipeline only writes when a journal is injected, so a test or a
  what-if evaluation never enters the record
- `ChangeFeedService` returned three hardcoded examples ("NVIDIA upgraded")
  and was imported by nothing. It now reads the journal, reports each
  recorded state change newest first, and reaches the dashboard through
  `GET /executive/portfolio`. Severity is the distance the decision moved
  along the lifecycle, so it is measured rather than asserted
- The Python reasoning stranded inside `apps/web/movrvest-web` is deleted,
  along with two uncommitted migration shims

## Deleted

See the Removed table in `REPOSITORY_INVENTORY.md`.

---

# Open Work

## Evidence quality

- [ ] Yahoo fundamentals are rate-limited and uncached; signals can flip
      between runs, which can flip a decision
- [ ] Crypto tickers do not resolve (`SOL` needs `SOL-USD`)
- [ ] Holdings absent from every watchlist cannot be named or analysed
- [ ] Holdings are not classified by asset type, which blocks allocation
      drift scoring and the crypto policy limit

## Reasoning

- [ ] `consistency_score` needs a record of the investor's own actions. The
      decision journal records the CIO's decisions, not what the investor did
      with them
- [ ] No decision is scored against its outcome; the journal is a record, not
      a track record
- [ ] `app/analysts` holds real per-security fundamental analysis that the
      canonical reasoning layer does not yet own

## Delivery

- [ ] API routes construct services directly, so they cannot be tested
      without network access
- [ ] The change feed covers recorded decision changes only. Market and macro
      movements are not recorded anywhere, so they are absent from it
- [ ] `ExecutivePipeline` recomputes symbol-independent reasoning per holding

## Structure

- [ ] `app/services` (~69 modules) still mixes load-bearing and incidental
      code
- [ ] Analysts accept `Brain | BrainContext`; narrowing them retires the
      legacy `BrainContext`
- [ ] `ClaimEngine.test.ts` has pre-existing TypeScript errors (`vitest` is
      not installed); excluded from the Next build graph, so it does not
      break the gate
- [ ] `docs/` holds ~20 documents, several superseded and a few iCloud
      conflict copies. Consolidate or mark them, as was done for
      architecture v4.0

---

# Success Metrics

## Architecture

- One implementation per concept
- No duplicate pipelines
- One-way dependency graph

## Product

Every executive recommendation can answer:

- What changed?
- Why?
- Why now?
- What should I do?
- Why should I trust this?

---

# North Star

```
Reality
    ↓
Evidence
    ↓
Brain
    ↓
Analysts → ReasoningSnapshot
    ↓
Executive Committee → CommitteeOpinion
    ↓
DecisionEvidence
    ↓
ArtificialCIO → ExecutiveDecision
    ↓
InvestmentThesis
    ↓
ExecutiveBrief
    ↓
Executive Workspace
```

No parallel paths. No duplicate ownership. No ambiguity.

End of document.
