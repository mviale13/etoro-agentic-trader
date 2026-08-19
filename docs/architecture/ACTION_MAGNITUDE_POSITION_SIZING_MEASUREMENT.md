# Action magnitude: what a capital envelope can rest on today

**Status: research. 2026-08-19. Nothing implemented, no decision
altered, no order constructed.** The follow-on #219's ruling reserved:
whether existing portfolio, market, risk and decision evidence can
support a deterministic Capital Action Envelope for OPEN, ADD and
REDUCE — without conviction, and without invented precision. Stage 1
ran offline over the #219 recorded cycle's own captured evidence with
every HTTP transport patched to raise; stage 2 is a synthetic
scenario matrix shaped like the real data contract; the report carries
normalized ratios only — no balance, account identifier or absolute
amount appears anywhere.

## Conclusion

# B. MECHANISM READY, OWNER RISK POLICY REQUIRED

**The capacity mechanism exists and is computable now — and capacity
is not yet position size.** From held data alone the platform can
produce, deterministically and monotonically, the **PortfolioCapacityCeiling**:
every holding's present weight; funding room above the cash target;
per-security concentration room against the single-position cap;
crypto class room; and, for an overweight holding, the
compliance-reduction *floor*. The fifteen-scenario matrix passed every
required monotonicity property, and conviction was not an input
anywhere.

**What the mechanism does not establish is a responsible initial
position or incremental ADD size.** An unheld equity under a 20%
single-position cap has up to 20% of concentration *capacity* — and
nothing measured here says 20% is an appropriate OPEN magnitude. The
final **CapitalActionEnvelope** is a smaller, owner-policy-bound
consideration *inside* that capacity:

> final envelope = min( portfolio capacity ceiling · evidence ceiling ·
> STANDARD_INITIAL_WEIGHT for OPEN · MAX_ADD_WEIGHT_CHANGE for ADD ·
> any operative drawdown or staleness ceiling )

and the two course-level parameters do not exist, so **broad-evidence
OPEN and ADD are also unbounded in action terms today** — computable
capacity, no position-size contract.

**What is missing is not engineering — it is eight owner decisions**
(§6), led by one this measurement did not expect to find: **the
platform has two independent policy sources, and the same portfolio is
non-compliant under one and compliant under the other.** Until the
owner names the authoritative source and supplies the parameters,
every final envelope must remain NONE, and OPEN/ADD stays what #219's
ruling made it — a course to consider, never a bounded instruction.

---

## 1. Stage 0 — what exists, and the finding that reframes it

### Two policy sources, unreconciled

| | source | who reads it |
|---|---|---|
| A | `config/policy.yaml` — risk profile, four allocation targets, `max_single_position` 15, `max_crypto` 20, rebalance threshold; **no `max_drawdown` key** | **only `movrvest decide`**, which also hashes it as a policy version |
| B | `data/investor_strategy.json` via `investment_policy_mapper` | **the entire Brain/executive path** |

Path B's mapper **hardcodes the stock, ETF and crypto allocation
targets to `0.0`** — only the cash target is real — and its *code*
carries two dangerous defaults: `maximum_single_position_pct` missing
⇒ **100.0, silently** (a missing concentration limit becomes no limit
at all), and `maximum_crypto_pct` missing ⇒ 0.0. **The live strategy
file does not exercise those defaults** — it explicitly sets
`maximum_crypto_pct: 65`, `maximum_single_position_pct: 20`,
`target_cash_pct: 5` — so the defaults are latent hazards, never the
live reading, and must not be substituted into any comparison. Path B
has no version or hash mechanism; path A has one, on the path that
does not feed the executive. And **the live strategy file carries
`status: draft`** — a draft strategy cannot be called approved or
authoritative without an owner ruling, and a draft cannot authorize a
capital envelope.

**No sizing contract can be written until the owner names the
authoritative source.** This measurement used path A's constraint
values as the illustrative policy and says so at every use.

### The field-by-field verdict (each traced to its code boundary)

**Admissible for magnitude, today**: per-position `market_value_usd`
with `PortfolioSnapshot.total_value` and `weight_pct` (gate on
`total_value > 0`; **aggregate by `instrument_id`** — eToro reports one
row per trade, and a 20.0% + 0.5% split once read as a compliant
20.0%); `allocation.cash` against `target.cash` (the funding room —
already turned into deployable dollars in exactly one place,
`CapacityAssessment.funding_room_usd`); `max_single_position` /
`max_crypto` via `PortfolioFit`'s room *terms* — **never the averaged
`portfolio_fit_score`, which destroys the magnitude information by
meaning nothing in weight units**; `realized_volatility` with an
explicit `price_reading.age()` gate; `PortfolioDrawdown.depth` against
`constraints.max_drawdown`.

**Inadmissible, with the reason**: the entire dormant
`app/config.py:70-81` family (`max_order_usd`, `max_position_pct`, …)
— never consumed, expressed as *fractions* where every policy figure
is a *percentage* (a silent 100× error), and a second unreconciled
policy source; `market_cap` and its magnitude (denomination
unestablished for every security, by the type's own construction —
inadmissible for absolute thresholds); **equity liquidity, which does
not exist** — `volume_24h` is token-only and no ADV/spread/volume
field reaches any equity type; **sector/correlation exposure, which is
unimplementable today** — holdings carry no sector field and no
pairwise correlation exists anywhere (the only correlation in the
codebase is security-vs-benchmark); the allocation targets for
stocks/ETFs/crypto on the executive path (constants of zero); and
**every field named confidence, conviction or score** — ordinal
0–100 values that *look* like portfolio percentages and mean nothing
in weight units, `portfolio_fit_score` the most dangerous because it
is literally derived from room fractions and then averaged into
meaninglessness. Conviction is additionally forbidden by the #219
ruling C.

**Three structural hazards a sizing contract must design around**:
the `None → 0.0` collapse on equity and cash (a broker outage is
indistinguishable from an empty account — sizing must gate on the
broker having actually answered); the silent 100.0 single-position
default; and the total absence of any broker minimum-order or
fractional-unit model — a computed size has nothing telling it whether
it is executable, which is one more reason the envelope must remain a
*consideration bound*, not an instruction.

**Two deliberate design positions confirmed, not gaps**:
`ExecutiveAction` carries no size *by stated intent* ("no size, price
or quantity is ever suggested"), and the entry-question's room figure
is documented as "a ceiling, never a target… sizing below the ceiling
waits for an evidence-backed sizing model." Adding magnitude is a
policy change the owner makes, not a hole to fill. And `held` at
action time is a boolean built one line away from the full position
weights — **the cheapest place magnitude could later attach is the
seam that already has the data in scope and deliberately narrows it.**

## 2. Stage 1 — input sufficiency, from the recorded cycle

Computed offline from cycle `0a15d9df7a64`'s own captured portfolio
evidence (transports patched to raise; zero calls). Normalized only:

- **cash fraction 0.578** · invested 0.422 · 14 holdings mapped
  through the identity observation stream with **zero unmapped
  instruments** — the #216 stream doubling as the instrument-to-symbol
  join, offline.
- weights: BTC **0.205**, ETH **0.105**, NOVO-B.CO 0.079, then eleven
  equity/fund positions between 0.001 and 0.005; top-3 0.389;
  HHI 0.059.
- **The same portfolio is non-compliant under policy A and compliant
  under policy B.** BTC+ETH ≈ 0.31 of the account is **over** path A's
  `max_crypto` 20 and **under** path B's explicitly set
  `maximum_crypto_pct` 65. Therefore no envelope can claim policy
  compliance until one source is authoritative — the two-source
  question in a single measured fact. (Path B's 0% missing-value
  default is not the live reading and is not substituted here.)
- Every capital-asking equity (DIS 0.003, BNP.PA 0.002) has essentially
  the full single-position room available; the binding constraint for
  any equity OPEN today would be the concentration cap, not cash.
- All of it computable with **zero new acquisition**: present weight,
  OPEN capacity, ADD capacity, REDUCE overweight, total and class
  concentration. The one required input that does **not** exist is an
  equity liquidity figure, and the one that exists but is unusable is
  the class target set on the executive path.

## 3. Stage 2 — the scenario matrix

Fifteen scenarios over synthetic normalized portfolios shaped like the
real contract (production evidence untouched), a deterministic
envelope of weight-based ceilings — eligibility (the #219 six-family
floor) → evidence ceiling (named gaps cap at STARTER, an owner
parameter **deliberately left unset**) → portfolio-capacity ceiling
(min of concentration room, funding room, class room where a cap
exists) → final = min. Results:

| scenario | outcome |
|---|---|
| 1 unheld, liquid, broad, OPEN | eligible, envelope = concentration room |
| 2 hard prerequisite unresolved | **refused, none** |
| 3 floor passes, one named gap | eligible, **capped at STARTER — not computable until the owner sets it**, gap named |
| 4 held below ceiling, ADD | eligible, room = cap − weight |
| 5 held at ceiling | eligible, **envelope zero** |
| 6 held above ceiling, course not REDUCE | envelope zero — worded as the owner's oversized sentence: the thesis unchanged, the capacity absent |
| 7 REDUCE on oversized | **compliance-reduction floor** = the overweight — *at least* this much restores compliance; never a maximum, a target, or an exit judgment |
| 8 concentrated / 10 cash below reserve | envelope zero, binding constraint = funding room |
| 9 drawdown breach | **envelope unchanged — the honest gap**: no owner loss budget exists to bind it |
| 11 small liquid company | same envelope as the large one — size is not an input |
| 12 famous company, floor fails | **refused, none** — fame is not an input |
| 13 stale price | refused, none |
| 14 correlated pair | **unsupportable — no sector or correlation data exists**; the two compete only through the shared funding room |
| 15 crypto | **refused**: the equity contract cannot govern a digital asset honestly — its own gate family, its own cap, and pretending otherwise would blur which rules bound the action |

**Five amendment pins**, added on the owner's correction, all
asserted (the 3% and 2% figures are scenario fixtures only, never
owner policy):

- a 20% concentration cap plus a 3% fixture initial-position limit
  yields a **3% OPEN envelope, not 20%** — capacity is the ceiling's
  ceiling, never the size;
- a 4% holding plus a 2% fixture ADD-change limit yields **at most a
  2% ADD envelope** although concentration room is 16%;
- a 4% overweight establishes a **4% compliance-reduction floor** —
  worded *"at least 4% of the portfolio would need to be reduced to
  restore policy compliance"*, never a maximum reduction, never an
  order, never a currency amount;
- the same **31% crypto exposure is over policy A's 20% and under
  policy B's 65%** — non-compliant and compliant at once, which is why
  neither can bind an envelope until one is authoritative;
- a **draft policy refuses the final envelope** while the capacity
  ceiling stays visible.

**Every required monotonicity property held**: gaps never increase the
envelope (ruling G, by construction — a gap can only add a ceiling);
more exposure never increases ADD room; less cash headroom never
increases capacity; a stale price or unresolved identity floors it to
none; conviction cannot move it because conviction is not an input.
Liquidity monotonicity is **recorded as unmeasurable** for equities —
no data exists to worsen.

## 4. Stage 3 — the form, measured

**A (exact currency): rejected.** It requires publishing or implying
live personal balances, false precision against an unmodelled broker
minimum, and it breaks the moment the account value moves.
**B (maximum portfolio-weight change): the right carrier** — computable
from admissible inputs, normalized (nothing personal leaks), unit-
compatible with every policy parameter, and scale-free (Q16: a small
company receives the same envelope as a large one when the constraints
are equal, because size is not an input).
**C (discrete NONE | STARTER | STANDARD): useful only on top of B.**
STARTER defined by anything evidence-derived becomes a confidence
grade by the back door (Q12); defined as **an owner-chosen maximum
weight for a first position under named uncertainty**, it is a capital
bound and nothing else.
**D = B + C is the least precise form that remains useful**: a
descriptive envelope backed by a maximum weight-change, each ceiling
named, the binding constraint named.

**The candidate object splits in two.** `PortfolioCapacityCeiling` —
the hard maximum room under cash, concentration and class constraints,
computable today — and `CapitalActionEnvelope` — the smaller,
owner-policy-bound action consideration inside it, whose final value
is the minimum of the capacity ceiling, the evidence ceiling, the
course's own owner parameter (STANDARD_INITIAL_WEIGHT for OPEN,
MAX_ADD_WEIGHT_CHANGE for ADD) and any operative drawdown or staleness
ceiling. The envelope object further survives with three amendments:
`liquidity ceiling` must be carried as **unmeasured** for equities
rather than a number; `owner-policy version` requires the hash
mechanism to exist on the *executive* policy path (today it exists only
on `decide`'s); and the object is a **projection** over the cycle
record and portfolio facts — derived on read, stored nowhere, exactly
as `DecisionSufficiency` before it. It has no conviction field, and
this measurement adds: it must also carry *which policy source and
version bound it*.

## 5. The eighteen acceptance questions

1. **Not as one symmetric contract.** OPEN and ADD need maximum
   *upward-change* envelopes bounded by owner parameters that do not
   exist yet; REDUCE computes a *policy-compliance reduction floor* —
   "at least this much" — and any reduction beyond it needs a separate
   owner rule or an explicit thesis reason. One capacity arithmetic,
   two different action semantics.
2. **Yes** — conviction appears nowhere and nothing missed it.
3. **Yes, by construction** — a gap can only add a ceiling (ruling G).
4. The #219 six-family floor, plus a readable broker answer
   (`total_value > 0` with the None→0.0 hazard gated) and an unstale
   price. Each forces NONE.
5. **Yes, mechanically — not yet in substance**: the STARTER cap makes
   a bounded envelope expressible, but its value is an owner decision
   that does not exist; until then a bounded envelope is NONE.
6. **Yes** — weight is normalized, policy-compatible, and leaks
   nothing; currency requires an executability model that does not
   exist and personal figures this report may not carry.
7. See §6 — eight decisions, led by the two-source reconciliation.
8. **Only if the owner sets a loss budget.** Scenario 9 measured the
   status quo honestly: a portfolio in drawdown sizes exactly as one
   that is not, because `max_drawdown` is unset on path A and optional
   on path B. Making it operative is one line of policy, not code.
9. **Yes** — single-security and class concentration are computable
   now (aggregate by instrument id; class room only where a cap
   exists and nothing is unclassified).
10. **No** — sector and correlation constraints have no data to stand
    on; holdings carry no sector field and no pairwise correlation
    exists. Named as out of reach without a data decision, not
    designed around.
11. As the owner's own sentence words it: above the envelope, thesis
    unchanged, capacity zero — scenario 6 produced exactly that state.
12. **Yes, iff STARTER is an owner-chosen weight bound.** Any
    evidence-derived definition is a confidence grade wearing a size.
13. **No** — no equity liquidity datum exists; the ceiling cannot be
    deterministic today and is carried as unmeasured.
14. Stale price → refusal (measured, scenario 13). Stale cash/exposure
    → currently invisible: the broker payload's age is captured but no
    consumer enforces a maximum — the staleness limit is owner
    decision #4.
15. **Yes** — the three tested wordings each fit one sentence; the
    eligible-but-limited form reads naturally with the envelope in
    weight terms.
16. **Yes** — measured (scenarios 1 vs 11, identical envelopes).
17. **Yes** — measured (scenario 12; fame is not an input).
18. §6, in full: everything else here is engineering.

## 6. The owner decisions required — and what stays NONE until then

1. **The authoritative policy source and its version** —
   `config/policy.yaml` or the strategy file, the reconciliation or
   deletion of the dormant `config.py` risk family, and the hash
   mechanism riding on whichever source wins. A **draft** strategy
   cannot authorize a capital envelope.
2. **The STARTER maximum weight** — the under-uncertainty bound.
3. **STANDARD_INITIAL_WEIGHT** — the maximum weight for a broadly
   evidenced *new* position. Without it, broad-evidence OPEN has
   computable capacity and no position-size contract.
4. **MAX_ADD_WEIGHT_CHANGE** — the maximum additional weight change
   considered in one cycle. Without it, ADD is likewise unbounded in
   action terms.
5. **The missing-limit rule** — an absent `maximum_single_position_pct`
   must *refuse* sizing rather than default to 100.0. (A latent code
   hazard today; the live file sets the value explicitly.)
6. **The staleness limits** — how old a price and a portfolio reading
   may be before the envelope refuses.
7. **The loss budget** — whether `max_drawdown` binds new capital, and
   at what depth; today a breach changes nothing.
8. **REDUCE_POLICY** — restore-to-policy-cap only, or a thesis-driven
   target/exit under a separately defined rule. Until selected, the
   only supportable sentence is: *"At least [normalized overweight]
   would need to be reduced to restore policy compliance."* — never an
   order, never a currency amount.

Four standing statements beside the inventory:
**`max_single_position` is a hard concentration ceiling, not a
suggested initial position.** **`minimum_cash_pct` and
`target_cash_pct` need explicit sizing semantics** — the live file
sets minimum 40 above target 5, and nothing consumes the minimum
today. **Liquidity remains unmeasured for equities.** **A draft
strategy cannot authorize a capital envelope.**

Also parked, per the #219 ruling E: DOCUMENT_REFUSED propagation
(named follow-on, not a sizing prerequisite); and equity liquidity —
the raw field exists in the provider payload and is discarded at the
facts boundary today, so an equity liquidity gate is a *data decision*
(read what is already served) rather than a new provider.

## 7. Boundaries held

No trading or order construction, and no broker write method exists ·
no exact dollar recommendation — normalized ratios only, no balance,
identifier or absolute wealth anywhere in this report or its artifacts
· no conviction in sizing (ruling C, enforced structurally: not an
input) · no confidence or completeness percentage · no Kelly, no
optimizer, no correlation acquisition, no new provider · no decision
threshold or quorum change · no automatic demotion for sparse
information (ruling A) · no scheduler, UI or surface work · no
production code · stage 1 offline with transports raising and zero
calls; production `data/` untouched; the synthetic matrix touched no
stored evidence.

---

## 8. Owner ruling — 2026-08-19 · the v1 capital policy

The corrected measurement is accepted, and the owner sets the v1
policy this section records.

### Policy authority

For the executive cycle and the Capital Action Envelope,
**`data/investor_strategy.json` is the authoritative owner-policy
source.** It must be explicitly **active** and valid before an
envelope is produced; its decision-bearing fields are canonically
hashed, and the policy source, version and hash travel with every
envelope. `config/policy.yaml` remains a legacy source for the old
standalone `decide` path and is **not admissible** for the envelope;
`app/config.py`'s dormant risk fields are inadmissible; policy sources
are never silently combined. A future cleanup may retire the legacy
`decide` policy — not in this slice.

### Owner values — capital envelope v1

| parameter | value |
|---|---|
| STARTER_MAX_TOTAL_POSITION_PCT | **1.0** |
| STANDARD_INITIAL_POSITION_PCT | **3.0** |
| MAX_ADD_WEIGHT_CHANGE_PCT | **2.0** |
| MAX_SINGLE_POSITION_PCT | **20.0** |
| MAX_CRYPTO_PCT | **65.0** |
| CAPITAL_ACTION_CASH_FLOOR_PCT | **max(target_cash_pct, minimum_cash_pct)** — 40.0 under the current declared strategy |
| PRICE_MAX_AGE_MINUTES | **15** |
| PORTFOLIO_MAX_AGE_MINUTES | **15** |
| MAXIMUM_ACCEPTABLE_DRAWDOWN_PCT | **20.0** |
| REDUCE_POLICY | **restore_to_policy_cap** |

Missing required limits always refuse. Crypto remains outside the
equity envelope. Human approval remains required. Automatic trading
remains disabled.

### Semantics

**STARTER is a maximum total position weight under named
uncertainty**: an unheld security's OPEN may consider up to 1%; a
holding below 1% may ADD only the room up to 1%; a holding at or above
1% has **zero** gap-limited ADD capacity.
**STANDARD_INITIAL_POSITION** is the maximum initial weight for a
broadly evidenced OPEN — not a target. **MAX_ADD_WEIGHT_CHANGE** is
the maximum upward weight change considered in one cycle — also not a
target. **MAX_SINGLE_POSITION** remains a hard concentration ceiling.
At or beyond the declared 20% portfolio drawdown: OPEN and ADD
capacity are zero, REDUCE remains available, non-capital courses
remain available. **REDUCE under v1 reports only the minimum
normalized reduction needed to restore the policy cap** — anything
larger requires a later thesis-driven rule and is never inferred.

These are conservative owner-selected product parameters. They are not
derived from conviction, company fame, coverage count or an optimizer.
