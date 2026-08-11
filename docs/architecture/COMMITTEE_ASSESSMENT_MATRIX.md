# The Committee Assessment Matrix

**Status: accepted, built, decision-neutral.** A projection of
independent judgments, and **not a new judge**.

It answers one question — *what have the registered committees concluded
about this asset?* — by placing each committee's own answer beside the
others without combining, comparing or interpreting any of them.

---

## 1. The measurement that determined the type

The cell was not designed. The live two-committee records were read
field by field first, and the shape follows from what was found.

**Fields both implementations always produce** — asset, committee
identity, `judged_at`, applicability, state, evidence digest and count.
Eight of eight records, both committees.

**Fields present only in one outcome shape** — verdict, its sentence,
confidence and refs appear exactly when answered (5/8 for Fee Capture,
3/8 for Supply Governance); the abstention reason and the committee's
own sentence appear exactly when not.

**Fields that only look common:**

- `evidence_count` — Fee Capture's 11 for HYPE counts fee readings,
  holder-revenue readings, an arithmetic share and temporal
  projections. Supply Governance's 11 for ADA counts rule parameters
  and projections. Same name, same type, **and a sum of the two is a
  number about neither**.
- `judged_at` — see the defect below.
- `model` — Fee Capture always; Supply Governance never, because it has
  no model seam.

**Fields that are demonstrably not comparable** — `confidence`. Supply
Governance saturates: 8, 9 and 11 findings all read
`MULTIPLE_OBSERVATIONS`. The vocabulary is calibrated to Fee Capture's
evidence shape, and two committees are not enough evidence to design its
replacement. So the matrix **carries confidence and never compares it**.

**Can the existing vocabulary represent the matrix losslessly?**
Yes — `JudgmentState` (3) × `Applicability` (3) × `AbstentionReason` (3)
× the verdict token and its sentence covers every observed cell, *once
the committee's own sentence is persisted*. Before this slice it was
not, and two Supply Governance abstentions with genuinely different
causes were indistinguishable from the record. That is the one contract
change this slice made, and it was forced rather than chosen.

---

## 2. Two defects the measurement found

**`judged_at` meant two different moments.** Fee Capture stamped the
moment the model answered; Supply Governance stamped
`rule.state.observed_at` — when the *chain* was read. Because
`record_id` derives from `judged_at` plus content, two convenings from
one cached rule produced **one record id**, the second append was a
no-op, and the record said the committee had met once when it had met
twice. That breaks the one thing PR #113 requires to be honest: a count
of judgments. Fixed — `judged_at` is when the committee concluded, and
ADA now carries three distinct Supply Governance records where it
carried one.

**`because` was not persisted.** PR #113 deliberately excluded prose,
and the ban is right for *a model's reading of a judgment*. But a
committee's own account of its own outcome is part of the answer, not a
later reading of it — and without it, ETH and ARB both read
`insufficient_evidence` under Supply Governance with nothing to tell
them apart. Store schema 3 carries it, read with a fallback.

---

## 3. What the cell is

```text
committee        identity, version, fingerprint — from the record
question         the remit, from the live contract; None if unregistered
posture          answered / four kinds of not
applicability    the committee's own decision
state            judged / abstained / unavailable
verdict          the committee's own token, never interpreted
verdict_stated   the committee's own sentence for it
abstained_because / because / unavailable_because
confidence       as that committee expresses it — carried, never compared
refs, evidence_count   in that committee's own units
comparability    is this still today's contract? (#114)
judgments_recorded     a count, never a duration
```

A committee that has never run is an `UnjudgedCommittee` — its own type,
because *never tried* and *tried and could not answer* are different
facts and rendering them alike would claim the first had been attempted.

---

## 4. What it refuses

No score, vote, agreement, weight, rank, majority, overall verdict,
favourable/adverse mapping or common verdict scale. Two committees
answering different structural questions are not two votes on a shared
proposition.

Three guards, because a field test alone would miss the next aggregate
arriving as a helper function:

1. `AssetCommitteeMatrix` has exactly three fields — `asset`,
   `assessments`, `unjudged` — asserted.
2. No attribute on any matrix type matches any of thirty forbidden
   names.
3. The **source** of all three matrix modules is searched: no `def` or
   `class` name may contain any of them.

And the serialised payload is checked the same way, because the frontend
is where an aggregate would be cheapest to invent.

---

## 5. Committee N+1

The core invariant, checked rather than claimed: the protocol acceptance
specimen from PR #114 — a custody committee with **three** verdicts that
ships nowhere — is registered by passing its contract in, and the matrix
renders it with no branch learning it exists. A companion test asserts
that neither matrix module names any committee or any committee's verdict
tokens.

It could not have branched usefully in any case: this layer does not know
what a verdict means, so it has nothing to branch on.

---

## 6. The corpus, preserved

```text
asset   Supply Governance        Value Capture
1INCH   known_not_applicable     no_mechanism_evidenced
ADA     governance_set           no_mechanism_evidenced
ARB     evidence_insufficient    no_mechanism_evidenced
BTC     consensus_bound          known_not_applicable
ETH     evidence_insufficient    mechanism_evidenced
HYPE    evidence_insufficient    execution_unavailable
SOL     governance_set           mechanism_evidenced
TAO     applicability_unknown    applicability_unknown
```

Every distinction #115 exposed survives the projection, each asserted by
its own test: BTC and 1INCH keep opposite applicability; HYPE keeps two
different unanswered reasons with two different sentences; ADA keeps two
structurally unrelated answers with neither mapped onto the other; TAO
keeps applicability uncertainty stated independently by both.

One observation the detail view surfaced that the #115 grid hid: HYPE's
Fee Capture cell is `execution_unavailable` because **the judge model
wrote the word "buy" and the validator refused the draft**. The PR #110
guard working, visible now because the committee's own sentence travels.

---

## 7. Recorded debt, deliberately unsolved

- **There is no shared notion of "acquired for committee N".** Fee
  Capture reads a stored protocol-fundamentals door; Supply Governance
  needed its own cached issuance door. `movrvest acquire` does not know
  to fill the second. The matrix is **not** the place to fix this: it
  reads and must never acquire, and teaching it to populate one
  committee's cache would couple the projection to one committee's
  evidence path. Acquisition orchestration deserves its own slice once
  its contract is measured.
- **`Confidence` saturates**, as above. Carried, never compared, not
  redesigned.
- **`execution_unavailable` and `evidence_insufficient` are not
  comparable across committees**, and no universal abstention ontology
  was built. Information is preserved instead: each cell keeps its own
  reason and its own sentence.
- **The model seam is per-committee** and the matrix cannot say which
  absences are switchable.

---

## 8. Surfaces

`movrvest committees [SYMBOL] [--evidence]` — one block per committee
with a symbol, the corpus as a grid without one. There is no bottom row.

`GET /committees/{symbol}` and `GET /committees/contracts` — the
projection, serialised. **Deliberately not a section of the dossier**:
placing it there would mean deciding where in the investor's narrative a
collection of independent structural judgments belongs, and that is the
layer this slice was told not to build. No frontend work was done for
the same reason.
