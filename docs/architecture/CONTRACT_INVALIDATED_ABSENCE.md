# An absence stops voting only where a contract, not a clock, explains it

**Status: built, BQ20. No model call, no acquisition, no production
write. `data/` byte-identical. Stopped for ruling.**

Two companies reached the same deadlock independently, which is what
made it a condition rather than an incident.

> **UNP resolves and KO does not, under one rule that names neither.**
> Union Pacific's five stale absences lose their vote and it reaches
> **MEDIUM 62**; Coca-Cola's do not, and it stays **UNKNOWN** — because
> KO's *positive* readings predate native stamping too, so the very
> contract that could have produced its absences is one that accepts
> `Net Operating Revenues`. Nothing about the vocabulary explains KO's
> absence, so nothing withdraws it.
>
> **A fingerprint difference proves nothing on its own**, and that is
> the control this slice exists to pass. The rule reads the *forms* a
> contract had, not whether two hashes differ.

---

## 1. The mechanism causing the deadlock

`_fact_consensus` counts one comparable answer per observation that
addressed the concept; an absence contributes `NO_FIGURE`.
`agreement(...)` requires a strict majority, so five absences against
five located figures is 5 of 10 — `by_majority` is `False`, the claim is
unsettled, and every margin loses its denominator.

Reproduced before anything changed, with the provenance of each side:

| | absences | positives | stamped? | outcome |
|---|---|---|---|---|
| **UNP** | 5 × *no figure located* | 5 × `Total operating revenues` 24,510 | absences **unstamped**, positives **`ea9df9c5adbc7f44`** | `by_majority=False` |
| **KO** | 5 × *no figure located* | 5 × `Net Operating Revenues` 47,941 | **all ten unstamped** | `by_majority=False` |

The asymmetry in that last column is the whole of §8's answer.

## 2. The rule

> **An absence loses its vote for one concept where the contract that
> produced it provably could not have accepted the label a later
> reading located for that concept.**

Everything else keeps voting, and the three exclusions are the rule's
real content:

- **two positives that disagree remain a disagreement.** A difference in
  producing contract is not a reason to prefer either, and Case A is
  never touched.
- **an absence whose contract *could* have accepted the label** is a
  reader difference, not a contract difference — exactly what the quorum
  exists to measure.
- **an absence whose producing contract cannot be bounded** proves
  nothing and keeps its vote.

Nothing in `absence_supersession.py` reads a date, a store position, a
band or a company. It is not *newer wins* and a test pins that it cannot
become it.

## 3. How causality is established

A fingerprint is one-way: it proves two contracts *differ* and can never
prove a label was *outside* one of them. So BQ17's stamp answers only
half, and `app/domain/vocabulary_contracts.py` answers the other —
**every published `TOTAL_REVENUE` vocabulary of the schema-3 era, with
its accepted forms verbatim**, reconstructed from the repository and
fingerprinted with the live function:

| Fingerprint | Forms | Introduced by | Stamps its readings |
|---|---|---|---|
| `ba55a427097938f3` | 12 | `301cfdf` — schema 3 begins | no |
| `3cdbddd6a1fcf0e6` | 13 | `6c96ea0` — BQ11 earns `net operating revenues` | no |
| `ea9df9c5adbc7f44` | 14 | `c49955b` — BQ19 earns `total operating revenues` | **yes** |

The lineage is complete for the era and totally ordered: `git log -S`
over `CONCEPT_LABELS` since `301cfdf` returns exactly those two
widenings. `registry_is_current` refuses to reason at all if the live
vocabulary ever moves ahead of the registry, so a stale lineage cannot
silently shorten a bound.

The chain, per absence:

1. **which concept** — the fact that recorded the absence;
2. **which contract produced it** — its `produced_under` stamp, or, where
   it carries none, the bound below;
3. **which label a later reading located** — from the positive facts in
   the same set;
4. **the form delta** — whether *every* contract the absence could have
   come from lacks that form.

**The bound for an unstamped reading** is a logical entailment, not an
assumption: a reading that carries no stamp cannot have been produced by
a contract that stamps, and every stored reading is of the current
schema because the store refuses any other. So its candidates are the
era's non-stamping vocabularies — and the absence is withdrawn only
where **all** of them lack the form.

That is why silence bounds without licensing: the same unstamped UNP
absence is **withdrawn** against `Total operating revenues` and **stands**
against `Total revenues`, which every contract in the era accepts.

*(A note on the brief's control 5. Read literally — "missing/unknown
producing provenance → remains active" — an unstamped absence would
never be withdrawn, and neither UNP nor KO could move. The rule
implemented distinguishes **missing** from **unbounded**: missing is
bounded by entailment and still requires every candidate to lack the
form; unbounded — a stamp naming no published vocabulary, or a concept
with no recorded lineage — proves nothing and keeps its vote. Both
behaviours are pinned. The deviation is deliberate and is flagged here
rather than buried.)*

## 4. The unit

**One concept of one observation.** A reading whose `total_revenue`
absence is withdrawn keeps its `net_income`, its dates, its rows and
every other fact, and continues to vote on all of them — pinned by a
test where the withdrawn readings still carry net income at 5 of 5.

Concept-locality also falls out of the registry: a concept with no
published lineage cannot be ruled at all, so widening one vocabulary can
never disturb another's absences.

## 5. The controls

| # | Control | Result |
|---|---|---|
| 1 | UNP shape: absence A, positive B, B's form new | **superseded**, and the live specimen resolves |
| 2 | KO, same generic rule | **not superseded** — and correctly, see §7 |
| 3 | positive A vs different positive B | both vote; a 5–5 split of positives settles nothing |
| 4 | absence + positive, vocabulary unchanged | **active** |
| 5 | absence stamped with an unpublished fingerprint | **unprovable → active** |
| 5b | unstamped absence, bounded | withdrawn against a new form, **active** against an old one |
| 6 | another concept's vocabulary moved | **no effect**; `net_income` has no lineage, so nothing is ruled |
| 7 | **fingerprints differ, but the located label was already accepted** | **active** — a difference alone is never evidence |
| — | concept-locality | withdrawn revenue absence; net income still 5 of 5 |
| — | immutability | the observation is byte-identical after the derivation |

Eleven tests, all passing.

## 6. UNP, before → after

| | readings | withdrawn | `total_revenue` | answered | band |
|---|---|---|---|---|---|
| stale only | 5 | 0 | unsettled — 5× *no figure* | 1 of 3 | UNKNOWN |
| **mixed (5 + 5)** | 10 | **5** | **settled** — `Total operating revenues` 24,510 | **3 of 3** | **MEDIUM 62** |
| fresh only | 5 | 0 | settled | 3 of 3 | MEDIUM 62 |

**Mixed now equals fresh-only**, which is the acceptance observation
rather than the rule: MEDIUM 62 is nowhere in the code, and the same
mechanism would have produced LOW or HIGH had the figures differed.

## 7. KO, before → after

**Unchanged: UNKNOWN, 0 withdrawn, `by_majority=False`.**

And the reason is structural rather than incidental. KO's five positive
readings were promoted in BQ16 but were *taken* before BQ17, so they
carry no stamp either. Both sides therefore fall in the same bound —
`{ba55a427, 3cdbddd6}` — and `3cdbddd6` is the contract BQ11 created
precisely by adding `net operating revenues`. An absence that could have
been produced by a contract which would have found the label is not
explained by the vocabulary, and the rule declines to withdraw it.

This is the different causal structure §8 anticipated. KO's tie is not a
contract-invalidated absence; it is an unresolved question about
readings taken under a contract that could have answered it. **The
mechanism was not tuned to move KO, and it did not move KO.**

## 8. Aggregate

| | HIGH | MEDIUM | LOW | UNKNOWN |
|---|---|---|---|---|
| production today, rule live, nothing appended | 4 | 4 | 3 | **13** |
| if UNP's five preserved readings were appended | 4 | **5** | 3 | **12** |

**One company moves, and only UNP.** The rule changes nothing on its own
because no production entry yet holds both sides of a widened
vocabulary; it changes UNP the moment its five preserved native readings
are appended.

## 9. History is untouched

- `git status --porcelain data/` **empty**;
- the rule is **derived on read** and writes nothing — no
  `superseded_because` is set, no fact is rewritten, no provenance is
  altered, nothing is deleted;
- a test asserts a withdrawn observation is byte-identical afterwards and
  still reports its absence, its `produced_under`, and no supersession
  reason.

The journal keeps telling the historical truth: *under contract A this
producer established nothing.* What changed is only whether that
sentence is allowed to settle today's claim.

`ConsensusFact.withdrawn_absences` reports the count beside the
agreement, so a claim settled 5 of 5 with five withdrawn never looks
like one settled 5 of 5 outright.

## 10. Gates

**2,805 pass** · ruff check clean · ruff format clean (996 files) ·
mypy clean, 593 files.

## 11. Recommended production action — not executed

**Append UNP's five preserved native observations**, through the
ordinary importer, which already rules them compatible with no manifest:

```bash
movrvest statement-import data/experiments/statement-observations/bq19/statements --apply
```

Expected, measured on a copy: 5 appended, UNP **UNKNOWN → MEDIUM 62**,
aggregate **HIGH 4 · MEDIUM 5 · LOW 3 · UNKNOWN 12**, no other company
moved.

**Not recommended in this slice**: anything for KO. Its tie needs a
different question answered — whether readings taken under a contract
that *could* have found a label, and did not, should be re-read rather
than re-ruled — and that is not a supersession question.

## Recorded, not solved

- **The registry covers `TOTAL_REVENUE` only**, because it is the only
  concept whose vocabulary has moved in the schema-3 era. Any future
  widening must extend it in the same commit, and `registry_is_current`
  fails loudly if it does not.
- **KO's tie is now the last of its kind measured**, and it is a
  re-reading question rather than a contract question.
- The four other vocabulary-blocked companies (AXP, C, BCS, NWG) are
  untouched: their forms were rejected in BQ19 and nothing here revisits
  that.

## Scope compliance

No vocabulary widened · Goldman's `Total net revenues` inconsistency not
investigated · HON untouched · the six no-top-line companies untouched ·
majority thresholds unchanged · **no recency weighting anywhere** · no
model or API call · AXP, C, BCS, NWG not acquired · no production
evidence appended or modified.
