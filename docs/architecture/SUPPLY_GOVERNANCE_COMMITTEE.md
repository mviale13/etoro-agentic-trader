# Committee #2, and the first two-committee matrix

**Status: accepted, built, decision-neutral.** The deliverable is not
*two committees* — it is the first empirical dataset showing how
independent committee judgments coexist.

---

## 1. Selecting the committee from evidence

Nineteen investor questions were already discovered in
`crypto_questions.py`. They were measured against the live eight-asset
corpus rather than chosen:

| question | ASK | declined | undet. | bound demands | readiness |
|---|---:|---:|---:|---|---|
| market_robustness | 8 | 0 | 0 | 3/3 | scorable_now |
| liquidity | 8 | 0 | 0 | 2/3 | not_ready |
| **supply_and_dilution** | **8** | **0** | **0** | **4/5** | **visible_not_scored** |
| economic_activity | 6 | 1 | 1 | 1/2 | visible_not_scored |
| capital_committed | 5 | 2 | 1 | 1/1 | visible_not_scored |
| protocol_capture | 2 | 5 | 1 | 1/2 | *Fee Capture owns this* |
| holder_value_accrual | 6 | 1 | 1 | 2/3 | *Fee Capture owns this* |
| venue_activity | 1 | 6 | 1 | 2/3 | visible_not_scored |
| monetary_scarcity | 1 | 6 | 1 | 2/4 | visible_not_scored |
| *(ten others)* | | | | 0–1 bound | not_ready |

Then the criteria that actually eliminated candidates:

- **`market_robustness`** — scorable, and the one thing Asset Quality
  already scores. Its answer is a *magnitude* against a threshold, which
  is banding by another name.
- **`liquidity`** — S5 measured that volume over market cap is not
  liquidity (it ranks BTC 158th of 233 while BTC trades $14.8bn a day).
  Explicitly not ready.
- **`capital_committed`** — 7 of 8 carry a TVL reading, so evidence was
  not the problem. It failed on two other criteria: the readings come
  from the **same provider and the same acquisition path as Fee
  Capture's fees**, and the answer is inherently a magnitude
  ($70m for ADA against $42bn for ETH), so any binary needs a threshold.
  A disguised second view of activity.
- **`venue_activity`, `monetary_scarcity`, `settlement_dependency`,
  `sequencer_economics`, `competitive_position`** — one applicable asset
  each. No contrast.

**`supply_and_dilution` won**, narrowed to the part of it that is
answerable now: *what would it take to change the rule that creates this
token's new supply?* It is applicable to all eight, its evidence is
primary chain state rather than vendor data, it is economically
unrelated to fees, and — the decisive property — **its structural answer
cannot be read as a grade**, because S5.3 already measured that BTC, ADA
and SOL are equally explicit and equally projectable, and parked the
magnitude that separates them outside quality.

---

## 2. What the committee owns

```text
question             what would it take to change the issuance rule
applicability rule   issues-to-secure-itself@1
verdicts             CONSENSUS_BOUND | GOVERNANCE_SET
evidence             MechanicalIssuance, read from primary surfaces
eligibility          Model C gates, asked of a rule
```

**Both verdicts are positive findings**, which is what makes this
committee unlike Fee Capture rather than a second view of it. Fee
Capture answers a presence and its negation; every asset reaching a
verdict here *has* a rule, and the answer says who can change it.
Sharing Fee Capture's vocabulary would have said something false about
what the answer means.

The applicability rule is the committee's own, in economic terms: a
token whose protocol **creates new supply to pay for its own security**
has an issuance rule as part of what the token is. It reads the
archetype's *capabilities* rather than its name, so an asset that is
several things at once is asked if any of what it is issues — which is
why Hyperliquid is asked despite being a venue.

**No model is asked anything.** Fee Capture needs a judge because
weighing a figure against a stated mechanism is a judgment; here the
judgment is an eligibility rule over primary evidence, and a model
applying it would be an unchecked lookup. That the protocol
accommodates a committee with no model seam is a finding.

---

## 3. The measurement that changed the design

The first implementation refused every asset. The clause was
`EvidenceStanding.ESTABLISHED`, and **every issuance rule on this
platform stands at `CLAIMED`** — BTC, ADA and SOL alike, all read from
canonical surfaces, all with every parameter sourced, all reproducing.

S1's corroboration vocabulary was built for vendor claims, where a
second independent source is real evidence. A chain's own issuance
parameters have no second source and cannot acquire one: **the chain is
the authority.** Requiring `ESTABLISHED` would not have raised the
standard, it would have made the committee permanently silent about the
strongest evidence the platform holds.

S4.5 had already ruled on this — *where a fact came from is a second
axis, never a second standing* — so the eligibility rule is S5.1's Model
C gates asked of a rule instead of a figure: primary authority, canonical
surface, every constant read rather than remembered, a versioned
reading, a path that re-runs, and an established mutability. **A clause
that cannot be evaluated fails.** A test asserts `EvidenceStanding`
appears nowhere in the committee, so the gate cannot drift back.

One distinction this rests on, from S5.2: Bitcoin's issuance *rule*
reproduces 89 of 89 daily intervals while its historical *total* stays
unresolved. The rule is right and the composition is unitemised — and
this committee asks about the rule.

**And the exclusion that had to be measured:** the committee never reads
a vendor supply figure. A vendor's `total_supply` is the protocol
maximum for 83 of 145 capped assets, which puts Cardano at 100% emitted
where its own ledger says 86.2%. A committee reasoning from that would
be confidently wrong about the quantity it exists to describe.

---

## 4. The two-committee matrix

Read from the store, not recomputed. **Not scored, and deliberately not
summarised.**

| asset | Fee Capture | | Supply Governance | |
|---|---|---|---|---|
| | posture | verdict | posture | verdict |
| BTC | known_not_applicable | — | **answered** | consensus_bound |
| ETH | answered | mechanism_evidenced | evidence_insufficient | — |
| SOL | answered | mechanism_evidenced | **answered** | governance_set |
| ADA | answered | no_mechanism_evidenced | **answered** | governance_set |
| HYPE | execution_unavailable | — | evidence_insufficient | — |
| ARB | answered | no_mechanism_evidenced | evidence_insufficient | — |
| 1INCH | answered | no_mechanism_evidenced | known_not_applicable | — |
| TAO | applicability_unknown | — | applicability_unknown | — |

| asset | FC confidence | FC evidence | SG confidence | SG evidence |
|---|---|---:|---|---:|
| BTC | — | 3 | multiple_observations | 8 |
| ETH | multiple_observations | 5 | — | 0 |
| SOL | multiple_observations | 5 | multiple_observations | 9 |
| ADA | multiple_observations | 3 | multiple_observations | 11 |
| HYPE | — | 11 | — | 0 |
| ARB | multiple_observations | 3 | — | 0 |
| 1INCH | multiple_observations | 3 | — | 0 |
| TAO | — | 1 | — | 0 |

Every combination the ruling asked to observe is present:

- **both answer** — SOL, ADA, in unrelated vocabularies
- **one answers, one abstains** — ETH, ARB (FC answers), BTC (SG answers)
- **opposite applicability** — **BTC and 1INCH swap sides.** Fee Capture
  declines BTC and asks 1INCH; Supply Governance asks BTC and declines
  1INCH. This is the single clearest evidence that the two are not one
  question asked twice.
- **both abstain for different reasons** — HYPE: the machinery did not
  run for one, the evidence could not answer the other
- **both abstain for the same reason** — TAO, and it is the same reason
  because neither committee can invent an economic role
- **different evidence coverage** — HYPE 11 against 0; ADA 3 against 11
- **structurally different verdict combinations** — ADA is
  `no_mechanism_evidenced` *and* `governance_set`

**None of this is agreement or disagreement.** ADA receiving a negative-
sounding answer from one committee and a neutral-sounding one from the
other means exactly those two things and nothing about the asset.

---

## 5. What became visible only because two committees exist

Recorded as findings for the next slice. **Not solved here**, because
none of them stops Committee #2 working.

1. **`Confidence` saturates.** The vocabulary was calibrated on Fee
   Capture's evidence shape. Supply Governance emits at least five
   findings per answered asset, so BTC's 8, SOL's 9 and ADA's 11 all
   land on `MULTIPLE_OBSERVATIONS`. The count is honest and the band is
   blind to it. Fixing it means deciding what a further band would
   *mean*, which no committee has earned.

2. **The model seam is per-committee, and nothing says so.** Fee Capture
   reads `MOVRVEST_COMMITTEE_JUDGMENT` and reports
   `execution_unavailable` when it is off; Supply Governance has no
   model and always answers. Two committees whose availability is
   governed by different switches now sit in one matrix, and a reader
   cannot tell from the matrix which absences are switchable.

3. **`execution_unavailable` and `evidence_insufficient` are not
   comparable across committees.** HYPE is unavailable for one and
   insufficient for the other; both are "no answer", and they are
   different facts about different machinery.

4. **A committee's evidence door is its own problem.** Fee Capture reads
   a stored protocol-fundamentals door; Supply Governance needed a new
   cached issuance door built for it. There is no shared notion of *what
   has been acquired for committee N*, so `movrvest acquire` does not
   know it should fill the issuance cache.

5. **The abstention vocabulary may be too small for a second
   committee.** `INSUFFICIENT_EVIDENCE` covers both *the protocol has no
   such rule* and *the rule exists and we cannot read it* — ARB and ETH
   respectively. PR #114 predicted a committee would eventually need a
   reason the framework cannot derive; this is that committee, and the
   distinction is currently carried only in the abstention's prose.

6. **No surface shows the matrix.** `movrvest judgment-history` prints
   each committee in turn, which is correct and is not the same as
   showing a reader how two judgments about one asset sit together.
   Whether it *should* is the question the next slice is meant to
   decide.

---

## 6. What was deliberately not built

No aggregation, no weighting, no agreement percentage, no
favourable/adverse mapping, no overall score, no recommendation, no
thesis, no portfolio coupling, no LLM synthesis across committees.

A test asserts that no record, transition or registry offers
`agrees_with`, `combined`, `consensus`, `aggregate`, `weight`,
`priority`, `rank` or `score`. The registry is a tuple and a lookup —
earned by a concrete failure (with two committees the history surface
would have shown one and stopped) and given nothing else, because the
moment it offers priority, every consumer downstream can build an
aggregate on it and call the aggregate earned.
