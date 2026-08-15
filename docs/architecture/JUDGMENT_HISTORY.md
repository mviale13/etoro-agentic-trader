# Judgment History

**Status: accepted, built, decision-neutral.**

The intelligence journal answered *what did this platform know about BTC
on 1 August*. This answers a different question, and the difference is
the slice:

> **What did this committee conclude, when — and is what changed a change
> in the evidence or a change in the judgment?**

Those are two facts, they move independently, and a system holding both
will report the first as the second unless something structural stops
it. That sentence — *"the number moved, therefore our conclusion moved"*
— is the most expensive one an investment platform can write, because it
is the one a reader acts on.

---

## The three axes

Every transition carries three, never one field:

```text
JudgmentChange      what happened to the committee's answer
SupportChange       what happened to the count of observation beneath it
EvidenceMovement    what happened to the evidence itself
```

**Evidence moving under a steady answer is the ordinary case.** A fee
reading is a different number every day. A layer that collapsed these
into one field would announce a reversal roughly daily while the
committee had not moved at all, and every announcement would be built
out of true parts.

So `EvidenceMovement.CHANGED` beside `JudgmentChange.VERDICT_UNCHANGED`
renders as a sentence that says so out loud:

> The evidence moved and the committee's answer did not, which is a fact
> about the evidence and not a change in what the committee concluded.

`SupportChange` is the third because §4's case D needs it: the same
verdict with more observation behind it is neither an unchanged fact nor
a changed conclusion. It is a changed count, and the wording says
*observations* for exactly that reason. Confidence is established by
code counting evidence and the verdict is chosen by the judge — neither
sees the other — so more support can never move the answer.

---

## The measurement, and it was live

The corpus was judged twice on 2026-08-10, and the second run produced
the demonstration this design was built for **without being contrived**:

| run | HYPE evidence | judgment |
|---|---|---|
| committee off | 4 eligible findings | no answer — the machinery did not run |
| committee on | *the same 4, byte-identical* | `mechanism_evidenced` |
| committee off | *the same 4, byte-identical* | no answer |

`EvidenceMovement.UNCHANGED` on both transitions, and the judgment moved
twice. **The evidence axis and the judgment axis are not merely modelled
apart — they were observed apart on the first live run.** A layer that
derived judgment change from evidence change would have reported
nothing happening, three times.

The reverse case — evidence moving under a steady verdict — is
demonstrated against controlled records rather than live, because
producing it live means waiting for a fee reading to move and paying for
a second model call to reach the same verdict.

---

## Five states that must never collapse

`JudgmentPosture`, six members, total over every
`(applicability, state, verdict)` combination — asserted by a test that
enumerates the product and requires every posture to be reachable:

```text
KNOWN_NOT_APPLICABLE      the question is the wrong instrument       (BTC)
APPLICABILITY_UNKNOWN     we cannot establish whether it applies     (TAO)
EVIDENCE_INSUFFICIENT     it applies, and evidence cannot answer it
EXECUTION_UNAVAILABLE     it applies, and the machinery did not run
EVIDENCE_OF_ABSENCE       it applies, and no mechanism is evidenced
EVIDENCE_OF_PRESENCE      it applies, and a mechanism is evidenced   (HYPE)
```

Four of the six produce no verdict. A history storing *"no verdict"*
would make them one fact — and the owner's PR #112 catch is exactly
that: BTC and TAO both produce no verdict and **their problems are
opposite**. On the live record they land in different postures, and the
transitions between them mean different things: *the question became
answerable* and *the question turned out not to apply* are opposite
readings of the same missing verdict.

Six rather than the ruling's five, because the committee already refuses
to collapse the last two: an abstention is the committee knowing its
limits, and an unavailable judgment is the machinery failing. Reporting
a broken provider as intellectual honesty is the lie `JudgmentState` was
built to prevent, and history inherits that refusal rather than undoing
it.

---

## A previous verdict is never carried forward

`JudgmentStanding` is the object that enforces §5, and it does it
**structurally rather than by wording**: when today's committee reached
no answer, `standing.verdict` returns `None` and the earlier record is
reachable only through `previously`, whose name says what it is. A
caller cannot print a stale verdict as current by accident because
nothing offers it as current.

The live sentence, from the third HYPE run:

> HYPE: the previous judgment, on 10 August 2026, was that measured
> network activity is captured for the token by an evidenced mechanism.
> Today the question applies and the committee did not run, so there is
> no answer either way. The earlier answer is therefore reported as what
> the committee concluded then, and is not restated as a current
> finding.

Never *"the mechanism remains evidenced"*. And the transition beneath it
is `BECAME_UNANSWERABLE`, whose own wording carries the guard: *"which
leaves the earlier answer unrefreshed rather than contradicted"*. **An
unavailable today is not a reversal**, and a surface that ranked it as
one would be reporting a provider outage as a change of mind.

---

## Committee version is part of identity

`CommitteeVersion` carries a declared version *and* a fingerprint
**derived from the live contract** — the remit question, the
applicability rule id, the eligible-claim-type contract, and the verdict
vocabulary. Edit any of the four and today's committee fingerprints
differently, so every record written under the old one becomes visibly
incomparable rather than silently comparable.

Two failures, told apart because they are different:

- `DIFFERENT_VERSION` — somebody declared a change. Honest.
- `CONTRACT_CHANGED` — the fingerprint moved and the version did not.
  **Nobody declared it**, and saying so is more useful than treating the
  two as one.

Incomparability **short-circuits everything**. The other two axes are
set to `NOT_COMPARABLE` rather than computed and hedged, because a
verdict transition across a redefinition is arithmetic over two
different questions wearing the clothes of a fact about an asset. And an
earlier verdict under an incomparable contract cannot become the
standing either — nobody can say what it would have concluded under this
contract.

---

## No semantic inflation

`NO_MECHANISM_EVIDENCED → MECHANISM_EVIDENCED` means that transition.
Not improved fundamentals, not a strengthened case, not a bullish
development, not increased conviction, not BUY.

Two guards, and the second is why the first is possible:

1. **The schema is the fence.** `JudgmentTransition` has nine fields and
   `JudgmentRecord` has sixteen, and neither has room for a
   recommendation, a score, a stance or a thesis — asserted by a test
   over the dataclass field sets. Nor does the record carry synthesis
   prose: *a model's reading of a judgment is communication*, and
   persisting it would turn last week's wording into this week's
   history.
2. **The vocabulary is finite.** Every sentence this layer produces is
   built only from its own enumerations, never from free text supplied
   by a committee or a provider — which is why `unavailable_because`
   appears in the CLI beside a transition and never inside one. So the
   full set of producible sentences is enumerable, and a test enumerates
   it: every posture × state × confidence × role, every transition
   between the first twelve of them, every standing, every coverage
   line, checked word-by-word against a list of thirty-seven inflation
   terms.

That test is a real check rather than a reassuring one **because** the
wording is closed. Open it to free text and the guarantee goes.

---

## Synthesis explains; it does not discover

§8's order, and the `H`-group lesson applied one layer up. A transition
reaches the synthesist as a `J` finding **only where code already
established it**, carrying its record ids as provenance. The model may
then write

> The committee now finds an evidenced token-capture mechanism where the
> previous compatible judgment found none.

and the existing validator polices it unchanged — the sentence's
vocabulary comes from the supplied finding, so no new rule was needed.
With no transition established there is no `J` finding, and the same
sentence is refused for citing evidence that was not supplied. **The
model cannot be the thing that noticed.**

---

## Recording is an explicit act

`movrvest judge [SYMBOL]` writes; `movrvest judgment-history [SYMBOL]`
and `movrvest committee-judgment [SYMBOL]` read and write nothing. The
separation is `observe`'s, for a sharper reason here: if judging wrote
history, opening a surface would append a judgment event, and
*"the committee has reviewed this eleven times"* would be a count of
page views wearing the language of review.

Storage is the journal's, deliberately its twin rather than its
subclass: JSON Lines, one file per asset, append mode only, **schema
carried per line** because a file that is never rewritten cannot be
migrated. A judgment written under committee v1 must stay readable
beside one written under v2 forever — that is not a storage
convenience, it is the evidence that the committee ever held the earlier
view.

And the record is the whole of that claim, not a cache of a derivable
one. **Delete the file and the ability to say *the committee previously
found this* goes with it** — running the committee again produces
today's judgment from today's evidence, which is a different fact.
Demonstrated by a test that deletes the file and asserts the standing
falls back to `NONE` rather than regenerating a verdict.

---

## What is deliberately not here

No second committee. No aggregation across committees, no overall score,
no thesis, no portfolio coupling — the ruling's closing instruction, and
an import test would be the place to enforce it when a candidate
appears.

Nothing consumes a transition except the CLI and the optional synthesis
seam. `MOVRVEST_COMMITTEE_JUDGMENT` remains off by default, and with it
off every asset records an honest `EXECUTION_UNAVAILABLE` — which is a
judgment event worth keeping, because *the committee did not run* is a
fact about a day.

---

## What `evidence_count` counts (2026-08-15)

**Status: accepted and built.** The recording defect PR #126 found and
reported without fixing.

### The old meaning was an accidental mixture

`app/commands/judge.py` called `committee.evidence(asset)` immediately
after `committee.judge(asset)` and passed the result to the recorder,
under a comment reading *"the evidence the committee was actually
given"*. On every path where `judge()` consults its evidence that was
true. On the two applicability paths — which return **before** consulting
anything — it was not: the recorder resolved evidence the committee had
never seen.

So one field carried two meanings depending on a branch the field could
not see:

| posture | reached by | what the count meant |
|---|---|---|
| answered | after `self.evidence(asset)` | eligible evidence **supplied to the committee** |
| evidence insufficient | after | supplied (and empty) |
| execution unavailable | after | supplied |
| known not applicable | **before** | eligible evidence **held in the store**, never given |
| applicability unknown | **before** | held, never given |

Measured over the 67 stored records:

| | records |
|---|---|
| total | 67 |
| reached without consulting evidence | 16 |
| …of which recorded a non-zero count | **10** (BTC value capture ×5 at 3, TAO value capture ×5 at 1) |
| …of which recorded 0 by coincidence | 6 (supply governance holds no rule for those assets either) |

That coincidence is why the defect survived: on one of the two
committees the wrong meaning and the right value agreed.

### It is also not `refs`

`refs` is what the verdict **cited**. Across the 26 answered records:

| | records |
|---|---|
| count == refs | 15 |
| count > refs | **11** |
| count < refs | 0 |

Supplied and cited genuinely differ in 42% of answered judgments, so one
counter could never have carried both. Both are kept, and neither is
derived from the other.

### The field is not renamed

The corpus proves the answer is *supplied to the committee*, which is
what `evidence_count` already says on the majority of paths. What was
wrong was the value on two paths and the absence of any statement about
which meaning a line was written under. Both are fixed; the name stays.

### Half one: the judgment carries its own evidence

`CommitteeJudgment.considered` holds the eligible evidence the committee
was given, and is empty wherever it reached an outcome without asking
for any. `record_from` reads it there, and its `evidence` parameter is
gone — **PR #113's identity fix, applied to evidence**: *a value supplied
alongside a judgment is a value that can disagree with it.* It did.

`abstain()` defaults `considered` to nothing, because an applicability
abstention is the most common way to reach it and the default must be
the truthful value. `unavailable()` takes it explicitly, because
machinery can fail on either side of consulting evidence — Value Capture
reads its findings *before* checking whether judging is switched on, so a
run with the flag off has been given its evidence and reached no verdict.

### Half two: the meaning is versioned, and history is not rewritten

`EvidenceSemantics` — `HELD_AT_RECORDING` / `SUPPLIED_TO_COMMITTEE` —
rides on the record, store schema 5. A line without the field decodes as
the old meaning, which is exactly what it was; **absent is not unknown**.

`_evidence_movement` returns `SEMANTICS_CHANGED` when two records
disagree about it. A distinct member rather than a reuse of
`NOT_COMPARABLE`: that one says the *question* differed, and here the
committee, the contract and the question are identical — only this
platform's account of what it counted has moved. It is not `moved`.

**No stored line is rewritten and none needed to be.** The store has no
write mode by design, and a rewrite would have changed 16 of 67
`record_id`s, which are hashed over the evidence digest and cited by
every transition.

### Proof: zero fictitious movements

A forward-only fix — correcting the producer and leaving history alone —
was measured first, and it was not safe:

| asset | committee | fictitious movement |
|---|---|---|
| BTC | value capture | `WITHDRAWN` |
| TAO | value capture | `WITHDRAWN` |
| 1INCH | supply governance | `CHANGED` |
| TAO | supply governance | `CHANGED` |

The last two are the sharper finding: their count was **already 0**, and
they moved because the *digest* did. `evidence_digest_of(())` is
`e3b0c44298fc1c14`, not the empty string — so zeroing a digest that was
already a digest-of-nothing invents a change out of two spellings of the
same absence.

With the semantics gate, re-judging every asset against its last stored
record produces **16 of 16 `semantics_changed` and 0 movements**.

### What each record now says

| asset / committee | posture | given | cited |
|---|---|---|---|
| BTC / value capture | known not applicable | 3 → **0** | 0 |
| TAO / value capture | applicability unknown | 1 → **0** | 0 |
| ADA / supply governance | answered | 11 | 11 |
| BTC / supply governance | answered | 8 | 8 |
| ETH / supply governance | evidence insufficient | 0 | 0 |
| HYPE / value capture | execution unavailable | 11 | 0 |

Two invariants hold over the whole corpus: a posture reached without
consulting evidence records none, and no judgment cites more than it was
given.

### The surface says which meaning it is reading

`movrvest committees` renders the count with
`EvidenceSemantics.stated` beside it, so a historical record reads
*"3 finding(s) — the eligible evidence held for this asset when the
judgment was recorded"* rather than restating an old measurement in
today's terms. `CommitteeAssessment` carries the semantics for the same
reason. **No investor-facing conclusion changed**: the crypto dossier
does not render either counter (PR #126), and no verdict, applicability,
confidence or reference moved.

### Guarded

`tests/test_evidence_semantics.py`. The strongest guard is structural
rather than observational: `committee.evidence` is monkeypatched to
raise, and both committees still reach every declining outcome — so the
recorded zero rests on the call never happening, not on a count being
discarded. Both halves were mutation-checked: removing the semantics
gate fails the migration test, and consulting evidence before declining
fails the invariant test.
