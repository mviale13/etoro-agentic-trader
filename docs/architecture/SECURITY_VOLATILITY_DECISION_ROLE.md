# What a security's own volatility may decide

**Status: measured, and awaiting the owner's ruling. Nothing was
changed.** No threshold, decision, course, capital-envelope value or
analyst semantic moved for this document; every number below was read
from evidence the platform had already acquired, through the platform's
own functions.

## The question

> Should severe historical volatility automatically reject an otherwise
> strong company, or should it normally constrain the capital envelope
> while preserving a PREPARE/INVESTIGATE thesis state?

## What was measured, and how

64 equities — every security the store holds both a quote and a
fundamentals reading for. Zero provider calls were made: the corpus is
the acquisition of 2026-08-20, replayed.

The harness reimplements nothing. Each security's evidence is built by
`DecisionEvidenceBuilder`'s own methods over its own signals, and each
decision comes from `ArtificialCIO.decide`. Two inputs are supplied as
constants because they are properties of the **account** rather than of
the security, and are identical for every security within one cycle:

| Input | Held at | Why |
|---|---|---|
| `cognitive_confidence` | 0.70 | portfolio + market + risk reasoning confidence, one value per cycle |
| `portfolio_fit_score` | 60 | measured against the live account, which is not the subject here |

Both feed `evidence_score` and conviction. **Neither can move a
volatility rejection**, because the risk gate fires before either is
read — so Contract A's outcomes below are exact. Under Contract B they
shift a case between INVESTIGATE and PREPARE, which is stated where it
matters rather than hidden.

The three contracts, run over the same evidence:

- **A — the live policy.** `risk_score > maximum_acceptable_risk` (70)
  rejects.
- **B — thesis-preserving.** The same cascade with that one branch
  neutralised (`maximum_acceptable_risk = 100`). Everything else,
  conviction arithmetic included, is untouched; the security's risk
  still enters conviction as safety.
- **C — hybrid.** B, plus REJECT where severe volatility coincides with
  adverse business evidence: any fundamental analyst verdict at or below
  the adverse band, or the security committee's own SELL.

---

## The corpus, security by security

Fifteen named securities in the three classes the brief asks for, read
out of the 64. *Quality* is the standing behind the score, not the score
alone: **filing-grounded** where the statements reached quorum,
*provider N* where the three-field proxy governs, **unmeasured** where
neither exists. *A: course* is the course the recorded cycle actually
produced — a course needs to know whether a security is held, so it is
reported only for the securities that cycle covered, and never inferred
here.

### High-growth / high-volatility

| Security | Revenue | Earnings | Net margin | Free cash flow | Quality | Valuation | Volatility | Drawdown | A: state | A: course | B: state | Company-specific adverse fact |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AMD | 50.1% | 159.5% | 15.6% | 8.8bn | provider 62 | 25 (P/E 30.4) | 71.8% | 27.8% | REJECT | none | PREPARE | **none** |
| PLTR | 92.8% | 215.4% | 49.0% | 2.2bn | **unmeasured** | 25 (P/E 74.8) | 60.5% | 48.2% | REJECT | not in the recorded cycle | INVESTIGATE | **none** |
| SHOP | 33.7% | 68.1% | 14.5% | 1.6bn | **unmeasured** | 25 (P/E 60.1) | 57.6% | 46.7% | INVESTIGATE | not in the recorded cycle | INVESTIGATE | **none** |
| UMI.BR | 60.1% | 74.2% | 2.0% | 535m | provider 62 | 80 (P/E 12.3) | 47.1% | 28.7% | PREPARE | hold | PREPARE | Profitability: weak |
| TSLA | 25.5% | −3.0% | 3.7% | 4.8bn | filing-grounded | 25 (P/E 148.1) | 46.4% | 39.1% | INVESTIGATE | not in the recorded cycle | INVESTIGATE | Profitability: weak |
| NVDA | 85.2% | 214.5% | 63.0% | 46.3bn | **unmeasured** | 80 (P/E 17.4) | 36.7% | 20.2% | INVESTIGATE | not in the recorded cycle | INVESTIGATE | **none** |

### Distressed high-volatility

| Security | Revenue | Earnings | Net margin | Free cash flow | Quality | Valuation | Volatility | Drawdown | A: state | A: course | B: state | Company-specific adverse fact |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LUNR | 198.7% | — | −32.7% | −32m | **unmeasured** | 80 (P/E −328.0) | 111.5% | 75.1% | REJECT | not in the recorded cycle | INVESTIGATE | Profitability: weak; Cash flow: weak |
| UUUU | 496.1% | — | −77.3% | −88m | provider 40 | 25 (P/E 28.7) | 92.6% | 61.3% | REJECT | none | **REJECT** | Profitability: weak; Cash flow: weak; committee votes SELL |
| CLNE | 13.3% | — | −22.7% | −19m | **unmeasured** | 25 (P/E 33.2) | 54.0% | 48.4% | INVESTIGATE | not in the recorded cycle | INVESTIGATE | Profitability: weak |
| INSE | −10.1% | — | −18.7% | −11m | **unmeasured** | 80 (P/E 13.6) | 48.5% | 37.8% | INVESTIGATE | not in the recorded cycle | INVESTIGATE | Growth: declining |
| ORSTED.CO | 33.4% | −84.9% | 0.2% | **−20.9bn** | **unmeasured** | 80 (P/E 14.4) | 67.6% | 66.0% | REJECT | not in the recorded cycle | INVESTIGATE | **none** |

### Stable large company

| Security | Revenue | Earnings | Net margin | Free cash flow | Quality | Valuation | Volatility | Drawdown | A: state | A: course | B: state | Company-specific adverse fact |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| JNJ | — | — | — | — | **unmeasured** | 55 (P/E 21.1) | 18.3% | 11.0% | INVESTIGATE | not in the recorded cycle | INVESTIGATE | **none** |
| PG | — | — | — | — | filing-grounded | 55 (P/E 19.7) | 19.7% | 15.5% | PREPARE | not in the recorded cycle | PREPARE | **none** |
| MCD | 3.7% | 5.7% | 31.7% | 6.3bn | provider 80 | 55 (P/E 19.2) | 18.2% | 22.0% | PREPARE | not in the recorded cycle | PREPARE | Balance sheet: weak |
| AAPL | — | — | — | — | filing-grounded | 25 (P/E 32.9) | 25.0% | 13.8% | PREPARE | not in the recorded cycle | PREPARE | **none** |
| MSFT | 17.7% | 31.7% | 40.3% | 16.5bn | provider 80 | 55 (P/E 20.4) | 32.3% | 34.5% | PREPARE | wait | PREPARE | **none** |

A dash in the growth and margin columns is a **fundamentals field the
provider did not return** — four of the five stable controls report no
growth or margin figures at all. It is not a zero, and none of it is a
finding about the company.

---

## Finding 1 — the risk gate is a single-variable volatility gate

`RiskSignal` bands volatility into LOW/MODERATE/HIGH/SEVERE and drawdown
into LOW/MODERATE/HIGH, then takes the higher. `SEVERITIES` maps SEVERE
to 0.85 → risk 85, which is the only value above the policy's 70.

**`_drawdown_level` has no SEVERE branch.** Its worst band is HIGH → 65,
below the ceiling. So no drawdown, of any depth, can ever reject a
security; only annualised volatility ≥ 60% can. The gate the platform
calls *risk* is, in effect, `volatility >= 0.60`.

Measured: 9 of 64 securities reach risk 85, and all 9 do so on
volatility. LUNR's 75.1% drawdown and PLTR's 48.2% contributed nothing
to either outcome.

## Finding 2 — what the veto actually rejects

| | Contract A | Contract B |
|---|---|---|
| REJECT | 9 | 1 |
| INVESTIGATE | 45 | 51 |
| PREPARE | 9 | 11 |
| RECOMMEND | 1 | 1 |

**Eight of the nine rejections rest on volatility alone.** Only UUUU has
an independent reason — the security committee votes SELL — and it is
the one security that still rejects under B.

Every one of the nine carries conviction **40**, which is
`conviction-mean@1`'s REJECT cap. A company burning cash and a company
compounding at 50% are indistinguishable on the number the surface
prints.

### The nine, with what the platform's own analysts say about them

| Symbol | Vol | Drawdown | Growth | Profitability | Balance sheet | Cash flow | A | B |
|---|---|---|---|---|---|---|---|---|
| LUNR | 111.5% | 75.1% | strong (100) | **weak (13)** | adequate (70) | **weak (0)** | REJECT | INVESTIGATE |
| SPCX | 105.1% | 48.8% | strong (100) | **weak (28)** | excellent (92) | excellent (100) | REJECT | INVESTIGATE |
| UUUU | 92.6% | 61.3% | strong (100) | **weak (28)** | strong (85) | **weak (0)** | REJECT | **REJECT** |
| MSTR | 76.2% | 77.1% | moderate (55) | weak (47) | excellent (100) | **weak (0)** | REJECT | INVESTIGATE |
| **AMD** | **71.8%** | 27.8% | **strong (100)** | **strong (80)** | **excellent (100)** | **excellent (100)** | **REJECT** | PREPARE |
| RIVN | 71.0% | 42.5% | unknown (0.0 conf) | unknown | unknown | unknown | REJECT | INVESTIGATE |
| ORSTED.CO | 67.6% | 66.0% | weak (50) | adequate (70) | strong (85) | adequate (50) | REJECT | INVESTIGATE |
| **PLTR** | **60.5%** | 48.2% | **strong (100)** | **excellent (100)** | **excellent (100)** | **excellent (100)** | **REJECT** | INVESTIGATE |
| MBGL | 60.1% | 17.4% | **declining (28)** | excellent (90) | excellent (92) | excellent (100) | REJECT | PREPARE |

Read down the analyst columns rather than across: **the gate's outcome
and the analysts' readings have almost nothing to do with each other.**
MBGL is rejected with three verdicts of 90 or better. SPCX — a fund — is
credited with excellent cash flow. And MSTR's profitability is *worded*
weak while it *scores* 47: `_opinion_finding` bands adverse at 40 or
below, so the analyst's own word and the sense the ledger records
disagree, and only the number is machine-readable.

**PLTR is the clearest refutation of Contract A on this corpus.**
Revenue +92.8%, earnings +215.4%, net margin 49.0%, debt-to-equity 0.02,
free cash flow +$2.2bn — four analyst verdicts of 100 out of 100 — and
the platform rejects it because its price moved 60.5% annualised.

**AMD is the same case with a quality reading attached**: revenue
+50.1%, earnings +159.5%, net margin 15.6%, free cash flow +$8.8bn,
quality MEDIUM (62). Rejected at 71.8% volatility, with 27.8% the
deepest fall it actually took.

Four of the nine — AMD, PLTR, RIVN, ORSTED.CO — carry **no adverse
analyst verdict at all**.

## Finding 3 — the corpus spans the range, and the gate bites in one place

| Class | Members | Volatility | Contract A |
|---|---|---|---|
| High-growth / high-volatility | AMD, PLTR, SHOP, UMI.BR, TSLA, NVDA | 36.7% – 71.8% | 2 rejected (AMD, PLTR) |
| Distressed high-volatility | LUNR, UUUU, CLNE, INSE, ORSTED.CO | 48.5% – 111.5% | 3 rejected (LUNR, UUUU, ORSTED.CO) |
| Stable large company | JNJ, PG, MCD, AAPL, MSFT | 18.2% – 32.3% | 0 rejected |

The controls behave: no stable large company comes near the ceiling
(the highest, MSFT, reads risk 45), and every distressed name is high-
volatility. **But the gate does not separate the first class from the
second.** NVDA — revenue +85.2%, net margin 63.0%, free cash flow
+$46.3bn — passes at 36.7% only because it is *below* the line, not
because anything about the business was weighed. CLNE, with a net margin
of −22.7% and negative free cash flow, passes at 54.0% for the same
reason.

## Finding 4 — absence is being read as a finding, in both directions

**RIVN** has no fundamentals in the store at all. Every analyst returns
*unknown* at confidence 0.0: growth unavailable, margins unavailable,
balance sheet unavailable, cash flow unavailable. Contract A rejects it
— on a volatility measurement — and Contract C would spare it, because
no adverse evidence exists to find. The same emptiness produces a
rejection under one rule and a reprieve under another, and in neither
case did anyone read anything about the company.

**ORSTED.CO** is Contract C's other failure. Free cash flow of
**−$20.9bn** is scored by the cash-flow analyst as *adequate (50)*, and
earnings −84.9% as *weak (50)* — 50 is the neutral band, so neither
registers as adverse. A hybrid rule keyed on adverse analyst verdicts
misses a utility burning twenty billion dollars.

**SPCX is not a company.** It is an exchange-traded fund that eToro's
own metadata classes as `asset_type_id` 5, the known defect from the
Provider Semantics Audit. One of the nine securities the risk gate
rejects has no business to be volatile about in the first place — and it
is carrying four analyst verdicts, including *excellent cash flow*.

## Finding 5 — the veto is currently masking two defects

Both would be *surfaced* by Contract B, and neither is caused by it.

**A negative forward P/E is banded CHEAP.** `pe-bands@1` reads
`if pe < 18: CHEAP`, scoring 80 at confidence 90. LUNR's forward P/E of
**−328.0** and RIVN's of **−9.0** are the market pricing expected
losses, and both score as attractively valued. Two of 64 today; the
number rises with any loss-making candidate.

**Unmeasured quality is excluded from the conviction mean rather than
penalised.** `_calculate_conviction` averages the scores that exist. A
company nobody could describe contributes no quality term, so the mean
is taken over the remaining four — and a *low* quality reading would
have pulled it down where an absent one does not.

Together, under Contract B:

| | Quality | Valuation | Risk | Conviction (B) |
|---|---|---|---|---|
| LUNR | unmeasured | 80 (CHEAP, from P/E −328) | 85 | **58** |
| AMD | 62 | 25 (EXPENSIVE, P/E 30.4) | 85 | **45** |

A company with a −32.7% net margin and negative free cash flow would
rank **thirteen points above** one compounding at 50% with $8.8bn of
free cash flow. That is not an argument for keeping the veto — the veto
is not what makes AMD's ranking right — but it is a blocking
precondition for removing it.

## Finding 6 — "hot stock" is already a positive signal

The momentum signal emits favourable findings (*"RIVN gained +4.03% in
its most recent reading"*, *"Short-term price momentum is strongly
positive"*), and under DV2's rule a conviction is emitted only where the
case cites support. So momentum is not merely counted — **it can be the
entire licence for a conviction number**.

Measured: **5 of 64 securities** (RIVN, SRAD, SE, DIDIY, BA) have
strengths consisting *only* of momentum findings. RIVN's conviction of
40 rests on nothing except the fact that it went up, on a security whose
fundamentals are entirely absent.

This is not a volatility question, and no contract in this document
changes it. It is recorded because the brief asks that recent
appreciation never become business quality, and on this corpus it
already has.

## Finding 7 — quality is a provider proxy for 60 of 64

Only **TSLA, DIS, AAPL and PG** carry a filing-grounded
`BusinessQuality`. Every other quality score in this document is either
the provider triad (market cap, earnings, dividend) or absent. Of the
nine rejected securities, exactly one — AMD — has any quality reading at
all, and it is the provider proxy.

Whatever contract is chosen, it will be applied over a corpus whose
business quality is largely unread.

---

## The five distinctions, and where the code holds them apart

| Concept | Owned by | Held apart today? |
|---|---|---|
| Business quality | `BusinessQuality` (filings) / `QualitySignal` (provider) | Yes — the two routes never blend |
| Investment attractiveness | `ValueSignal` + `valuation-scores@1` | Yes, and the observation is now separated from any comparison (`VALUATION_COMPARISON.md`) |
| Historical price volatility | `RiskSignal` | Measured cleanly, then **conflated twice** (below) |
| Portfolio suitability | `PortfolioFit` | Yes — measured per security against the account |
| Permitted position magnitude | `CapitalActionEnvelope` | Yes — and it reads **no** security-level risk term at all |

**The two conflations are both volatility's.** The same measurement
- gates the thesis (`risk_score > 70` → REJECT), and
- moves the ranking (as `safety_score`, one of the five terms averaged
  into conviction).

So a volatile security is penalised twice from one reading, and the
penalty in the second place is invisible: it lowers conviction whether
or not the gate fires.

**And the envelope cannot yet receive what the gate would give up.**
`CapitalPolicy` carries eleven decision-bearing fields: eight
account-level percentages (`max_single_position_pct`,
`starter_max_total_position_pct`, `maximum_acceptable_drawdown_pct` and
the rest), two freshness gates, and a reduce policy. There is no
per-security risk term anywhere in it, and the drawdown the envelope
does read is the **portfolio's**, not the security's. Moving
volatility to sizing is not a re-wiring: it is a new policy clause the
investor's own strategy file does not currently express.

---

## The three contracts, on this corpus

| | A (live) | B (sizing) | C (hybrid) |
|---|---|---|---|
| Rejects | 9 | 1 | 5 |
| Rejects a company with no adverse finding | **4** | 0 | 0 |
| Rejects a company with four analyst verdicts of 100 | **1** (PLTR) | 0 | 0 |
| Spares a company burning $20.9bn | no | **yes** (ORSTED.CO) | **yes** (ORSTED.CO) |
| Spares a company nothing was read about | no | **yes** (RIVN) | **yes** (RIVN) |
| Lets a distressed name outrank a strong one | no | **yes** (LUNR 58 > AMD 45) | no |

**A is refuted by its own outputs.** It rejects on price behaviour
alone, and four of its nine rejections have no adverse finding of any
kind behind them. It also rejects RIVN, about which nothing whatever was
read, and SPCX, which is a fund.

**C's discriminator does not survive the corpus.** Keyed on adverse
analyst verdicts it misses ORSTED.CO (−$20.9bn free cash flow scored
*adequate*) and spares RIVN (nothing read). Its apparent success — five
rejections that all look defensible — comes from the four names whose
weakness the analysts happened to band below 40, and the band is
`unsourced`. A rule that treats *unreadable* as *unadverse* inverts
Invariant 1.

**B answers the question correctly and is not shippable today.** It
preserves the thesis for AMD (PREPARE) and PLTR (INVESTIGATE) while
keeping UUUU rejected on its own merits, and it moves exactly 8 of 64
securities. What it does not do is constrain anything: with no
per-security term in the envelope, B currently converts a rejection into
an unconstrained INVESTIGATE.

---

## Conclusion

**B — MOVE VOLATILITY TO ACTION/SIZING.**

Severe historical volatility should not automatically reject an
otherwise strong company. It is one measurement, of one variable, over
one observed year, and on this corpus it rejected two companies whose
own analysts read growth, profitability, balance sheet and cash flow as
strong or better, and two more about which nothing adverse was known.

The ruling is a direction, not a patch. **Three things must land with
it, and each is named because the current veto is hiding one of them:**

1. **A per-security volatility term in the capital policy and the
   envelope.** Without it, "constrain the size" has nowhere to be
   expressed, and B is a rejection removed rather than a constraint
   applied. This is the owner's risk policy to write: a number, in
   `investor_strategy.json`, with the same provenance discipline every
   other capital constant now carries.
2. **A negative forward P/E must not band CHEAP.** Two securities
   currently score 80 on valuation for being expected to lose money, and
   under B that score reaches the ranking.
3. **Unmeasured quality must not be silently omitted from conviction.**
   Absence currently improves a mean it should constrain, which is how
   LUNR comes to outrank AMD.

Two further findings are recorded, and neither blocks the ruling:
momentum can be the sole licence for a conviction (5 of 64), and one of
the nine rejected securities is an ETF classed as a company.

**Not chosen, and why.** A is refuted. C reads better than it is: it
would decide on a band nobody sourced, and it would spare the two names
this platform knows least about.

---

## What this measurement does not establish

- **It does not measure returns.** Nothing here says a high-volatility
  security performs better or worse than a calm one; it says what this
  platform's own rules do with one, and what its own analysts say about
  the same company.
- **The counterfactual states are harness states.** Contract A's
  outcomes are exact — the gate fires before any account-level term is
  read — but under B a case may sit at INVESTIGATE or PREPARE depending
  on the two constants stated at the top. The *set* of securities that
  move is exact; the state each lands in is not.
- **One year, one provider.** Volatility, drawdown and beta are all read
  from a single vendor's daily closes over `1y`, and 60 of 64 quality
  readings are a provider proxy rather than a filing.
- **`pe-bands@1`, `risk-bands@1`, `risk-severity@1`, `provider-quality@1`
  and `conviction-mean@1` are all `UNSOURCED`.** Every band in this
  document is a house constant measured in `DECISION_PHILOSOPHY_AUDIT.md`,
  and naming them does not make them right.

---

## Owner's ruling — 2026-08-21

**Conclusion B is accepted.**

> Historical price volatility is not, by itself, a verdict on the
> investment thesis. The target contract moves security volatility from
> automatic thesis rejection into action eligibility and magnitude.
> Implementation is gated by the four prerequisite corrections below.

The ruling is a direction and not a licence to remove the veto. **The
absolute volatility veto stays in place until every prerequisite below
has landed**, and neither the implementation slice nor the research
slice that follows may remove it.

### The four prerequisites

1. **Negative or zero P/E must never band CHEAP.** A forward or
   trailing P/E at or below zero means earnings-based valuation is not
   measurable through P/E — it is not a cheap security. The exact
   reported value is preserved as evidence, and no other valuation
   method is substituted for it.
2. **Unequal score coverage must not produce a cross-company conviction
   ranking that reads as comparable.** Two convictions computed over
   different numbers of score families are not two points on one scale,
   and presenting them as a ranking asserts that they are.
3. **Non-company securities must not pass through company-quality
   analysis.** A fund has no earnings, no dividend policy of its own and
   no company profitability, and no proxy for those may produce a
   company-quality verdict for one.
4. **The Capital Action Envelope must carry an explicit per-security
   volatility constraint before the absolute veto is removed.**
   Otherwise B is a rejection deleted rather than a constraint applied.
   The constraint's values are the owner's to write.

### Clarifications carried with the ruling

- **Do not penalise missing quality as though missing information were
  bad company quality.** The two are different facts and only one of
  them is about the company.
- **Do not fill an absent score with zero.** Zero is the lowest score on
  the scale, which is a judgment; absence is the lack of one.
- **Until a new conviction contract is ruled, carry participation and
  prohibit cross-coverage ranking.** The number may be shown beside its
  coverage; it may not be ordered against a number computed over a
  different set of families.
- **Momentum alone must not be described as a business thesis.** Five of
  the sixty-four have strengths that are only momentum, and under DV2
  that is what licenses a conviction number at all.
- **Drawdown and volatility remain separate measurements.** Neither
  stands in for the other, and this document's Finding 1 — that no
  drawdown of any depth can reject — is not repaired by conflating them.
- **No risk threshold changes in the research PR.**

### What lands next, and what does not

The implementation slice that follows builds only the prerequisites
that need no new owner sizing threshold: **A** (negative P/E), **B**
(unequal conviction coverage) and **C** (the asset-class boundary,
including an audit of the stored corpus for other mismatches).
Prerequisite 4 is researched and not implemented — candidate policy
shapes for how annualised volatility constrains OPEN eligibility, ADD
eligibility, maximum total position and maximum incremental position
change, with maximum drawdown measured separately, and **no threshold
or multiplier invented**. That research lands as
`docs/architecture/SECURITY_VOLATILITY_CAPITAL_ENVELOPE.md` and must
conclude one of: **A. POLICY VALUES READY**, **B. MECHANISM READY,
OWNER VALUES REQUIRED**, or **C. NOT READY**.

Implementation and research are separate PRs, and both stop for owner
review.

### Already landed under this ruling

The second clarification's first half arrived with the owner's
amendments to #231: a conviction is now stated as *"computed from 4 of
5 score families"* with the absent families named, and
`ExecutiveDecision` carries the participation counts. That is
presentation and provenance only — the conviction arithmetic is
untouched, and prerequisite 2's ranking prohibition is the
implementation slice's work.
