# Closing the evidence-root class

**Status: built. Four repositories repaired, one exemption documented,
one shared invariant added. No LLM call, no credit. Production evidence
byte-identical; 0 analytical changes. Stopped for ruling.**

#118 made the evidence root a declared input and converted the provider
caches. Every **repository** kept a string literal. BQ9 found the first
one the hard way — the statement store was reading the developer's own
corpus inside tests that believed they were hermetic. BQ10 closes the
class.

---

## 1. The audit

Every `data/…` default in `app/`, traced rather than assumed:

| Module | Default | Evaluated | Root honoured? | Explicit path | Verdict |
|---|---|---|---|---|---|
| `company_knowledge_store` | `"data/knowledge"` | construction (`Path(directory)`) | **no** | authoritative | **defect** |
| `investment_decision_store` | `"data/decisions"` | construction | **no** | authoritative | **defect** |
| `json_event_repository` | `"data/events"` | construction | **no** | authoritative | **defect** |
| `json_snapshot_repository` | `Path("data/portfolio_snapshots")` | **import** | **no** | authoritative | **defect ×2** — see §3 |
| `investor_strategy_service` | `"data/investor_strategy.json"` | construction | no | authoritative | **intentional — not evidence** |

None of the three named stores was assumed defective: each was traced,
and each turned out to resolve its literal at construction (so no
import-time freeze) while ignoring `MOVRVEST_EVIDENCE_ROOT` entirely.
The snapshot repository carried both faults.

**The exemption, with its reason.** `data/investor_strategy.json` is
the investor's own declared strategy — one tracked configuration file
read by a service, not a stream of observations kept by a repository.
Redirecting it with the evidence root would make a test's
*configuration* depend on where its *evidence* lives, which is the
coupling this abstraction exists to remove rather than to spread. It is
recorded in `OUTSIDE_THE_ROOT` and a test asserts the exemption still
names a file that exists.

## 2. Ambient-production dependencies exposed

**None.** The full suite passed unchanged after all four repairs
(2,682 → 2,709 with the new tests).

This is worth stating plainly because it differs from BQ9: repairing
the *statement* store broke three tests immediately, because
`test_score_derivation` read the statement corpus with no declaration.
Nothing was leaning on knowledge, decisions, events or snapshots the
same way. **The defect was uniform; the exposure was not** — which is
exactly why the invariant belongs in a test rather than in a habit.

## 3. The repairs

All four follow BQ9's pattern exactly — `None` in the signature, the
root resolved **at construction**, explicit paths untouched:

```python
self.directory = (
    Path(directory) if directory is not None else evidence_path("knowledge")
)
```

**The snapshot repository needed a second, separate repair.** It called
`mkdir(parents=True)` in `__init__`, so *constructing* it wrote a
directory — and under an unset root that directory was
`data/portfolio_snapshots` in the developer's tree. My own invariant
test created it on the first run, which is the defect demonstrating
itself. The `mkdir` now happens in `save()`, as it already does in
every other store: **a repository creates its directory when something
is written, never merely by existing.** That is the half of #118 that
was about writing rather than reading.

## 4. The shared invariant

`tests/test_evidence_root_invariant.py`, parametrised over all five
participating repositories (statements, knowledge, decisions, events,
snapshots) — 27 tests:

- the default hangs from the configured root;
- nothing is read or written outside it;
- an explicit path stays authoritative;
- **the root is re-read between constructions** — the failure a
  signature default produces, where `evidence_path(...)` evaluated at
  import binds whatever root existed then;
- production is still what an unset root means.

Plus the closure: a **source sweep** over every module in `app`, so a
repository added later either hangs from the root or is named in
`OUTSIDE_THE_ROOT` with a reason. A remembered list would have to be
remembered; this fails by construction.

## 5. Production invariance

| Check | Result |
|---|---|
| `git status --porcelain data/` | **empty** |
| `data/knowledge` | 33 files, 0 modified |
| `data/statements` | 24 files, 0 modified |
| `data/decisions` | 1 file, 0 modified |
| `data/events` | 22 files, 0 modified |
| stray directories created | **none** |
| Business Quality across 24 | **0 differences** |

Nothing was migrated, rewritten or moved. With `MOVRVEST_EVIDENCE_ROOT`
unset, every default resolves exactly where it resolved before.

## 6. HON stays parked — BQ9's falsification, recorded

- HON's header cells are at columns **0 / 6 / 12**; its figures at
  **3 / 9 / 15**.
- **Forward-fill is not authoritative**: a pre-existing adversarial
  case (written in BQ7, before the rule existed) shows headers at 3 and
  5 with figures at 3, 4, 5 labelling the column-4 figure `2025` when
  it is 2024.
- A blank header cell **cannot distinguish** a colspan continuation
  from a genuinely missing header.
- The safe repair is **preserving source `colspan`** (or equivalent
  structural provenance) at parse time, so a figure sits inside a
  *declared* span rather than after a blank.

Not implemented here. HON was not re-observed. The statement parser is
byte-identical to `main`.

## 7. Readiness for the next funded experiment

**Ready, and better than before.** The isolation defect that forced
BQ8's experiment to use a hand-built harness is gone: a funded run can
now redirect `MOVRVEST_EVIDENCE_ROOT` and be certain no observation
lands in the production corpus and no ambient evidence leaks in.

The recommended target is unchanged from BQ8 and BQ9: **the seven
recoverable comparative instances** (TSLA, ALL, WMT, MTB, RF), where
the mechanism is proven twice and the only open question is whether a
full quorum re-read moves the bands. **HON is still excluded** — the
parser cannot read its table shape, so re-observing it would spend
credits to reproduce the same correct refusal.

## Scope compliance

Statement parsing unchanged · financial concepts unchanged ·
`CONCEPT_LABELS` untouched · Business Quality untouched · nothing
re-observed · no LLM call, no credit · comparative cohort not
refreshed · no crypto analytical logic, no UI, no PR #145 · no evidence
migrated or rewritten.
