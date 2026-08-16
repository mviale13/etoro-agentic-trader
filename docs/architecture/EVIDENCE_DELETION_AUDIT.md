# The evidence-deletion audit

**Status: audit only. No code changed, no weight, threshold, veto or
UNKNOWN semantic touched.**

#136 withdrew an unwarranted quality point and 99 new SELL vetoes
appeared. The reasoning offered was that the veto was what value and
momentum already demanded, and the quality point had been masking it.
This audit asks whether that reasoning covers **every** case in which
removing evidence hardens a call, or whether some of them are absence
accidentally behaving like evidence.

The answer is that both exist, they run in opposite directions, and
only one of them currently reaches the investor as a decision.

---

## 1. The signals and their epistemic states

Four signals reach the decision layer. Only three vote.

| Signal | States | Votes? | Score to the CIO |
|---|---|---|---|
| **Value** | CHEAP / FAIR / EXPENSIVE / UNKNOWN | yes, ×0.40 | 80 / 55 / 25 / None |
| **Quality** | HIGH / MEDIUM / LOW / UNKNOWN | yes, ×0.35 | 80 / 62 / 40 / None |
| **Momentum** | BULLISH / NEUTRAL / BEARISH / UNKNOWN | yes, ×0.25 | **none** |
| **Risk** | LOW / MODERATE / HIGH / SEVERE | no | 20 / 45 / 65 / 85 |

**UNKNOWN is reached by four different situations, and the vote cannot
tell them apart:**

1. *not measured* — the provider returned nothing;
2. *not admissible* — measured, but the translation is unwarranted
   (`momentum-input-eligibility@1`, `market-cap-input-eligibility@1`);
3. *not applicable* — a fund has no earnings to be priced against, a
   token has no business quality (`has_no_company`);
4. *insufficient coverage* — no factor was readable at all.

States 1–4 differ in what they say about the world. State 3 is a fact
about the *instrument*; state 1 is a fact about the *platform*. All
four produce the identical vote term.

## 2. What each state contributes

`CompanyCommitteeService.evaluate`:

```
score = 0.40·value + 0.35·quality + 0.25·momentum
BUY  ≥  +0.50        SELL ≤ −0.50        otherwise HOLD
```

The three score maps
(`company_committee_service.py:60-91`) are:

| | favourable | middle | adverse | UNKNOWN |
|---|---|---|---|---|
| value | CHEAP `+1` | FAIR `0` | EXPENSIVE `−1` | **`0`** |
| quality | HIGH `+1` | MEDIUM `0` | LOW `−1` | **`0`** |
| momentum | BULLISH `+1` | NEUTRAL `0` | BEARISH `−1` | **`0`** |

**Two conflations, both structural:**

- **UNKNOWN ≡ the middle band.** "We cannot tell" scores exactly what
  "the evidence says middling" scores. `0` is not a neutral position
  in a sum that also contains `−1`: it is strictly better than adverse
  and strictly worse than favourable.
- **No denominator.** The vote is a weighted **sum over a fixed
  divisor**, not a mean over available signals. Deleting a signal does
  not reduce a coverage term — it silently substitutes the middle
  value for the missing one.

There is no quorum: one readable signal produces a vote as
confidently as three. `SELL` is the only veto-eligible outcome, and it
is consumed at `artificial_cio.py:113` as gate **2 of 9**, ahead of
every absence check.

The CIO's own gates are, by contrast, **absence-aware and correctly
asymmetric**: `risk_score is not None and > max → REJECT`,
`quality_score is not None and < 35 → REJECT`. A missing score never
rejects; it stops progression (`quality_score is None → INVESTIGATE`,
`valuation_score is None → PREPARE`). *An unmeasured score is never a
reason to reject* is implemented correctly at that layer — and the
vote reaches REJECT before that layer's discipline applies.

## 3–5. Counterfactual deletion, measured

Method: build the signals, then delete **one otherwise-admissible
signal at a time** by forcing it to UNKNOWN, and record the
transition. Nothing else is altered.

### Recommendation layer — 576 deletions over a synthetic grid

| deleted | before → after | count | direction |
|---|---|---|---|
| quality | HOLD → **BUY** | 16 | **harder** |
| quality | HOLD → **SELL** | 2 | **harder** |
| value | HOLD → **BUY** | 2 | **harder** |
| value | HOLD → **SELL** | 16 | **harder** |
| value / quality | BUY or SELL → HOLD | 76 | softer |
| momentum | BUY/SELL → HOLD | 28 | softer |
| momentum | anything → harder | **0** | — |
| (all) | unchanged | 436 | — |

**36 of 576 deletions (6.3%) hardened the call, in both directions.**

Momentum can never harden a call, and this is arithmetic rather than
luck: a HOLD→BUY by deleting momentum needs a pre-deletion score in
`[0.25, 0.50)`, and the reachable value+quality sums are
`{0.75, 0.40, 0.35, 0.05, 0, −0.05, …}` — so the post-deletion score
is either already ≥ 0.50 or still far below it. **The margin is
exactly zero**: `CHEAP + HIGH + BEARISH = 0.40 + 0.35 − 0.25 = 0.50`,
which is BUY. Any momentum weight above 0.25 would open the path.

### Decision-state layer — 243 deletions

| deleted | before → after | count | direction |
|---|---|---|---|
| quality | PREPARE → **REJECT** | 3 | **harder** |
| value | INVESTIGATE → **REJECT** | 3 | **harder** |
| quality | PREPARE/RECOMMEND/REJECT → INVESTIGATE | 57 | softer |
| value | RECOMMEND → PREPARE, REJECT → … | 18 | softer |
| momentum | REJECT → INVESTIGATE/PREPARE | 6 | softer |
| (all) | unchanged | 156 | — |

**6 of 243 (2.5%) hardened, and every one of them landed on REJECT.
No deletion anywhere produced a RECOMMEND.**

### Live corpus — 202 deletions over the stored securities

**13 hardened**, in exactly two clusters:

| Cluster | Securities | Shape |
|---|---|---|
| delete `quality=LOW` → **BUY** | DIDIY, DV, LUNR, MSTR, ORSTED.CO, RIVN | `v=CHEAP q=LOW m=BULLISH`, 0.30 → 0.65 |
| delete `value=CHEAP` → **SELL** | ETOR, FLYW, GRE.MC, H2O.DE, IS7.DE, MBGL, PROX.BR | `v=CHEAP q=LOW m=BEARISH`, −0.20 → −0.60 |

## 4. Legitimate versus pathological

**The legitimate class — #136's shape, and it is provably the whole
SELL side.** Deleting a *favourable* signal reveals opposition the
remaining signals already carried. The maximum single adverse
contribution is `−0.40`, so **a veto mathematically requires at least
two adverse signals**. Every deletion-created SELL therefore has two
remaining signals summing past `−0.50` on their own:
`LOW + BEARISH = −0.60`, `EXPENSIVE + BEARISH = −0.65`.

No deletion-created REJECT exists in which a single adverse signal
carried the veto, and none can be constructed under these weights.
**The SELL side is #136-legitimate throughout, live and synthetic.**

**The pathological class — deleting *adverse* evidence manufactures a
BUY.** Six live securities become BUY when the platform forgets that
their business quality scored LOW. Nothing about the company changed;
one adverse reading was removed, and `0` replaced `−1`.

This is absence behaving as evidence in the strict sense: the
recommendation improved **because** the platform knows less. It is not
the mirror of #136 — #136 removed *unsupported support* and let real
opposition through, whereas this removes *real opposition* and lets an
unopposed case through.

**Both clusters are the same root cause seen from two sides**: the
vote is a sum in which UNKNOWN is scored `0`, and `0` is a *position*
on the same axis as `+1` and `−1` rather than an abstention.

## Containment — why the pathology has not reached a recommendation

The asymmetry is the audit's most important structural finding:

- The **SELL** path reaches `analyst_veto`, evaluated at gate 2,
  **before any absence check**, so a deletion-created veto becomes
  REJECT immediately.
- The **BUY** path must survive seven further gates, and deleting a
  signal also deletes its *score* — so `quality_score is None →
  INVESTIGATE` or `valuation_score is None → PREPARE` stops it. The
  six live BUY specimens are INVESTIGATE before deletion and
  INVESTIGATE after; the vote flips, the state does not.

**The containment is incidental, not designed**, and it rests on two
properties that nothing enforces:

1. **A band and its score are always deleted together.** They move
   together only because both derive from the same signal. Any future
   consumer supplying a score from one source and a band from another
   would break it — the grounded quality route (#81) already supplies
   a quality score from filings rather than from the provider triad.
2. **Momentum has no score and therefore no None-gate.** It is the one
   voting signal whose deletion removes a vote term while leaving
   every CIO gate satisfied. It is contained today *only* by the
   arithmetic margin above, which is exactly zero.

**A deletion-created BUY is nevertheless already investor-facing.**
`CompanyRecommendation` is rendered on the dossier as BUY / HOLD /
SELL. The six live securities publish a BUY under the counterfactual
even though the CIO state does not move — so the pathology is
contained at the *state* layer and not at the *surface*.

## What was not done

No weight, threshold, veto, gate or UNKNOWN semantic was changed, and
no repair is proposed here. Three candidate directions are recorded
for a future ruling, unranked and unbuilt:

- **Distinguish abstention from the middle band** — the two
  conflations in §2 are one decision, and it is the owner's: whether
  UNKNOWN should be an abstention (reducing a denominator) rather than
  a position scoring `0`.
- **Give the veto the same absence discipline the CIO already has.**
  Gate 2 is the only decision-bearing test that runs ahead of every
  absence check.
- **Name a coverage floor.** There is no quorum: one readable signal
  votes as confidently as three, and `available` — which the quality
  signal already computes — reaches no decision.
