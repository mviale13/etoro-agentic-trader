# Market-cap eligibility: a magnitude has no scale invariance

**Status: built. The largest deliberate decision change in this arc.
Stopped for review — the consequence needs the owner's ruling.**

The second warrant consumer, and the counter-example to the first.
`momentum-input-eligibility@1` admitted ASSUMED because a daily change
is a **ratio** over two closes of one series, invariant under any
linear rescaling. This slice asks the same question of the
market-significance quality point and gets the opposite answer, for a
reason that is arithmetic rather than temperamental.

> **A ratio survives a rescaling. An absolute comparison is destroyed
> by one.**

---

## 1. The audit, before any code changed

**Where market cap enters analytical logic.** Exactly two consumers on
this platform, and only one of them is unprotected:

| Consumer | Threshold | Gate today |
|---|---|---|
| `quality_signal_service.py:84` — the large-cap point | a single `$10bn` line, 1 point or 0 | **none** |
| `MARKET_ROBUSTNESS_RULE` (crypto, `crypto_quality.py:490`) | `$10bn` / `$500m`, 2 / 1 / 0 points | `EvidenceStanding.ESTABLISHED` via the #99 gate |

The brief's `$500m` / `$10bn` and its "0 / 1 / 2 points" belong to the
**crypto** rule. That consumer is already protected — by a *value*
standing (does a second source corroborate the number) rather than a
*translation* warrant (are we entitled to read the field this way) —
and every crypto asset reads UNKNOWN under it because the quorum of 2
is unmet. **This slice therefore changes nothing on the crypto path**,
and the equity large-cap point is the unprotected consumer.

**The path.**

```
Yahoo marketCap                      (registry: ASSUMED, kinds=(SEMANTIC,))
  → ValuationSnapshot.market_cap
  → CompanyFacts.market_cap          (company_facts_service.py:153)
  → QualitySignalService  market_cap >= 10_000_000_000 → 1 point
  → 3-factor count → HIGH/MEDIUM/LOW → 80/62/40
  → CompanyCommitteeService  quality term ×0.35
  → CompanyRecommendation → DecisionEvidence → ArtificialCIO.decide()
```

**The warrant in force: ASSUMED**, and the threshold's own unit is
**unstated** — `LARGE_CAP_THRESHOLD = 10_000_000_000` names no
currency, so the comparison is between an unlabelled magnitude and an
unlabelled constant.

**Corpus, measured before changing anything** (72 stored magnitudes):

- 48 above the line, 24 below.
- **17 are listings whose magnitude is denominated in a currency this
  platform never reads** — `.PA`, `.L`, `.CO`, `.SW`, `.DE`, `.MI`,
  `.BR`, `.MC`.
- **57 of 72 sit within a factor of 100 of the threshold**, so a
  hundredfold denomination error changes which side they fall on. The
  pence-versus-pounds error is not hypothetical: #134 measured BP.L's
  *price* stored as `517.2` under a hardcoded `"USD"`.
- `CompanyFacts.currency` is never assigned anywhere (#134 §7), so no
  currency accompanies any magnitude.

## 2. The semantic requirement

The consumer depends on **three crossings**, and they fail
independently:

| Kind | Question | Status |
|---|---|---|
| **Semantic** | is this figure *this company's* equity value? | ASSUMED |
| **Unit / representation** | in what denomination? | **not established at all** |
| **Identity** | which instrument does the record describe? | unresolved for SPCX (#134 §6) |

The brief's admission criterion is the one applied:

> A warrant may be admitted only if the unresolved uncertainty cannot
> change which side of the absolute threshold the value lies on.

For ASSUMED that condition is **measured false** — 57 of 72 flip under
a denomination error the platform cannot rule out. So ASSUMED is
refused, and with it DECLARED: a provider's statement of what a field
*means* establishes semantics and says nothing about the
*denomination* this consumer additionally needs.

```python
ELIGIBLE_MARKET_CAP_WARRANTS = {VERIFIED, VALIDATED}
```

plus a **conjunction**, because a warrant alone is not the whole
requirement:

```python
admissible = is_measured and warrant in warrants and denomination_established
```

**Explicit membership, no ordering, no `warrant >= X`.**

### The middle option, measured and refuted

A tempting third rule was tested rather than dismissed: admit ASSUMED
**where the margin proves safety** — where the magnitude is more than
100× above the threshold or below 1/100 of it, a hundredfold
denomination error cannot flip it. It is mathematically clean and it
would have preserved 15 of 72.

**The corpus refutes it, using the brief's own specimen.** Under that
rule **SPCX scores the large-cap point**: $1.75T is comfortably more
than 100× the line, so no denomination error could move it — but
SPCX's defect is not denomination, it is **identity**, and an identity
error is unbounded. The number may describe a different economic
object entirely. A margin test bounds one uncertainty and is silent
about the other. (It also confidently calls HYPE "small" on Yahoo's
known-wrong $8,105.)

That refutation is why the rule is a conjunction over crossing kinds
rather than a tolerance on the value.

## 3. Three states, in the existing vocabulary

No new epistemic state was invented, because the domain already had
one. An inadmissible magnitude is **not counted as a factor**, exactly
as an absent one has always been — so `available` falls to 2 and
`QualitySignal` reports how much of the question set it could read.

1. measured and below → "Small or mid-cap company.", 0 points, counted;
2. measured and above → "Large-cap company.", 1 point, counted;
3. **not admissible → no finding, not counted, `available` 3 → 2.**

State 3 is not zero and not "small". `MarketCapMagnitude.refusal()`
names the crossing that failed and never the company, and a guard
asserts the word *small* cannot appear in it.

## 4. Historical records

**No.** A stored `market_cap` cannot say which warrant was in force
when it was accepted: the fundamentals cache holds one bare number per
symbol, no per-field provenance, and `observed_at` equals `stored_at`
in all 77 records (#134 §5). Nothing is fabricated for old records.

The consequence is stated rather than worked around: **the repair
applies at evaluation, not at acquisition** — unlike #135's, because
eligibility is decided from the *registry* at read time rather than
from something the adapter must have recorded. A replayed legacy
magnitude is therefore judged under today's registry, which is a
deliberate choice and the honest one available: the alternative would
be to grandfather values whose warrant nobody knows.

## 5. Rule versioning

**New rule `market-cap-input-eligibility@1` (ARGUED).**
`provider-quality@1` is **untouched** — its threshold, points, bands
and score map keep fingerprint `3adc0fd3fd9f`, because the ruler did
not move; only the admissibility of its input did.

The fingerprint is over the membership, **canonicalised by sorting**
before hashing (a frozenset's iteration order is not stable), pinned
at `a3f6c145c2de`. The ARGUED count moved 2 → 3 with the assertion
renamed and updated deliberately.

## 6. Before → after

Corpus of 3,024 trials over market cap × P/E × EPS × dividend ×
daily change × volatility, run in a worktree of `564ab1f` with the
`sys.path` fix #135 established.

| | Before | After |
|---|---|---|
| quality HIGH | 144 | **0** |
| quality MEDIUM | 768 | **336** |
| quality LOW | 2,064 | **2,352** |
| quality UNKNOWN | 48 | **336** |
| factors available = 3 | 1,152 | **0** |
| **BUY** | 105 | **42** |
| **HOLD** | 2,094 | **2,058** |
| **SELL** | 825 | **924** |

**63 BUY recommendations withdrawn, and 99 new SELL vetoes.**

The second number is the one that needs the owner's attention, and it
deserves a plain explanation rather than a footnote. Quality UNKNOWN
scores `0` in the weighted vote, not `−1` — so this repair never
*pushes* toward a veto. What it does is stop the quality point from
*holding one off*: in those 99 cases the value signal (EXPENSIVE,
−0.40) and momentum (BEARISH, −0.25) already summed to −0.65, past the
−0.50 veto line, and an unestablished large-cap point was the only
thing keeping the case at HOLD. The veto was always what the other two
signals demanded; it was being masked by evidence the platform could
not justify.

**HIGH is now unreachable on the provider-quality route** (144 → 0),
because three factors can never all be available while the size factor
is refused. The filing-grounded route (`quality-grounded@1`, #81) is
untouched and remains the way a company can reach HIGH.

On the live stored corpus the effect is the same shape: of 72
securities, all 10 that read HIGH drop to MEDIUM, and 17 whose only
readable factor was size drop to UNKNOWN.

## 7. Where the change comes from

Not a veto rule, not a weight, not a quorum. **A coverage effect
inside the score**: `BANDS` counts absolute points against a
three-factor ruler, so removing one available factor lowers the
reachable band. That is the same treatment an absent market cap has
always received, and it is now reached by a second route.

No threshold or weight was modified: `0.40 / 0.35 / 0.25`, `±0.50`,
`$10bn` and the band table are all byte-identical.

## 8. Guards

`tests/test_market_cap_eligibility.py`, 17 tests:

- above / between / below the line under an admissible magnitude →
  the existing 1-point and 0-point results, unchanged, plus both sides
  of the `$10bn` boundary and the constant itself;
- a numerically huge but semantically unjustified magnitude → **never
  the point** (SPCX's figure, by value);
- correct semantics with an unresolved denomination → refused;
- an assumed currency is not an established one;
- the refusal names the crossing, never the company;
- membership enumerated by value, ASSUMED / DECLARED / UNKNOWN out;
- eligibility is not representable as a band change — two rules, two
  fingerprints, `provider-quality` still at version 1;
- **an end-to-end decision regression**: with value EXPENSIVE and
  momentum BEARISH, an admissible magnitude holds the case at HOLD and
  an inadmissible one lets the veto fire — pinning the causality the
  brief asked for.

Plus a cross-slice guard in `test_momentum_warrant_consumer.py`
asserting the two consumers require **different memberships**: a
single global "provider confidence" policy would have to give both the
same answer, and either answer is wrong for one of them.

## What this slice did not do

No repair of the provider registry, SPCX identity, Yahoo semantics or
currency normalisation. No threshold, weight, veto or gate moved. No
other consumer learned to read a warrant — value and risk are still
asserted to contain no warrant vocabulary at all.

**Recorded and unsolved:** reading Yahoo's `financialCurrency` would
establish the denomination for most securities and is the obvious next
repair — it is a new translation needing its own warrant, and it is
deliberately not in this slice. Until it lands, the size factor is
unscorable for every security, and that is what the platform can
honestly say.
