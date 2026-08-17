# A reading records the contract that produced it, not the one reading it

**Status: built, BQ17. Every newly acquired statement observation carries
the vocabulary contract its concepts were read under. No model call, no
credit, nothing re-observed, no backfill. Production `data/statements`
byte-identical — verified by decoding and re-encoding all 24 entries.**

BQ16 established the rule and paid the price of not having this: *same
schema is not same producing contract*, and the only way to rule on the
historical corpus was an operator's authored testimony, reasoned from
git archaeology, because the records carried no trace of which labels
their reader had been permitted to accept. BQ17 makes the trace native.

> **229 bytes per observation.** Six fingerprints on an income-statement
> reading — the identity of each concept's vocabulary, never the
> vocabulary itself.
>
> **Stamped once, at acquisition, and never recomputed.** The generator
> is reachable from the extractor and from nowhere else, pinned by a
> test that walks `app/` for its call sites.
>
> **Zero production bytes changed and zero records backfilled.** The
> field is written only where a reading carried it, so all 24 existing
> entries re-encode identically and every one still reports *not
> recorded*.

---

## 1. The identity — BQ16's, unchanged

The producing contract is the **per-concept vocabulary fingerprint**
BQ16 proved useful: `concept_vocabulary_fingerprint`, sha256 over the
concept and its normalised, sorted accepted forms, owned by the module
that owns `CONCEPT_LABELS`. **No second algorithm was invented** — BQ17
imports the same function BQ16's manifests were computed with, which is
what lets a native stamp and a manifest entry be compared on equal
terms.

Per concept, not per vocabulary, and this slice is where that pays: §5's
fourth case only passes because a change to one concept's forms leaves
every other concept's fingerprint untouched.

## 2. The persisted shape

`producing_contract(statement)` returns one `ConceptContract` per
concept the statement asks; the observation carries them as
`produced_under`, and the store writes them as a flat object:

```json
"produced_under": {
  "gross_profit":        "36b11e47cf234c1f",
  "net_income":          "c5983f89b332a0c7",
  "net_interest_income": "8c3e67f9872329b5",
  "operating_income":    "668db132db8b57bd",
  "premium_revenue":     "87e065f39c345a37",
  "total_revenue":       "3cdbddd6a1fcf0e6"
}
```

It answers the three questions the brief names, with no git archaeology:
**which concept** (the key), **under which vocabulary** (the
fingerprint), **belonging to which assertion** (it sits inside the
observation, so it travels with the bytes it describes — through
`append`, through promotion, through equality).

Smallest, deliberately. Only the concepts *this statement* is asked, so
a balance-sheet reading carries four and not twelve; fingerprints and
never the forms, so `CONCEPT_LABELS` is not copied into every
observation of every company; and a flat object rather than a nested
record, because the question it answers is only whether two contracts
are the same one.

**Decoded in the vocabulary's own order**, not the JSON object's —
`sort_keys` alphabetises, and a decode that depended on key order would
make a promoted observation unequal to the one it was copied from. That
was caught by the round-trip equality test, not by inspection.

## 3. Why it cannot drift to current-reader state

Three mechanisms, and the third is the one that makes it structural:

- **Written only at acquisition.** `producing_contract` reads the live
  `CONCEPT_LABELS`, which is correct exactly once — at the instant of
  reading — and wrong everywhere else. Both extractor construction sites
  stamp it: the model-read observation, and the structurally-unlocated
  one. The second matters more, because every fact in it is an absence,
  and an absence is the one claim a later reader cannot check against
  the document.
- **Read back verbatim.** `_observation` decodes what was written and
  never computes. An entry without the key stays without it: *not
  recorded*, never *matched today's* — the `located_among` precedent,
  which records 0 rather than inventing a count.
- **Pinned structurally.** `test_only_acquisition_generates_a_producing_contract`
  walks every file under `app/` for `producing_contract(` and asserts
  the call sites are exactly two: the module defining it, and the
  extractor. `test_the_store_never_computes_a_fingerprint` asserts the
  store's source names no fingerprint function at all. A future
  consensus or store that started stamping records would fail here
  before it ran.

## 4. Compatibility — native and historical

`statement_promotion` now resolves an absence's producing vocabulary
from two sources, **in this order**:

1. the observation's **own stamp** (`produced_contract_for`);
2. the **manifest** entry for its artifact (BQ16's bridge, unchanged and
   deliberately not removed).

The record is consulted first, so testimony can never overrule an
observation that answers for itself — pinned by a test where the
manifest claims today's contract and the reading says otherwise: the
reading wins and is refused.

| Record | Absence resolves from | Ruling |
|---|---|---|
| stamped, fingerprint equals today's | itself | **compatible** — no manifest needed |
| stamped, fingerprint differs | itself | **incompatible**, worded *"the reading records no figure for X under a vocabulary that differs from today's"* |
| unstamped, manifest rules it | the manifest | BQ16's behaviour exactly, worded *"the manifest records…"* |
| unstamped, no manifest | nothing | **compatibility unproven → refused** |

Located anchors keep their independent check — a label today's
vocabulary refuses is incompatible from the record alone, no testimony
involved either way.

One deliberate strictness: **an observation with no account at all is
UNPROVEN even if every fact it holds is located.** A reading that
happens to locate everything is still a reading nothing vouches for, and
BQ16's rule stands — deserialization is admission to inspection, never
to a consensus.

## 5. The A → B mutation test

`test_a_stored_stamp_is_never_rewritten_by_a_later_vocabulary` and its
two siblings prove all four properties, with the vocabulary genuinely
mutated mid-test in the shape `6c96ea0` had (one more accepted form for
one concept):

| # | Property | How it is proved |
|---|---|---|
| 1 | the stored observation still says **A** | `produced_contract_for(net_income) == A` and `!= B` after the widening |
| 2 | rereading does not mutate it | the **bytes on disk** still hold A, and a second `read()` returns an object equal to the first |
| 3 | compatibility sees **A versus B**, not one schema | the same artifact rules `compatible` before the widening and `incompatible` after — schema 3 on both sides throughout, and `apply()` appends 0 |
| 4 | an unchanged concept is not falsely incompatible | widening `gross_profit` *and* `total_current_assets` leaves the reading **compatible**, and it appends |

Case 4 is the design justification: under a single global extraction
fingerprint every one of those readings would have gone incompatible for
a change that touched nothing they claim.

## 6. No retrospective fabrication

Nothing was backfilled. Measured over the live corpus: **24 files
checked, 0 whose bytes would change on re-encode, 0 existing
observations carrying a stamp.** `git status --porcelain data/` is
empty.

The three BQ16 manifests stay exactly as they were, and they remain the
only legitimate account of the pre-BQ17 material — including the
experiments whose producing contract *is* independently pinned, because
a deterministic derivation from repository history is still testimony
about the record rather than something the record says. Native
provenance begins with observations produced after this slice; a
reading appended beside an unstamped one leaves it unstamped, which has
its own test.

## 7. Purity

No model call, no funded observation, no re-observation, and no
financial value moved: the field is additive, written only when present,
and the only behavioural change outside acquisition is that a *stamped*
record no longer needs a manifest.

**Gates**: ruff clean · mypy clean over 591 files · **2,792 tests pass,
0 failures** (the three network-dependent crypto files reached their
endpoint on this run; they remain the known flake and the next slice's
subject).

## 8. Recorded, not solved

- **The crypto-dossier CI fix** stays the identified next item and is
  deliberately not bundled here: `crypto_dossier.py:153` constructs a
  raw fetching `IssuanceRuleProvider()` under a route documented as
  acquiring nothing.
- **The manifest mechanism is not retired**, and should not be until the
  pre-BQ17 artifacts are either promoted or retired themselves.
- **`ConceptContract` covers vocabulary only.** The parse contract is
  still checked against the document by `statement-audit`, and the
  *asked* contract is still the schema version. Three axes, three
  mechanisms, each where it can be proven — no attempt is made here to
  unify them.

## Scope compliance

`STATEMENT_SCHEMA_VERSION` unchanged at 3 · `CONCEPT_LABELS` unchanged ·
no new financial concept · quality thresholds, questions and
completeness untouched · nothing promoted · nothing re-observed · no
model call, no credit · no backfill of any historical record · crypto
untouched (its known CI issue recorded, not fixed) · no UI · PR #145
untouched · production `data/statements` byte-identical.
