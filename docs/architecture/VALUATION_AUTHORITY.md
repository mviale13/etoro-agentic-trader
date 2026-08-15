# The Valuation Authority Investigation

**Status: measured, 2026-08-16. An investigation — nothing was changed.**

The first UNSOURCED rule examined under the provenance regime:
`pe-bands@1` with `valuation-scores@1`. The question was never what the
thresholds should be; it was **what evidence and authority would allow
MOVRvest to conclude that a security's price improves, weakens, or does
not affect its investment case.**

The verdict, stated first: **MOVRvest currently cannot establish that a
security is cheap or expensive.** It can establish a multiple — one
provider's unaudited ratio, at a date — and it holds two sources of
context it has never licensed. Every word past the multiple is
unsourced judgment, including the word "CHEAP" itself, and including a
finding sentence that claims a comparison nobody computed.

---

## 1. The complete valuation path

```text
Yahoo `info["forwardPE"]`                 ← provider-computed, definition undisclosed
  → ValuationSnapshot.forward_pe          dated (Provenance), cached, replayed as dated
    → CompanyFacts.forward_pe             gated by has_company (F1)
      → pe-bands@1: <18 | <28             CHEAP / FAIR / EXPENSIVE  + confidence 90/80/85 (asserted)
        → finding: "Forward P/E below     ← prose claiming a benchmark nobody holds
           historical market average"
        → signal-vote@1: CHEAP=+1 ×0.40   → BUY/HOLD/SELL → actionable-buy@1 / veto-sell@1
        → valuation-scores@1: 80/55/25    → DecisionEvidence.valuation_score
          → decision-gates@1:
              score < 60 → PREPARE        "valuation does not currently support action"
              score ≥ 60 → (next gate)
          → conviction-mean@1             the 80/55/25 enters the average
```

**Why FAIR cannot reach RECOMMEND, mechanically:** the gate reads one
bit. `minimum_recommendation_valuation = 60`, and the score map places
only CHEAP (80) above it — FAIR (55) and EXPENSIVE (25) both land in
the same PREPARE branch. The three-band vocabulary collapses to a
binary at the gate; the 55-vs-25 distinction survives only in the
conviction average. Two further facts the thresholds hide:
**EXPENSIVE never rejects** (an overpriced case is parked, not
discarded), and a valuation of `None` also parks at PREPARE — so the
entire investment meaning of `pe-bands@1` + `valuation-scores@1` at the
state machine is exactly: *CHEAP permits; everything else waits.*

**Information discarded en route:** `trailing_pe` and `peg_ratio` —
acquired in the same payload, cached, consumed by nothing; the
provider's own `revenue_growth`, `earnings_growth`, margins, ROE,
leverage and cash flows — on `CompanyFacts`, read by other signals,
never by valuation; sector and industry — read only by the playbook
selector. **Assumptions introduced:** that 18 and 28 mean the same
thing for every business; that Yahoo's ratio is right; that a
confidence of 90 attaches to a threshold comparison.

---

## 2. What the provider P/E actually establishes

| question | answer |
|---|---|
| definition | Yahoo's `forwardPE`: price ÷ consensus forward EPS, computed by Yahoo, methodology undisclosed, unaudited |
| trailing vs forward | forward used; `trailingPE` acquired and consumed by nothing |
| observation time | carried honestly (Provenance) — the measured corpus was deciding on snapshots 6–7 days old |
| currency | the ratio is currency-free when price and EPS share a unit; Yahoo's LSE pence/pounds mismatch is a known hazard of this provider — no live LSE snapshot exists to measure (AZN holds nothing) |
| negative earnings | Yahoo usually omits the field → honest UNKNOWN. **But a negative `forwardPE`, if ever delivered, reads `pe < 18` → CHEAP at confidence 90** — the band has no lower bound. Latent, unexercised by the corpus, recorded not repaired |
| exceptional earnings | nothing distinguishes a cyclical peak from a run rate |
| company vs security level | listing-level (share class) |
| sector / growth / balance sheet / maturity | all acquired in the same payload; none enters the valuation path |

**The source establishes:** one unaudited ratio, at a date. **MOVRvest
infers:** the band, the confidence, the "below historical market
average" sentence, the 80/55/25, and the gate — all five inferences
under two UNSOURCED rules.

A neighbouring measured hazard, same provider class: `dividendYield`
arrived ×100 wrong for four live securities (BNP.PA reads **885%**,
VOW3.DE 689%, UMI.BR 210%, DIS 143%). It does not touch the band, but
it sits one field away in the same payload and confirms the standing
provider-hygiene finding: this source's units cannot be trusted
per-field without measurement.

---

## 3. The universality assumption, measured

Eight of the nine live securities holding a P/E read **CHEAP**. What
that one band spans:

| security | fwd P/E | eps growth | rev growth | op margin | d/e | what it is |
|---|---|---|---|---|---|---|
| VOW3.DE | 3.3 | **−41.0%** | 2.0% | 4.2% | 1.39 | cyclical, capital-intensive, captive-finance leverage |
| BNP.PA | 8.6 | — | — | — | — | **a bank** — a business this platform has *ruled* is read in a different financial language |
| ADBE | 9.6 | 7.9% | 12.7% | 35.3% | 0.61 | high-margin software |
| ETOR | 10.5 | 24.6% | **−35.6%** | 2.8% | 0.02 | broker, revenue collapsing |
| UMI.BR | 12.8 | **+74.2%** | 60.1% | 3.0% | 1.33 | industrial at a growth inflection |
| NOVO-B.CO | 14.0 | **−20.6%** | 2.1% | 42.5% | 0.63 | pharma past an earnings peak |
| DIS | 14.1 | **−48.3%** | 6.8% | 19.3% | 0.39 | mature media, earnings halved |
| META | 16.9 | — | — | — | — | platform business |

One band covers earnings growth from **−48% to +74%**, margins from
2.8% to 42.5%, leverage from 0.02 to 1.39, a bank, a broker, a
cyclical and two growth franchises. The economic proposition "this
price is low relative to what you get" is *obviously different* in
each row, and the band cannot see any of it.

Two sharper points from the same table:

- **The provider's own context field disagrees with its flat band.**
  `pegRatio`, already cached: VOW3.DE 0.7 and ADBE 0.6 against
  NOVO-B.CO 3.2, DIS 2.6, UMI.BR 2.6. The same vendor's
  growth-adjusted multiple *re-orders* the CHEAP bucket end to end.
  This is not an endorsement of PEG — it demonstrates that even
  one-field context overturns the universal ordering.
- **The platform contradicts itself about BNP.PA.** The Financial
  Domain Boundary ruling holds that a bank is read in an
  interest-based financial language, and `FinancialModel.BANK` refuses
  generic industrial questions — while `pe-bands@1` applies the
  industrial multiple lens to the same bank without comment.

**Conclusion: P/E cannot legitimately carry investment meaning without
context, and the corpus proves it on eight securities.** Separately,
SPCX — an ETF — is classified `stock`, so a fund is receiving a P/E
judgment (71.8 → EXPENSIVE), a LOW company quality and a SELL veto:
the F1 defect shape re-entering through asset-class *input* rather
than the boundary rule. Recorded as a follow-up finding.

---

## 4. What "valuation" currently collapses

Four distinct claims live in the one word:

| layer | example | exists today? |
|---|---|---|
| **Observation** | forward P/E is 17.4×, per Yahoo, on this date | **yes** — `CompanyFacts.forward_pe`, dated, honest about absence |
| **Comparison** | 17.4× is below *benchmark B* | **no** — the constant 18 is an unnamed benchmark; no domain object names a basis of comparison |
| **Interpretation** | the price embeds assumptions that look conservative relative to evidenced fundamentals | **no** — collapsed into the band word |
| **Investment effect** | this improves the case | **collapsed into 80/55/25 + the gate**, unsourced |

The architecture can support the first today. The second is where the
one actively *false* sentence lives: the CHEAP finding reads **"Forward
P/E below historical market average"** — prose claiming a comparison
with a benchmark this platform does not hold. The number 18 is a house
constant; "historical market average" is an appeal to evidence that was
never acquired. That sentence is the Invariant-10 shape (a fact
carrying an interpretation nobody licensed) already on the dossier.

---

## 5. Dormant valuation capability

The repository sweep for intrinsic value, fair value, DCF, margin of
safety, analyst targets, price targets, required/expected return and
valuation ranges: **empty across all of `app/`**. There is no dormant
valuation model. What exists instead:

- **`trailing_pe` and `peg_ratio`** — acquired, cached, consumed by
  nothing (provider-grade, unit-hazardous).
- **Provider growth/margin/leverage/cash-flow fields** — on
  `CompanyFacts`, consumed by other signals, never by valuation.
- **`FinancialUnderstanding`** — the genuine asset: filing-grade
  margins, growth, ratios and cash flow computed from checked cells
  with the narrowest agreement beneath each. Live for **1 of 14**
  holdings (DIS); the wider statements corpus (JPM et al.) sits outside
  the portfolio.
- **The old market-level Value committee** (`app/committee/value.py`) —
  *a second, independent copy of the same belief*: `pe < 18 → BUY`
  ("Forward P/E is attractive"), `pe > 30 → HOLD`, at market altitude,
  feeding the `/brain` surfaces. The 18 constant exists twice, in two
  packages, under no rule in one of them.
- **`InvestmentPolicy`** — risk profile, allocation targets,
  constraints. **No required return, no valuation preference of any
  kind.** The investor's own policy is silent on price.

---

## 6. Contrasting case studies

*What would MOVRvest actually need to know before calling this
security cheap?*

- **VOW3.DE (cyclical, P/E 3.3).** Whether 3.3× is priced off peak or
  trough earnings — a cycle position the platform does not hold — and
  what the captive finance arm does to the denominator. A cyclical at
  3× peak earnings is routinely dearer than at 12× trough. The
  earnings the multiple divides by fell 41% last period; nothing in
  the path knows.
- **BNP.PA (bank, P/E 8.6).** The platform's own ruling: bank
  economics are interest-based, prudentially constrained
  (CET1/LCR unreachable today), and not readable in industrial
  language. A bank P/E without book value, capital position and rate
  environment is a number wearing a meaning it cannot carry — by
  MOVRvest's own domain law.
- **NOVO-B.CO / ADBE (growth, 14.0 / 9.6).** Whether evidenced growth
  and margins justify the multiple — the *only* question, and the one
  the band cannot ask. Both context fields exist (provider-grade for
  both, filing-grade for neither).
- **DIS (mature, P/E 14.1, eps −48%).** Whether the earnings halving
  is structural or transient. DIS is the one holding with filing-grade
  `FinancialUnderstanding` — the context exists at licensed quality
  and the valuation path cannot see it.
- **AZN / CYD (nothing held).** The honest case, handled honestly:
  no snapshot → UNKNOWN → no score. The absence path is the one part
  of this pipeline that already meets the platform's standards.

The needed evidence differs *structurally* by business — cycle
position for the cyclical, capital structure for the bank, growth
durability for the growers, earnings quality for the fallen — which is
the finding: **no single-field rule can be repaired into legitimacy.**

---

## 7. Candidate authorities

For each: evidence required / acquirable today? / deterministic? /
contains investor preference? / could investors disagree? /
generalises? / who could license the effect.

| authority | needs | acquirable | deterministic | preference? | disagree? | generalises | licensor |
|---|---|---|---|---|---|---|---|
| **own history** (P/E vs its past range) | a multiple time series | not held (cache overwrites); the journal pattern could hold it | yes, given a window | **yes** — mean reversion is a belief | yes | poorly (regime changes, banks) | a measured doc + policy |
| **comparable businesses** | peer group + peers' multiples | not held for equities; crypto's `MarketPeerGroup` precedent warns a vendor category is not an archetype | yes, given the group | **yes** — "peers should trade alike" | yes | medium | same |
| **evidenced growth/cash relationship** | growth + margins + a linking model | **partially held**: provider-grade for most, filing-grade (licensed quality) for DIS | only given a named model | the model *is* the preference | yes | medium | same |
| **explicit valuation model (DCF)** | projections + discount rate | nothing held; a discount rate is an investor preference squared | no (inputs are choices) | **maximal** | maximal | yes in form | investor policy only |
| **market-implied expectations** (reverse-engineer what the price assumes) | price (held) + base earnings (held; filing-grade for DIS) + a named model with named parameters | **closest to reach** | **yes** — arithmetic under a versioned model | in the model choice, *not in the output* | about the model, not the fact | yes | a versioned rule, like every S5 rule |
| **investor required return** | the investor to state one | policy has no such field | yes, once stated | **that is the point** — the preference placed where preference belongs | n/a — it is *their* number | yes | **the investor**, via policy |
| **analyst consensus** | acquisition of third-party targets | not acquired | n/a | imports others' | yes | medium | nobody — the platform already rules a third party's opinion is "not evidence" (TokenInsight) |
| **investment-policy rule** | any of the above, named | — | — | — | — | — | the licensing *mechanism*, not an authority itself |

Two stand out, for opposite reasons:

- **Market-implied expectations** is the only authority whose output
  is a *fact about the price* rather than a judgment about
  attractiveness — "at this price, under model M@1, the market embeds
  X% growth for N years." Deterministic under a versioned rule,
  auditable, and it hands the investor exactly what MOVRvest's
  charter promises: evidence they can decide with. It does not
  produce an `InvestmentEffect`; it produces the *comparison layer*
  §4 shows is missing.
- **Investor required return** is the only legitimate home for the
  *effect*: whether embedded expectations are acceptable **is an
  investor preference**, and the policy — currently silent on
  valuation — is where the platform already keeps preferences
  (risk profile, allocation). "MOVRvest recommends; the investor
  decides" points here.

The two compose: the platform establishes what the price assumes; the
policy says what the investor will pay for. Neither exists today, and
neither was built in this slice.

---

## 8. CHEAP / FAIR / EXPENSIVE

The words contain judgment, not description. "Cheap" asserts all four
of §4's layers at once — an observation, a comparison against an
unnamed basis, an interpretation, and (through the score map) an
effect. A raw multiple cannot legitimately be called CHEAP without a
comparison basis, and the only basis on hand is a constant that
`pe-bands@1` now at least *names*.

The least opinionated vocabulary for what the system knows today:
**"forward P/E of 17.4× — below this platform's fixed band at 18
(`pe-bands@1`, unsourced)"** — the position and the ruler, no verdict
word. The `ScoreBasis` prose already says half of this honestly ("This
platform scores CHEAP at 80…"); the *finding* sentence ("below
historical market average") says the dishonest half. Nothing renamed
in this slice.

---

## 9. The FAIR-wall propositions, made explicit

What each transition would require somebody to establish:

- **CHEAP → RECOMMEND (current):** *"a forward P/E below 18 improves
  any investment case enough to permit action — for every sector,
  growth rate, leverage and earnings direction."* Established nowhere;
  contradicted by the corpus table in §3.
- **FAIR → PREPARE (current):** *"a price in [18, 28) neither clears
  nor damns; the case waits."* Hidden inside it: waiting is treated as
  costless — no opportunity-cost proposition exists anywhere.
- **FAIR → RECOMMEND (counterfactual):** would require *"an evidenced
  case is not materially weakened by a price within the band"* —
  valuation as a **veto** (reject overpaying) rather than a
  **requirement** (demand cheapness). That is a different investment
  philosophy, held by many reasonable investors, established by
  nobody here.
- **EXPENSIVE → never RECOMMEND (current):** *"no business is good
  enough to pay more than 28× forward earnings for."* A proposition
  entire schools of investing reject.
- **EXPENSIVE → never REJECT (current, unnoticed):** *"an overpriced
  case is worth keeping warm rather than discarding."* Arguably the
  rule's one humane choice — exactly as unsourced as the rest.

---

## 10. Recommendation: the smallest legitimate next boundary

**The Comparison layer — a valuation statement must name its
benchmark, as a versioned rule, or state that it has none.** Not a new
model, not new thresholds, not an effect. Concretely, the next slice
worth proposing (not built here):

1. the CHEAP/FAIR/EXPENSIVE finding sentence stops claiming a
   "historical market average" nobody holds and states its actual
   basis — the platform's own fixed band, by rule id — which is a
   presentation-honesty repair squarely in the Invariant-10 lineage;
2. `movrvest`'s valuation vocabulary becomes *observation + named
   basis* (§8's wording) with the band word retained as the label of
   the platform's rule rather than a claim about the market;
3. the first candidate authority to *investigate* afterwards is
   market-implied expectations under a named versioned model — the
   only authority producing a fact rather than a preference — with
   the effect reserved to a future investor-policy clause
   (`required return`), which is where this platform already keeps
   the investor's own choices.

**And the honest headline stands: MOVRvest cannot currently establish
that any security is cheap or expensive.** It can establish a
multiple, an absence, and — for one holding — filing-grade context it
has never connected. Everything else is a constant with a confident
vocabulary. That result is the deliverable.
