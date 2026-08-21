# How a security's own volatility could constrain the action

**Research only. Nothing here is built, and the absolute volatility veto
is untouched.** Prerequisite 4 of the owner's ruling of 2026-08-21 on
[`SECURITY_VOLATILITY_DECISION_ROLE.md`](SECURITY_VOLATILITY_DECISION_ROLE.md):

> The Capital Action Envelope must carry an explicit per-security
> volatility constraint before the absolute veto is removed.

The brief asks what shapes that constraint could take across four
surfaces — OPEN eligibility, ADD eligibility, maximum total position,
maximum incremental position change — with maximum drawdown measured
separately, and **no threshold or multiplier invented**.

---

## Conclusion

**B — MECHANISM READY, OWNER VALUES REQUIRED.**

Every part of the machinery a per-security volatility constraint needs
already exists and is already shaped the right way. What does not exist
is a single number saying how volatility maps to a ceiling, and no
measurement in this document can produce one: the corpus can say what
each candidate shape *would do*, and cannot say what an investor should
be willing to hold.

Three things are ready, and each was checked rather than assumed:

1. **The reading reaches the envelope.** `SECURITY_VOLATILITY_DECISION_ROLE.md`
   recorded that *"the envelope cannot receive what the gate would give
   up"*. That is now out of date: PR #231 put the whole `RiskSignal` —
   `volatility`, `max_drawdown`, `level`, its rule — on
   `DecisionEvidence` as `risk_reading`, and `_envelope` already reads
   `workspace.evidence`. The security's own volatility is one field
   access away from the envelope, and no new wire is needed.
2. **Every ceiling is already a `min()`.** `envelope_for`'s own
   contract is that *"every ceiling is a minimum, so information can
   only preserve or reduce the result"*. A volatility ceiling composes
   into that without touching the ruling's monotonicity — it is another
   term in the same `min`, not a new arithmetic.
3. **The refusal cascade is already ordered and worded.** OPEN and ADD
   eligibility are the same cascade — hard floor, capacity, price,
   portfolio drawdown budget — each refusing in its own sentence. A
   volatility gate is one more entry in that order.

One thing is missing, and it is the whole of the gap: **`CapitalPolicy`
has eleven fields and every one of them is account-level.** There is no
per-security term of any kind, and `investor_strategy.json` states no
number about a single security's price behaviour.

---

## What was measured, and how

The stored acquisition of 2026-08-21, replayed. **Zero provider calls.**
87 stored quotes, of which 65 are equities under the broker's own
classification; 63 carry both a volatility and a drawdown reading.

Nothing in this document changes a threshold, and nothing in it selects
one.

### The corpus's volatility

| percentile | annualised volatility |
|---|---:|
| p0 | 0.3% |
| p10 | 19.1% |
| p25 | 26.8% |
| **p50** | **37.6%** |
| p75 | 52.4% |
| p90 | 67.6% |
| p100 | 111.5% |

Mean 41.6%, median 38.2%, over 80 securities holding a reading.

Under `risk-bands@1`'s existing lines (20% / 35% / 60%), the equity
corpus falls out as:

| band | count | share |
|---|---:|---:|
| LOW | 5 | 7.9% |
| MODERATE | 20 | 31.7% |
| HIGH | 27 | 42.9% |
| SEVERE | 11 | 17.5% |

**The distribution matters for shape selection.** 43% of the book sits
in a single band, so a four-band ceiling table would give nearly half
the corpus one identical constraint, and would separate almost nothing
inside it.

### The securities at the top

| security | volatility | max drawdown |
|---|---:|---:|
| LUNR | 111.5% | 75.1% |
| SPCX | 105.1% | 48.8% |
| IS7 | 93.6% | 52.4% |
| UUUU | 92.6% | 61.3% |
| MSTR | 76.2% | 77.1% |
| AMD | 71.8% | **27.8%** |
| RIVN | 71.0% | 42.5% |
| ORSTED | 67.6% | 66.0% |
| H2O | 60.8% | 63.8% |
| PLTR | 60.5% | 48.2% |
| MBGL | 60.1% | **17.4%** |

(1INCH and ADA also clear 60% and are tokens; v1 does not size
cryptocurrencies, so they are outside every shape below.)

---

## Drawdown is a second measurement, and the corpus proves it

Across 80 securities holding both, **volatility and maximum drawdown
correlate at r = 0.753**. High, and nowhere near identical — and the
residual is where the interesting names live.

At the top band the two disagree for **17 of 63** equities. Two are
decisive:

- **AMD** — 71.8% volatility (SEVERE) against a 27.8% drawdown
  (MODERATE). It swings hard and has not fallen far.
- **MBGL** — 60.1% volatility (SEVERE) against a 17.4% drawdown (LOW).

And the reverse exists too: **NFLX** (34.7%, MODERATE) and **PNR**
(32.8%, MODERATE) both carry drawdowns above 45%.

**They answer different questions.** Volatility asks how much the price
moves; drawdown asks how far it has actually fallen from a peak. An
investor's tolerance for the first is a tolerance for noise; for the
second it is a tolerance for loss. The ruling's clarification — *drawdown
and volatility remain separate measurements* — is not a stylistic
preference here: on this corpus, substituting one for the other changes
the answer for 17 securities.

**The envelope already reads a drawdown, and it is the wrong one.**
`envelope_for`'s existing loss-budget gate reads `drawdown_depth_pct`,
which is the *portfolio's* current depth against the investor's
`maximum_acceptable_drawdown_pct`. That is an account-level gate and
stays one. A per-security drawdown term would be a second, differently
scoped constraint, and conflating the two would let one security's
history close the whole account's budget.

---

## The four surfaces, and what could attach to each

The brief names four. Each already exists in `envelope_for`, and this
is where a volatility term would attach.

| surface | today | what a volatility term would be |
|---|---|---|
| **OPEN eligibility** | the refusal cascade: hard floor → capacity → price freshness → portfolio drawdown budget | one more refusal in that order, worded like its neighbours |
| **ADD eligibility** | the same cascade | the same refusal; ADD and OPEN differ only in which room constant applies |
| **maximum total position** | `starter_max_total_position_pct` under named uncertainty, else `standard_initial_position_pct`; `max_single_position_pct` bounds the account side | another ceiling in the existing `min()` |
| **maximum incremental change** | `max_add_weight_change_pct` | another ceiling in the same `min()`, on the ADD branch only |

The evidence ceiling is the precedent worth copying: under any named
uncertainty the envelope already drops to a **maximum total position**
rather than a fresh increment — *"room up to it, never a fresh increment
on top of it"*. A volatility ceiling has the same character and should
compose the same way.

---

## Candidate shapes, measured — none selected

Four shapes were considered. Each is described by what it would do to
this corpus, not by a number.

### Shape 1 — an eligibility line

Volatility at or above some level refuses OPEN and ADD outright.

This is the current veto relocated from the thesis to the action. It
satisfies the ruling's letter — the case survives as a thesis — and it
is the only shape that produces *no* magnitude at all above the line.

- At the existing 60%: **11 equities** refused, the same set that is
  rejected today.
- The shape's honest problem: it reproduces the defect the ruling
  identified, one layer down. AMD's 71.8% would close the action while
  its own analysts read growth, profitability, balance sheet and cash
  flow as strong or better. A line is a line wherever it is drawn.

### Shape 2 — a band-to-ceiling table

`risk-bands@1`'s four levels each map to a maximum total position.

Reuses machinery that exists, needs no new measurement, and produces a
sentence the envelope can already word. **But 43% of the equity corpus
is in one band**, so the table would treat a 35.1% security and a 59.9%
security identically while separating 59.9% from 60.1%. The corpus does
not support four steps carrying much information.

### Shape 3 — a continuous ceiling

Maximum total position scales inversely with volatility under some
function.

Separates the whole distribution rather than four steps of it, and it
composes into the existing `min()` unchanged. It needs **two** owner
values rather than one — a reference volatility and a reference weight —
and it invites a third: a floor, or the ceiling approaches zero for
LUNR at 111.5%.

Recorded as a caution rather than an objection: a continuous function
reads as a measurement. Whatever curve is chosen is a policy, and its
output must be worded as *the policy permits*, never as *the security
supports*.

### Shape 4 — increment-only

Volatility constrains the incremental change alone, leaving the
maximum total position to the existing account caps.

The narrowest shape, and the one that changes least: it slows the rate
at which a volatile position is built without ever saying how much of
it may be held. It also does nothing for a security bought once at
full size, which is the shape most of this account's positions have.

---

## What must be true before any shape is built

Recorded because each is a defect waiting if it is skipped.

1. **A gate that cannot be evaluated fails.** Two equities in the
   corpus — **NESN** and **UDMY** — hold no volatility reading at all.
   Under every shape above they must refuse rather than pass, which is
   the rule `envelope_for` already applies to an unmeasured portfolio
   drawdown. That is 2 of 65 equities losing their action, and the
   owner should know that before choosing a shape rather than after.
2. **Crypto is outside all of it.** v1 does not size cryptocurrencies,
   and after #231 HYPE and TAO carry no vendor series and therefore no
   volatility at all — their listings are refused. No shape here reaches
   them, and none should be described as if it did.
3. **The value belongs in `investor_strategy.json` with provenance.**
   Every capital constant now travels with its source and version. A
   volatility term added in code would be the sixteenth unsourced
   constant the Decision Philosophy Audit exists to have stopped.
4. **The veto comes out only after the term goes in.** In that order,
   and not the reverse: removing the gate first leaves severe
   volatility constraining nothing at all.
5. **The wording is the policy's, never the security's.** *"The current
   policy permits consideration up to X% for a security this volatile"*
   is checkable. *"This security supports X%"* is a claim about the
   security that no measurement here establishes.

---

## What this document does not establish

- **It does not measure returns.** Nothing here says a volatile security
  performs better or worse than a calm one. It says what this
  platform's own rules would do with one.
- **It selects no shape and no number.** Four shapes are described by
  their consequences on one account's corpus. Which trade-off an
  investor wants is not a measurable property of the corpus.
- **One year, one provider.** Every volatility and drawdown figure is
  read from a single vendor's daily closes over `1y`. A different
  window would move the bands and the counts.
- **`risk-bands@1` remains `UNSOURCED`.** Shape 2 would inherit that
  status, not repair it — reusing an unsourced band in a second place
  doubles its reach without establishing it.
- **The corpus is one account.** 65 equities the investor holds or
  watches, which is not a sample of anything.
