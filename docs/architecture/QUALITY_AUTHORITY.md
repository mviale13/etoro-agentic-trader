# Quality authority: a band is a claim about the business

**Status: built. `quality-authority@1`. The LOW/MEDIUM/HIGH ruler and
its thresholds are unchanged. Currency is deliberately not repaired in
this PR.**

C4 from `QUALITY_BAND_RULER.md` (#140), implemented as a dedicated
authority rule. The separation:

```
performance  →  coverage of the applicable factor set  →  authority
             →  LOW / MEDIUM / HIGH, or abstain
```

Short of authority Quality **abstains**. Not LOW, not neutral, not a
zero score, not a synthetic band — the honest state the signal already
had for *nothing readable*, now also reached for *not enough readable*.

---

## What was built

`app/domain/quality_coverage.py` — `QualityFactor` (the three factors,
**named** rather than counted, because #140 found the platform could
say how many it was missing and never which), `FactorStanding` and
`QualityCoverage`. Participation reuses #139's `SignalParticipation`
rather than inventing a second vocabulary for the same three states.

`QualityCoverage.may_band` is **completeness**, not a ratio floor:
every applicable factor read, or no band. #140 measured that every
partial rule — relative performance, a coverage floor, a breadth floor
— lets deleting a factor move the band's direction. Requiring the
whole applicable set leaves a deletion no direction to move.

The ruler is untouched and runs unchanged once authority is
established: `provider-quality@1` keeps fingerprint `3adc0fd3fd9f`,
and `BANDS`, `FACTORS`, `LARGE_CAP_THRESHOLD` and `CONFIDENCE` are all
asserted unchanged by test.

**The measured half survives the abstention.** `earned`, `available`
and `contributions` are all carried on a withheld signal, so the
platform can now say *passed the one factor we could read, which is
not enough to judge the business* — true, and previously unsayable.
`basis` names the missing factor.

## The acceptance states

| State | Result | |
|---|---|---|
| `1/1`, one of three applicable readable, passed | **no band** | Apple's shape |
| `0/1`, same coverage, failed | **no band** | and `earned` still differs |
| `2/2`, third applicable factor unread | **no band** | names the missing factor |
| `3/3` | **band, unchanged** | HIGH / MEDIUM / LOW exactly as before |
| genuinely two-factor applicable set at `2/2` | **band** | supported via `NOT_APPLICABLE` |
| any established factor deleted | **authority withdrawn only** | direction never moves |

The applicability model does support the smaller set: a factor marked
`NOT_APPLICABLE` leaves the expected denominator, so a two-factor
company is complete at `2/2`. No live company reaches that state yet —
nothing marks a per-factor inapplicability today — and the capability
is tested rather than inferred.

## Invariants, measured on the live corpus

**Intra-Quality factor deletion: 42 deletions across every company
with an authorised band, and 0 moved the band's direction.** Every one
withdrew authority instead.

**#139's single-signal deletion invariant still holds at 0** hardening
transitions.

## The corpus, and the silence

| | pre-stack `main` | #136→#140 + C4 |
|---|---|---|
| BUY | 11 | **0** |
| HOLD | 58 | **77** |
| SELL | 8 | **0** |

**Quality authorised: 0. Abstaining: 77.**

Nineteen transitions from pre-stack `main`, **every one a softening**:
eleven BUY→HOLD and eight SELL→HOLD. The six blocking specimens —
AAPL, GOOG, PG, PLTR, SBUX, TSLA — are HOLD rather than SELL, and are
pinned as regressions.

**The silence is total, and that is the point of landing this first.**
No security reaches `3/3` because
`market-cap-input-eligibility@1` makes the size factor inadmissible
for all 77 — so Quality can honestly assess none of them, the vote
loses coverage, and nothing is actionable.

This is not C4 failing. It is the platform stating, for the first
time accurately, that it cannot currently judge business quality —
because it cannot establish what currency a market capitalisation is
denominated in. The next slice establishes the denomination, the size
factor becomes readable, coverage returns to `3/3`, and banding
resumes under the same unchanged ruler.

**First make ignorance safe, then acquire more knowledge.** Landing
the acquisition repair first would have hidden whether these semantics
were sound; landing them first proves the system behaves honestly when
its evidence is poor.

## Rule and provenance

`quality-authority@1`, status **ARGUED**, fingerprint `4079e4af87d7`
over the completeness requirement. `provider-quality@1` untouched at
`3adc0fd3fd9f`. The ARGUED count moved 4 → 5.

A withheld band carries the rule that withheld it, exactly as
Momentum's abstention carries `momentum-input-eligibility@1` — so a
reader can see which rule decided the silence.

## `is_capped_by_unreadable_factors`

**Preserved, and its meaning has sharpened.** The signal no longer
*emits* a capped band — a company whose dividend cannot be read
abstains rather than banding MEDIUM — so the predicate now describes
why Quality withheld judgement rather than why an issued band
understates a business. Its wording is unchanged in this slice and is
the owner's noted follow-up.

## Not done

No currency repair, no change to acquisition, weights, directional
thresholds, the LOW/MEDIUM/HIGH ruler, the CIO gates or #139's kernel.

**Recorded and unsolved:** a one-factor *applicable* set would be
complete at `1/1` and authorised. Unreachable today, because nothing
marks a factor inapplicable; if per-factor applicability is ever
populated, that degenerate set needs the same absolute-breadth
treatment `decision-authority@1` already applies one layer up.
