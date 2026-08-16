# The decision kernel: direction separated from authority

**Status: built. `decision-authority@1`. No weight, directional
threshold, band, veto or gate was changed.**

The implementation of the separation #138 proved
(`DECISION_KERNEL_ALGEBRA.md`). UNKNOWN has stopped being a voting
position. A signal takes part in the direction only when it expresses
an analytical reading; whether the platform may *act* on that
direction is a second question with a second answer.

---

## What changed

**UNKNOWN cannot be looked up.** The three score maps are gone. In
their place, `_VALUE_DIRECTIONS`, `_QUALITY_DIRECTIONS` and
`_MOMENTUM_DIRECTIONS` contain only real readings — `CHEAP/FAIR/
EXPENSIVE`, `HIGH/MEDIUM/LOW`, `BULLISH/NEUTRAL/BEARISH`. A band
absent from its table is an **absence**, not a zero, and the type
system carries that: `SignalStanding.direction` is `int | None`, where
`None` means *did not speak* and `0` means *spoke, and said middling*.

**Three participation states** (`app/domain/decision_participation.py`):

- `PARTICIPATING` — expressed a reading. **A genuine NEUTRAL
  participates**, contributing zero to the direction and counting
  fully towards coverage.
- `EXPECTED_ABSENT` — applicable, and not established: unread,
  inadmissible or unknown. Stays in the expected set, so its absence
  lowers coverage. This is the whole mechanism by which ignorance
  withdraws authority instead of voting.
- `NOT_APPLICABLE` — the question does not apply. Leaves the expected
  set entirely, so it cannot lower coverage.

**Direction preserves the original weights and is not renormalised.**
`score = Σ standing.contribution` over participants at `0.40 / 0.35 /
0.25`. A survivor never gains authority from a neighbour's absence —
#138 measured that renormalising over survivors is what makes
forgetting look bullish (deleting the specimens' LOW quality moved the
direction from `+0.30` to `+1.00`). Arithmetically this is what the
vote always computed; what changed is that abstention is now visible
and acting on the result is asked separately.

**Two independent authority gates**, and neither is expressible as the
other:

| Gate | Constant | Protects against |
|---|---|---|
| relative coverage | `= 1.00` | a signal being deleted |
| participating signals | `≥ 2` | a degenerate expected set |

The second is deliberately **not** encoded as relative coverage. A
security with one applicable signal has 100% coverage by construction,
which is exactly how #138's model made a fund a BUY on momentum alone.

**A withheld direction survives structurally.** `CompanyRecommendation`
gained `direction` (what the evidence says) beside `recommendation`
(what may be acted on), plus `authority` and a
`lean_without_authority` property. The direction is **not** forced to
NEUTRAL when actionability fails — *the evidence leans bullish and we
do not hold enough of it* is a different statement from *the evidence
is balanced*, and before this they were the same word.

## Before → after, 77 securities

| | Before | After |
|---|---|---|
| BUY | 11 | **8** |
| HOLD | 58 | **61** |
| SELL | 8 | 8 |

**Three transitions, all softening**, and no security hardened:

| Security | | |
|---|---|---|
| NESN.SW | BUY → HOLD | bullish lean, coverage incomplete |
| NOVO-B.CO | BUY → HOLD | bullish lean, coverage incomplete |
| VOW3.DE | BUY → HOLD | bullish lean, coverage incomplete |

**Direction held but not actionable: 3** (all BUY leans). Under the
old kernel these were indistinguishable from conviction; they are now
HOLDs that can say what they lean towards and why they are withheld.

**Failed-authority reasons across all 30 non-actionable securities:**
relative coverage alone 17, relative coverage *and* absolute breadth
13. No security fails on breadth alone in this corpus — expected,
since a one-signal expected set requires a NOT_APPLICABLE, and the
corpus is read as `stock` throughout. The gate is nonetheless load-
bearing: the fund case is covered by test rather than by corpus.

**Participation per security:** 3 signals for 47, 2 for 17, 1 for 9,
none for 4.

## The invariant

**Counterfactual single-signal deletion over the live corpus:
13 hardening transitions → 0.**

The property is also proved exhaustively rather than sampled:
`test_no_single_deletion_increases_decisiveness` walks all 64 readings
× every established signal and asserts no deletion increases
decisiveness. `BUY → SELL` and `SELL → BUY` are separately forbidden
for every reading.

**Softening remains permitted and is tested as such.** `BUY → HOLD`
and `SELL → HOLD` are correct: a design that could never soften would
be retaining a conclusion after its evidence, which is why #138
restated the invariant over *decisiveness* rather than over
*positivity*.

The mechanism is structural rather than arithmetic: an actionable call
requires coverage of exactly 1.00, so **any** deletion drops coverage
below the gate and yields HOLD. There is no threshold to tune and no
case that squeaks through.

## The six specimens

`tests/test_decision_kernel_specimens.py` — the `xfail(strict=True)`
markers came off. They failed the suite *for passing unexpectedly*
once `decision-authority@1` landed, which is precisely the handover
the strictness existed to force; they are ordinary regressions now.
DIDIY, DV, LUNR, MSTR, ORSTED.CO and RIVN: deleting their established
LOW quality leaves HOLD unchanged, and can never manufacture BUY.

## Rule and provenance

`decision-authority@1`, status **ARGUED**, fingerprint `45b26f7f2a21`
over both constants — hashed together because they are one rule: a
call is actionable only if both hold. `signal-vote@1` keeps
`f2fdf881fe4f`; the weights and the ±0.50 thresholds are untouched and
asserted so by test. The ARGUED count moved 3 → 4.

`CompanyRecommendation.rules` now carries three entries, so a reader
can see which rule said what the evidence points at, which scored its
confidence, and which decided whether it could be acted on.

## No control-flow collision

The brief asked for a stop-and-report if the separation could not be
made without changing recommendation policy beyond the two gates.
**None was needed.** `analyst_veto` and `actionable_now` both key on
`company.recommendation` (`decision_evidence_builder.py:247,249`), so
withholding a direction withdraws the veto and the execution trigger
together, through the existing control flow. The nine CIO gates are
untouched, and the gate-ordering asymmetry #137 identified is
unchanged — still open for a ruling, and now with fewer absence-driven
calls reaching it.

## What was not done

No change to provider acquisition, quality scoring, momentum bands,
valuation thresholds, signal weights or the BUY/SELL thresholds. The
CIO's gates and their ordering are untouched.

**Recorded and unsolved:** `lean_without_authority` reaches no
surface — the dossier still renders `recommendation` alone, so the
three withheld leans are currently invisible to an investor. Making
that visible is a presentation slice with its own product story, and
#126's ruling applies: it should appear once, owned by one layer.
