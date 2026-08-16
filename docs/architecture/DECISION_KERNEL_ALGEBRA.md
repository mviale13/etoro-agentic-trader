# The decision kernel: direction is not authority

**Status: research and design. No aggregation was changed. The six
specimens are pinned; nothing else in this slice touches behaviour.**

`EVIDENCE_DELETION_AUDIT.md` found that the vote scores UNKNOWN as
`0`, so absence sits on the same axis as `+1` and `−1` and deleting
adverse evidence can manufacture a BUY. This slice asks what the
weighted sum was *meant* to mean, models four aggregation semantics
against the corpus, and tests the invariants the owner set.

The headline: **the owner's two-dimensional hypothesis is confirmed
and one part of the leading design is measurably unsafe.**

---

## 1. What the weighted sum was intended to mean

`UNKNOWN: 0` was explicit in the first commit
(`fd42194`, 29 July) — a declared entry in each score map, not a
`.get` default. So the vote's author did decide it.

**The signals then decided the opposite, and the vote never caught
up.** The domain language that arrived later says so directly:

- `QualitySignal.contributions` — "Empty where nothing could be read
  — **which is not a score of zero**, and the band is `UNKNOWN` there
  rather than `LOW`."
- `QualitySignal.rule` — `None` "where nothing was banded: **an
  UNKNOWN produced by absence had no meaning assigned at all**."
- `QualitySignal.available` — "counts only the factors this company's
  data allowed a look at, so it is **a statement about the reading
  rather than about the business**."

The quality signal already implements abstention with coverage
internally: an unreadable factor is dropped from `counted`, `earned`
and `available` are carried apart, and `next_band_needs` explains a
band capped by unreadable data. **The kernel is the last layer still
treating absence as a position**, and it contradicts the vocabulary of
the objects it consumes.

That is the intent finding: this is not a policy the platform argued
for and would defend. It is a July default that the platform's own
language has since outgrown.

## 2. Four aggregation semantics, measured

64 signal readings × single-signal deletion = 144 counterfactuals.
No weight or threshold was tuned; `0.40 / 0.35 / 0.25` and `±0.50` are
constant throughout.

Invariants, **restated in terms of decisiveness** (see §3 for why):

- **I1′** deleting *adverse* evidence must never reach BUY;
- **I2′** deleting *favourable* evidence must never reach SELL;
- **I3** any deletion must never increase decisiveness.

| Model | I1′ | I2′ | I3 | neutral ≠ unknown |
|---|---|---|---|---|
| **M0** current, UNKNOWN = 0 | 2 | 2 | 4 | **0 / 48** |
| **M1** abstain, full denominator | 2 | 2 | 4 | **0 / 48** |
| **M2** abstain, renormalised | 11 | 11 | 34 | 48 / 48 |
| **M3** renormalised + coverage ≥ 0.60 | 5 | 5 | 16 | 48 / 48 |
| **M3** renormalised + coverage ≥ 0.75 | 1 | 1 | 4 | 48 / 48 |
| **M3** renormalised + coverage = 1.00 | **0** | **0** | **0** | 48 / 48 |

Three results matter more than the ranking.

**M1 is arithmetically identical to M0.** Every transition, every
violation, every count. Contributing `0` to a fixed denominator *is*
contributing nothing — so "abstention with the original denominator
preserved" changes only what the platform can *say*, never what it
decides. It is a necessary semantic step and it is not a repair.

**M2 makes the pathology substantially worse** — I3 violations go
4 → 34. Renormalising over survivors amplifies them: deleting the LOW
quality from the six specimens moves the direction from `+0.30` to
`+1.00`, a *maximally* bullish reading produced entirely by
forgetting. Renormalisation without a coverage requirement is the
worst of the four options and should not be adopted alone.

**Only a coverage requirement fixes anything**, and only at 1.00 is it
clean. At 0.75 a single case survives — deleting momentum leaves
coverage exactly at the floor.

## 3. Two of the invariants, as stated, are unsatisfiable

Measured against the literal wording, **every model including the best
one violates I1 and I2** — 11 violations each under M3@1.00. The cause
is not the models.

*"Removing established adverse evidence must never improve an
investor-facing recommendation"* forbids `SELL → HOLD`. But if the
adverse evidence that produced a SELL is genuinely gone, HOLD is the
honest answer; keeping the SELL would be retaining a conclusion after
its evidence. Any aggregation that responds to evidence at all must be
allowed to soften.

**The defensible content of both is I3.** Deleting evidence may only
ever make the platform *less* decisive, never more — in either
direction. I1′ and I2′ above are the directional halves of that, and
M3@1.00 satisfies all three at zero.

This matters for the eventual rule: written as stated, I1 and I2 would
pin the kernel into never softening, which is a worse defect than the
one being repaired.

## 4. Neutral ≠ unknown, and applicability ≠ ignorance

**I4 — neutral versus unknown.** M0 and M1 cannot distinguish them in
**any** of 48 cases: FAIR and UNKNOWN produce identical scores,
identical coverage, identical everything. M2 and M3 distinguish all
48, because a measured middle band participates in the denominator
while an absence does not. **Only a renormalising model can express
the distinction the domain language already claims.**

**I5 — applicability, and the trap in the leading design.** Modelled
as the owner proposed — NOT_APPLICABLE excluded from the expected set
rather than treated as missing — a fund whose only applicable signal
is momentum reads:

| Model | outcome |
|---|---|
| M0 / M1 | **HOLD**, coverage 1.00 |
| M2 | BUY, coverage 0.25 |
| **M3 (any floor)** | **BUY, coverage 1.00** |

**A fund becomes a BUY on momentum alone, at "full" coverage**, and
today's kernel is accidentally safe from this only because `0.25 <
0.50`. Relative coverage over a one-signal expected set is 100% by
construction, so excluding NOT_APPLICABLE from the denominator hands
authority to a single surviving signal.

The correction is that **coverage needs two conditions, not one**:

- **relative** — participating ÷ applicable, which protects against
  deletion;
- **absolute** — a floor on how much evidence participates at all,
  which protects against a degenerate expected set.

Neither substitutes for the other, and the leading design as sketched
carries only the first.

## 5. Direction versus authority, quantified

Over the 64 readings under M3@1.00:

| evidence direction | coverage | issued | count |
|---|---|---|---|
| BUY | adequate | BUY | 5 |
| BUY | **inadequate** | HOLD | **9** |
| SELL | adequate | SELL | 5 |
| SELL | **inadequate** | HOLD | **9** |
| HOLD | either | HOLD | 36 |

**18 of 64 readings have a clear evidence direction the platform is
not entitled to act on.** Today that population is invisible: it is
merged into HOLD, indistinguishable from genuine equivocation. The
owner's hypothesis is confirmed — the scalar is carrying two
questions, and 28% of the readings are exactly where they differ.

## 6. The cost, on the live corpus

77 securities. Signals actually participating: **3 for 47, 2 for 17,
1 for 9, none for 4.**

| Model | BUY | HOLD | SELL | actionable |
|---|---|---|---|---|
| M0 / M1 (today) | 11 | 58 | 8 | 19 (25%) |
| M2 | 16 | 44 | 17 | 33 (43%) |
| M3 @ 0.60 / 0.75 | 16 | 53 | 8 | 24 (31%) |
| **M3 @ 1.00** | 8 | 61 | 8 | **16 (21%)** |

The only invariant-clean model is also the most conservative: 16
actionable against today's 19. That is the trade the owner is being
asked to price — **not a tuning question**, because moving the floor
to make the number larger is exactly the "tune it until the outputs
look nice" this slice was told not to do.

## 7. The six specimens, under each model

`value=CHEAP, quality=LOW, momentum=BULLISH`, deleting the established
LOW quality:

| Model | before | after | |
|---|---|---|---|
| M0 / M1 | HOLD | **BUY** | violates the pin |
| M2 | HOLD | **BUY** (score `+1.00`) | violates the pin |
| M3 @ 0.60 | HOLD | **BUY** | violates the pin |
| M3 @ 0.75 | HOLD | HOLD | holds |
| M3 @ 1.00 | HOLD | HOLD | holds |

Pinned in `tests/test_decision_kernel_specimens.py`: six baseline
tests asserting today's LOW/HOLD reading (green, so the baseline
cannot drift), and six invariant tests marked **`xfail(strict=True)`**.
The strictness is deliberate — when a design makes them pass, the
suite fails for *passing unexpectedly*, forcing whoever lands it to
return and convert them into ordinary regressions rather than letting
the repair go silently untested.

## 8. Gate ordering

The audit found SELL vetoing at gate 2 of 9 while BUY passes seven
further epistemic gates. Nothing here changes it, and the
recommendation is the owner's own: **if the asymmetry is retained it
must become an explicit, tested investment policy** rather than
control flow that happens to read that way.

The measured argument for retaining it: a veto expresses *this case
should not proceed*, and proceeding is the action with the
irreversible consequence. The measured argument against: gate 2 is the
only decision-bearing test in the platform that runs ahead of every
absence check, so it is also the only place where an absence-driven
conclusion reaches an investor unfiltered — which is precisely how the
deletion pathology reaches REJECT while its mirror is contained.

Either way it should carry a named rule and a fingerprint, as
`veto-sell@1` already does for the mapping but not for the *ordering*.

## What this slice recommends, and does not build

**Recommended shape** — M3 with two coverage conditions:

1. signals participate only when they express a view; UNKNOWN
   abstains; a measured NEUTRAL participates as neutral;
2. NOT_APPLICABLE leaves the expected set rather than being missing
   from it;
3. direction is the renormalised score over participants;
4. authority is **relative coverage AND an absolute participation
   floor** — §4 shows why one alone is unsafe;
5. a direction the platform may not act on is *reported as such*,
   not merged into HOLD.

**Open for the owner, and deliberately not decided here:** the value
of the relative floor (only 1.00 is invariant-clean, at a cost of 3
live actionable securities); the absolute floor's unit (weight, or a
count of signals); whether "direction known, authority insufficient"
becomes a distinct investor-facing state or a qualifier on HOLD; and
whether the gate asymmetry is retained as policy.

No aggregation code was touched. The specimens are pinned.
