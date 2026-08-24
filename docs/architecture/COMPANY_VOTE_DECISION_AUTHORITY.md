# Company Vote Decision Authority

**Status: direct gates removed and accepted. Path C open.** Owner
rulings, 2026-08-24.

**The precise claim, used everywhere in this repository:**

> The company vote's SELL and BUY directions no longer directly reject
> or authorize a case. Its confidence remains decision-bearing through
> `evidence_score`; that residual changes one live blocker, can reach a
> state threshold, and is **not** accepted as the final contract.

That is deliberately weaker than the sentence this document first
carried. The vote is **not** now descriptive: its *direction* is, its
*magnitude* is not. Momentum has **not** lost all decision authority —
it has lost the two direct gates.

The owner's behavioural ruling this slice implements:

> A one-session price move may remain visible as a descriptive momentum
> signal. It may not, by itself or through the composite company vote:
> reject an investment thesis; authorize a recommendation; claim that
> evidence is more complete; manufacture an analyst veto; or alter a
> capital envelope.

This is the volatility ruling of 2026-08-21 applied one layer up.
**Market behaviour may inform risk, timing and eventual sizing without
becoming a judgment about business quality** — a boundary this slice
moves toward and does not yet reach, because the third clause
(*claim that evidence is more complete*) is exactly what Path C still
does.

---

## What was found

`CompanyCommitteeService` computes a weighted direction over three
bands — value 0.40, quality 0.35, momentum 0.25, each ±1 by band — and
calls it BUY at `≥ +0.50`, SELL at `≤ −0.50`. That single number had
**three decision-bearing paths**:

| | Mapping | Where it landed |
|---|---|---|
| **A** | `SELL → analyst_veto` | `REJECT`, the **first live branch** of the cascade, ahead of every score |
| **B** | `BUY → actionable_now` | the **final gate** before `RECOMMEND` |
| **C** | vote confidence → `evidence_score` | three evidence gates, and conviction |

Momentum contributes ±0.25, so it moves the score by 0.50 across its
range — exactly the width of both thresholds. **A one-session provider
price move was decisive at both ends.**

The motivating case: AMD moved `PREPARE → REJECT` on a **−4.28%**
session with quality, valuation and risk byte-identical across all
three recorded decisions. The blocker read *"Blocked by a specialist
analyst's veto: it read a risk at the level that stops a case
outright."* No analyst had spoken, and no risk had been read. The
deciding number carries an `ASSUMED` warrant, which the platform's own
registry pairs with `GATES_A_DECISION`.

---

## Stage 0 — measured before anything was changed

Read-only over the complete held corpus at cycle `2c5986e6ea43`. Zero
provider calls, zero model calls, no store writes.

### The cliff

With value `EXPENSIVE` and quality `MEDIUM` fixed — AMD's own, unmoved —
the decision turned on **one hundredth of a percentage point**:

| session | momentum | vote | outcome |
|---|---|---|---|
| −0.49% | NEUTRAL | −0.40 | HOLD → PREPARE |
| **−0.50%** | **BEARISH** | **−0.65** | **SELL → REJECT** |

### Who exercised which authority

- **A (veto)** — 2 securities, both **candidates**: AMD and UUUU. No
  holding was vetoed. AMD's veto was decided by the momentum band alone.
- **B (trigger)** — 4 held securities voted BUY: AZN, DIS, BNP.PA,
  UMI.BR. The flag was **decided by the momentum band** for ADBE,
  UMI.BR, CYD and MSFT.
- **C (confidence)** — removing the vote's confidence from
  `evidence_score` moves 7 of 19 securities across the 75 gate.

One finding worth recording on its own: **SPCX votes SELL and is not
vetoed**, because its quality band is absent and the coverage gate
withholds authority. A security was protected from automatic rejection
by holding *less* evidence.

### Contract comparison

Every option produces the **same two movements**, and both are the veto:

| | movements | held securities moved |
|---|---|---|
| 1 · direction *and* confidence removed | AMD `REJECT→PREPARE`, UUUU `REJECT→INVESTIGATE` | **0** |
| 2 · direct gates removed | identical | **0** |
| 3 · SELL veto removed only | identical | **0** |

`DIS` and `BNP.PA` keep `RECOMMEND`; their BUY vote was not
load-bearing. Digital assets are untouched — a token returns through
`DigitalAssetDecision` before the equity cascade is reached at all, and
that path reads neither flag.

### The modelling error that mattered

Removing the BUY mapping is **not** the same as leaving `actionable_now`
permanently `False`. Modelled naively, `not actionable_now → PREPARE`
fires for every equity and **`RECOMMEND` becomes unreachable** — BNP.PA
and DIS lose their course. The gate must be *removed*, not starved.
Measured both ways; the table above is the correct model.

---

## What was built

Two gates deleted from `decision-gates`, re-versioned **@3 → @4**:

- `analyst_veto → REJECT` — gone, with `BlockerKind.ANALYST_VETO`,
  the `analyst_veto` field, and the `veto-sell` rule.
- `not actionable_now → PREPARE` — gone, with
  `BlockerKind.EXECUTION_TRIGGER`, the `actionable_now` field,
  `_actionable_now`, and the `actionable-buy` rule.

**Nothing replaces the execution trigger.** No technical-analysis
trigger is introduced. A case that satisfies quality, evidence,
valuation, risk and portfolio fit is recommended on those alone —
noting that `evidence` there still carries the vote's magnitude.

The vocabulary is *removed*, not left unread: `DecisionEvidence` refuses
either field at construction, so a caller that still sets one fails
rather than being quietly ignored. `AnalystEvidence.veto` goes with
them — a veto nothing can act on is dead vocabulary that reads as live.

**What is untouched**: value, quality, momentum and risk are all still
measured, banded, evidenced and rendered; the committee still states its
direction and summary; conviction still averages five families; every
genuine gate still fires; and no policy constant moved.

**And what is untouched that should not be read as settled**: Path C.
Value, quality and momentum no longer stop a case *through the deleted
direct branches*; they remain capable of affecting the evidence gates.

---

## What was *not* removed, and why

**Path C — the vote's confidence still reaches `evidence_score`.** This
is stated plainly rather than glossed: *the authority is not removed.*

`evidence_score = (cognitive_confidence + vote_confidence) / 2`, and
`vote_confidence = 50 + |score| × 50` — it rises with the **magnitude**
of the vote in either direction. So a large one-session move still
raises the evidence score. AMD's went **71 → 83** on the day it was
vetoed: the platform reported the case as *better evidenced* because
the price fell.

It is left in place because removing it is worse. `cognitive_confidence`
is `(portfolio + market + risk) / 3` — **entirely account-level**.
Dropping the company term leaves `evidence_score` identical for every
security (85 across the whole book today), making three evidence gates
security-blind. That is the defect shape `CLAUDE.md` warns about, and
replacing it needs a policy ruling on what evidence coverage means.

**Measured residual**: no security's *state* moves through this path,
because every one is blocked at an earlier gate. One security's
*blocker* does — MSFT's moves between `missing_evidence` and
`risk_gate`. And the state crossing is **reachable**, not impossible:
at the observed cognitive confidence the 75 gate sits at `|score| ≈
0.30`, and momentum moves `|score|` by 0.25. MSFT sits one gate away.

**Recommended next**: a genuine evidence-coverage measure.
`DecisionAuthority.relative_coverage` and `QualityCoverage.earned /
available` already exist and are security-specific. Wiring one in is a
policy decision, not a repair.

---

## Verified outcome

Against the patched cascade, over the live corpus:

```
movements: 2   AMD REJECT->PREPARE   UUUU REJECT->INVESTIGATE
held securities moved: 0
DIS RECOMMEND · BNP.PA RECOMMEND — unchanged
digital assets — separate path, untouched
state moves on momentum alone: 0   (was 1: AMD)
blocker moves on momentum alone: 1  (MSFT, the path-C residual)
```

No security lost a course: AMD gains one (`none → hold`), UUUU gains one
(`none → research`). No capital envelope moved — envelopes attach to
capital-asking courses, and no security gained or lost one.

## Boundaries

No order-capable path is introduced. No valuation, quality, risk,
portfolio-fit, capital-envelope or allocation-policy threshold changed.
No new timing model. The digital-asset contract is untouched by
construction rather than by coincidence.

---

## Owner ruling — 2026-08-24

Recorded after the Stage 0 measurement and the corpus verification
above, on PR #248.

**Accepted.**

- **Direct-gate removal.** `SELL → analyst veto` and
  `BUY → execution trigger` are removed. Neither is to be restored or
  replaced.
- **Deletion of the unreachable vocabulary** — the `DecisionEvidence`
  fields, `BlockerKind.ANALYST_VETO`, `BlockerKind.EXECUTION_TRIGGER`,
  the `veto-sell` and `actionable-buy` rules, `_actionable_now` and
  `AnalystEvidence.veto`.
- **`decision-gates@4`**, re-fingerprinted.
- **The two corpus movements**: AMD `REJECT → PREPARE` and
  UUUU `REJECT → INVESTIGATE`.
- **Zero held movements and zero lost courses.**

**Explicitly not accepted.**

- **Path C is not the final evidence-sufficiency contract.** The
  company vote's magnitude-derived confidence remains a term of
  `evidence_score`, and it is accepted only as a *residual carried
  forward*, never as a settled measure of how well a security is
  evidenced.
- **Path C is not to be "fixed" by dropping the company term.** Doing
  so would leave `evidence_score` built from account-level confidence
  alone and identical across every security, which trades one wrong
  answer for a worse one.
- **No replacement formula is to be invented in this PR.**

**Next.** A **security-specific evidence-coverage measurement** is the
next policy slice: research only, offline, and stopping for a ruling
before anything is implemented. It must replace magnitude-derived
confidence without making every security inherit the same account-level
score and without treating missing information as negative business
evidence.

**Standing.** Momentum remains visible. No technical-analysis trigger is
introduced, in this slice or the next.
