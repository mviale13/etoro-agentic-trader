# The Value Capture Committee — the first bounded judgment

**Status: built 2026-08-10. Off by default.** No recommendation, no
score, no portfolio coupling, no committee aggregation, no Artificial
CIO. One committee, one question, three possible outcomes.

```bash
MOVRVEST_COMMITTEE_JUDGMENT=on movrvest committee-judgment ETH --evidence
```

---

## The boundary this crosses

Everything before it establishes knowledge and was deliberately built
unable to read meaning into it:

```text
Evidence → Finding → Temporal Finding → Synthesis      (knowledge)
Eligible grounded findings → Committee → Judgment      (judgment)
```

The permission to interpret is new, so it is granted structurally rather
than by convention.

---

## A. The remit, chosen by measurement

Measured first. Eligible (`MEASURED` / `REPORTED`) claims across the
eight-asset corpus:

| evidence | coverage |
|---|---|
| `return.24h / 7d / 30d` | 8/8 — but this is price, and a committee judging it is a momentum score |
| `network.fees.*` | **8/8** — the widest non-price evidence |
| `network.holder_revenue.*` | 4 with a figure, **3 established-and-empty** |
| `flow.*` | 2/8 — too narrow |

The holder-revenue sibling is what makes the question answerable: under
S2's sibling rule a source that publishes the metric for comparable
entities and none here is **establishing an absence**, not omitting a
number. Nothing else in the corpus separates six assets three ways on a
question an investor would ask.

**The remit:**

> Does this network generate evidenced fee activity, and does an
> evidenced mechanism capture some of it for the token or its holders?

Two clauses, both of which must be evidenced. What it deliberately does
**not** ask is whether the amount is large enough to matter.

---

## B. Three separate questions, never collapsed

| step | decided by | outcomes |
|---|---|---|
| **1. Applicability** — is this economically meaningful here? | the committee's own rule, reading the archetype as evidence | `APPLICABLE` · `NOT_ECONOMICALLY_APPLICABLE` · `UNESTABLISHED` |
| **2. Evidence** — is there enough eligible evidence? | code | findings, or none |
| **3. Judgment** — what does it conclude? | the judge, validated | `MECHANISM_EVIDENCED` · `NO_MECHANISM_EVIDENCED` · abstain |

**Applicability is decided before any evidence is read**, so a rich
evidence set cannot make an inapplicable question applicable. Bitcoin
has eligible evidence and is still not asked.

### Why the committee owns its applicability rule

It would have been one line to call `applicability_for(archetype,
HOLDER_VALUE_ACCRUAL)`. That was the first draft, and it was wrong in
two ways.

`TokenArchetype` was built to decide which questions an **Asset
Quality** layer asks. A committee that forwarded to it would be a
generic crypto-quality judgment wearing a narrow remit, and would change
meaning silently the next time that taxonomy moved for another purpose.

And it produced a concrete defect: **BTC and TAO came out identical**,
both `not_asked`. They are not the same. Bitcoin's economic role is
established and the question is the wrong instrument for it; Bittensor's
role is not established at all, so this platform cannot say whether the
question applies. Collapsing them reports *we know this does not apply*
when the truth is *we do not know*.

So the committee states its own rule, in economic terms:

> *"This asset's established economic role is monetary: the fees its
> users pay are the budget that secures the network rather than a flow
> the token is entitled to. Asking whether they are captured for holders
> is the wrong instrument, so the question is left unanswered rather
> than answered adversely."*

That is S5.3's own finding restated — the same figure is a security
budget or a transfer depending on where it goes. **This is a coupling,
and it is named**: the committee reads one fact from S3 and owns the
rule applied to it.

---

## C. Neither verdict is a grade

`MECHANISM_EVIDENCED` is **not** "favourable". It is a structural fact
about the token's economics. Whether it is good depends on what an
investor is buying the asset for, and that judgment belongs to a layer
that does not exist.

Asserted by test: no verdict value or wording contains *favourable*,
*adverse*, *positive*, *negative*, *strong*, *weak*, *good*, *poor* or
*healthy*.

**And no threshold is encoded.** 64%, 18% and 9% are excellent contrast
and six observations do not establish that 5% is a floor — S5.3 already
parked magnitude outside quality for exactly this reason. The committee
reports the share as evidence and refuses to band it. Tested
behaviourally rather than by keyword, because the module *explains* that
it establishes no threshold and a text search finds the sentence
refusing one.

`NO_MECHANISM_EVIDENCED` is only reachable when all four of the owner's
conditions hold: the question applies, the source establishes the
absence (sibling rule), the absence is not merely missing evidence, and
**the verdict does not assert that the absence is bad**.

---

## D. Eligibility is structural

```python
ELIGIBLE_CLAIM_TYPES = {MEASURED, REPORTED}
```

`EligibleFinding.__post_init__` raises on anything else, so an
`ATTRIBUTED` or `INFERRED` claim cannot be *constructed* as committee
evidence — the rule holds even if the assembly code is wrong. Synthesis
prose is unreachable from both modules, asserted over the parse tree:
**the synthesis is communication, not evidence**, and letting it back in
through the judgment door would launder a model's reading into a model's
premise.

---

## E. Code calculates; the judge interprets; the validator refuses

**§8** — every comparison is settled before the judge sees a word. The
share of fees reaching holders is Python arithmetic over two checked
figures, carried as its own finding with its own ref.

**§7** — confidence is established by `confidence_from(supporting,
across_captures)`, which counts observations and **never sees the
verdict**; the judge chooses the verdict and never sees the count. The
same verdict cited against one finding and then two produces
`SINGLE_OBSERVATION` → `MULTIPLE_OBSERVATIONS` with the answer
unchanged. Categorical rather than 0–100: three readings are three
readings, not 73% confident.

**§10** — the schema is the fence. Three fields, and no `score`,
`confidence`, `recommendation`, `conviction` or `stance` exists to fill.
The validator refuses an out-of-enum verdict, a ref that was not
supplied, a verdict citing nothing, a figure appearing in no supplied
fact, a name appearing in no supplied fact, and any of twenty
out-of-remit words. Fail-closed, as with the Executive Writer.

---

## F. The acceptance demonstration, live

```
asset  applicability                state       answer                    confidence
HYPE   applicable                   judged      mechanism_evidenced       multiple_observations
ETH    applicable                   judged      mechanism_evidenced       multiple_observations
SOL    applicable                   judged      mechanism_evidenced       multiple_observations
ARB    applicable                   judged      no_mechanism_evidenced    multiple_observations
ADA    applicable                   judged      no_mechanism_evidenced    multiple_observations
1INCH  applicable                   judged      no_mechanism_evidenced    multiple_observations
BTC    not_economically_applicable  abstained   not_economically_applicable    —
TAO    unestablished                abstained   applicability_unestablished    —
```

A judgment in full:

```
ETH
  applicability: applicable — This asset's established economic role —
    Smart-contract network — is one where activity accruing to the token is
    part of what the token is, so whether it does is a meaningful question.
  eligible evidence: 5 finding(s)
  judgment: measured network activity is captured for the token by an
    evidenced mechanism
  confidence: several independent supporting observations
  “Users paid fees over a day, and a stated mechanism—amount of ETH burned
    (base fees plus blob fees)—caused an amount to reach token holders over
    the same period.”
  resting on: F.ethereum-chain, H.ethereum-chain,
              T.network.fees.ethereum-chain, T.network.holder_revenue.ethereum-chain
```

| # | Demonstrated | Result |
|---|---|---|
| 1 | supported judgment, mechanism present | ETH / HYPE / SOL, citing fee + capture + share findings |
| 2 | supported judgment, mechanism absent | ARB / ADA / 1INCH, resting on the sibling finding |
| 3 | abstention | BTC and TAO, **for different reasons** |
| 4 | removing the decisive finding | the ref is refused as unsupplied; the model cannot rebuild it |
| 5 | `ATTRIBUTED` / `INFERRED` cannot affect it | `EligibleFinding` raises at construction |
| 6 | synthesis prose cannot enter | unreachable, asserted over the parse tree |
| 7 | confidence rises, verdict does not | 1 ref → 2 refs, same verdict, higher confidence |
| 8 | no output can express an action | the schema has three fields and no enum member is an action |
| 9 | every judgment resolves to eligible evidence | `grounded_in`, plus a live check over the corpus |
| 10 | provider failure ≠ abstention | `UNAVAILABLE` with a worded reason vs `ABSTAINED` with a reason code |

30 tests, none of which asserts that an asset is *good*.

---

## G. What this committee can now truthfully judge

**That an evidenced flow of network activity does or does not reach the
token — and, separately, whether that question is even the right one to
ask of this asset.**

Every layer before it was built unable to say this, deliberately:

- the **protocol layer** holds a fee figure and a holder-revenue figure
  and is forbidden to relate them;
- the **intelligence layer** reports both as claims and states in as
  many words that a driver is not a conclusion;
- the **journal** records that they held across captures and refuses to
  say what that means;
- the **synthesist** may connect them into a sentence and may not
  conclude from them.

The committee can now say: *these fees exist, this mechanism is
evidenced, and therefore — within this one question — activity is or is
not captured for the token.* It can also say *this question does not
apply here*, which is the answer the evidence architecture could
generate the inputs for and never reach.

**What it still cannot say, by construction**: whether any of that makes
the asset worth owning, whether 9% is enough, whether one asset is
better than another, or what anyone should do. There is no field for
those answers and no layer above it.

---

## Boundaries held

- **One committee**, one remit, earned by measurement — not a taxonomy.
- **No portfolio context**: no position, cash, concentration, holding,
  preference, `ExecutiveDecision`, `Recommendation` or `CommitteeOpinion`
  is reachable. Asserted over the parse tree.
- **No Asset Quality**, in either direction.
- **No aggregation, no recommendation, no CIO reasoning, no historical
  committee evolution** — none of it built.
- Off by default; with the flag off there is no judgment and the
  eligible evidence stands unchanged.
- Equity behaviour unchanged.
