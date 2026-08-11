# The Crypto Committee Protocol

**Status: accepted, built, Fee Capture migrated, decision-neutral.**

Extracted from two working systems rather than designed ahead of them —
the Value Capture Committee (#112) and Judgment History (#113). The
question the slice had to answer was not *what would a good abstraction
look like* but:

> What must every future crypto committee satisfy so MOVRvest can run
> it, know whether it spoke, keep its evidence basis, record its
> history, and later compose several of them **without learning any
> committee's semantics**?

The headline result is that the extraction was a **relocation, not an
invention**. The framework's *logic* was already generic; only its
*vocabulary* was not.

---

## 1. What the two implementations forced into the contract

Measured by reading every decision Judgment History makes. All of them
run on four things, and none needs to know what an answer means:

```text
posture.is_answered              did the committee speak
previous.verdict == current      is this the same answer as before
previous.applicability vs now    does the question still apply
identity.comparability(other)    were both produced under one contract
```

So the protocol is exactly what those four need, plus what the record
must persist:

| Concept | Why it is generic |
|---|---|
| `CommitteeContract` | identity, version, question, applicability-rule id, verdict vocabulary, admitted evidence — the four inputs a fingerprint needs |
| `CommitteeIdentity` | what a record persists: key, name, version, fingerprint |
| `StructuralVerdict` | a token and a sentence. **Two members, and the omissions are the point** |
| `Applicability` (3 states) | every committee needs *applies / wrong instrument / cannot tell* |
| `ApplicabilityBasis` | state + reasoning + the economic role it was read from |
| `JudgmentState` (3) | answered / abstained / unavailable |
| `Confidence` + `confidence_from` | counting observations is the same everywhere |
| `EligibleFinding`, `ELIGIBLE_CLAIM_TYPES` | the epistemic floor, argued from claim types and not from fees |
| `Committee` protocol | `contract`, `basis`, `evidence`, `judge` — one member per thing a caller already does |

**One line proved the framework was not yet generic**, and it is the
whole reason this slice exists:

```python
JudgmentPosture.EVIDENCE_OF_PRESENCE
if verdict is Verdict.MECHANISM_EVIDENCED
else JudgmentPosture.EVIDENCE_OF_ABSENCE
```

Judgment History was reading a Fee Capture verdict and deciding what it
*meant*.

---

## 2. What looked generic and was not

- **The verdict vocabulary.** `MECHANISM_EVIDENCED` /
  `NO_MECHANISM_EVIDENCED` sat in the shared domain. Moved to the
  committee. The framework now carries a token and a sentence and
  understands neither.
- **The question text.** `_QUESTIONS` and `_REMITS` held Fee Capture's
  wording in the framework. Moved to `CONTRACT`.
- **`Remit` as a framework enumeration.** A central list every
  committee has to be added to. Replaced by a `key` string on the
  contract — which is what the store already persisted, so the line
  format did not change.
- **`posture_of`'s answered branch.** See above.
- **The applicability *rule*.** The three applicability *states* are
  generic; the rule choosing between them is economics and stays with
  the committee. PR #112 already established this the hard way.

---

## 3. Redundant or reconstructable fields

**`abstained_because` is fully reconstructable from
`(applicability, state)` today.** Measured, and it is a total bijection
across every live record:

```text
NOT_ECONOMICALLY_APPLICABLE + ABSTAINED → not_economically_applicable
UNESTABLISHED               + ABSTAINED → applicability_unestablished
APPLICABLE                  + ABSTAINED → insufficient_evidence
```

It was **kept anyway**, and the reason is the protocol's own test: those
three are Fee Capture's reasons. A second committee that abstains for a
fourth reason — *the rule cannot discriminate on this evidence* — is
still `APPLICABLE + ABSTAINED`, and the framework could not derive it.
The field is committee vocabulary that happens to be derivable from one
committee. Removing it would have been a storage migration that bought
a constraint.

**Nothing else was redundant.** In particular `applicability` is *not*
reconstructable from the verdict or the abstention wording — the
prohibition the ruling names — and an `UNAVAILABLE` judgment implies
nothing about applicability at all.

**`JudgmentPosture` lost a member and lost no information.** Six became
five. The presence/absence split was used for **wording only**; the
record now carries the verdict token and the committee's own sentence,
so the two answered states are as distinct as they ever were —
distinguished by identity rather than by the framework knowing which one
is presence.

---

## 4. What history needed that the committee did not expose

Two things, and both were seams where two facts could disagree:

1. **The contract.** `JudgmentHistoryService.record(judgment, VERSION, …)`
   took identity as a *separate argument*, so a caller could file a
   judgment under a committee that did not produce it and nothing would
   notice. The judgment now carries its own contract and the argument is
   gone.
2. **Which history a judgment belongs to.** `against_history` and
   `standing` took a remit from the caller; both now read
   `record.committee.key`. A judgment compared against another
   committee's past would be a transition between two questions.

A third, already fixed in #113 and worth naming because the protocol
makes it structural: **applicability and the economic role it was read
from**. `ApplicabilityBasis` now carries them together, so a committee
cannot state one without the other.

---

## 5. Does this make a second committee cheaper — without constraining it?

**Yes, and the evidence is `tests/test_committee_protocol.py`.**

It describes a committee that ships nowhere and differs from Fee Capture
in every way the protocol claims not to care about — a custody question,
**three verdicts rather than two**, its own applicability rule, its own
evidence. It implements four members and inherits nothing (structural
typing, so the framework is not the place a committee registers). The
whole lifecycle then runs: judge → record → project → stand → count,
with all ten of #113's distinctions reached through the generic
contract.

Three verdicts is the load-bearing part. A framework that had quietly
assumed a binary — a `bool`, an `is_positive`, a pair of postures named
presence and absence — passes every Fee Capture test and fails this one.

And the constraint runs the other way too. A test reads the framework's
own source and asserts that **no committee's verdict tokens appear in
it**, that it imports no committee, and that neither
`CommitteeContract` nor `JudgmentTransition` offers `polarity`,
`is_favourable`, `rank`, `score`, `weight`, `sentiment` or `direction`.
The moment one of those exists, every consumer downstream is free to
build a score on it and call the score earned.

---

## Migration: the outcomes are semantically identical

Run live under the protocol, verified from the store rather than from
the prose:

```text
HYPE / ETH / SOL      mechanism_evidenced        answered
ARB / ADA / 1INCH     no_mechanism_evidenced     answered
BTC                   —                          known_not_applicable
TAO                   —                          applicability_unknown
```

All eight as stated in the ruling. BTC and TAO remain the two opposite
kinds of no-answer.

**Records written before the migration still read.** Storage schema went
to 2, adding the committee's display name and the committee's own
sentence for its verdict. Both are **read with a fallback rather than
migrated** — a schema-1 line names its committee by key and its answer
by token, which is terser and exactly as true. The journal's rule holds:
a file that is never rewritten cannot be migrated. Proven by the
record ids of the pre-migration HYPE judgments coming back
byte-identical.

---

## What this deliberately is not

No second committee ships. No registry — with one committee a registry
is speculation, and both commands name the one contract that exists. No
aggregation, no weighting, no cross-committee agreement, no score, no
recommendation, no thesis, no portfolio coupling, and no layer that
reads a verdict as favourable or adverse.

The protocol is the *lifecycle* a committee plugs into. What a committee
concludes, and what that conclusion is worth, remain entirely the
committee's — and the second half of that has not been earned by
anyone.
