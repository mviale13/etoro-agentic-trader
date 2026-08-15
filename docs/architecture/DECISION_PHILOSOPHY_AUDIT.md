# The Decision Philosophy Audit

**Status: measured, 2026-08-16. An investigation — nothing was repaired.**

The question this slice was given: *what is currently allowed to improve
or worsen an investment case, who gave it that meaning, and on what
evidence?*

The answer, stated first: **MOVRvest's decision layer is internally
coherent — its bands are deliberately aligned to its gates, its absences
genuinely refuse to become numbers — and its investment meanings are
almost entirely unlicensed.** Every threshold that decides whether a
company can be recommended traces back to an unsourced constant: a P/E
of 18, a market cap of $10bn, a dividend of anything, a daily price move
of half a percent, a weight vector of 0.40/0.35/0.25. The platform's own
crypto side has spent eleven slices building the discipline — named
rules, versioned contracts, licensed meanings — that its equity decision
path predates and lacks.

---

## 1. The dependency graph

Every value that can change `ArtificialCIO.decide()`, traced to origin.

```text
Yahoo forward_pe ──[<18|<28]──► CHEAP/FAIR/EXPENSIVE ──[80/55/25]──► valuation_score ──[≥60]──┐
                                                                                              │
Yahoo market_cap ──[≥$10bn: +1]─┐                                                             │
Yahoo eps        ──[>0: +1]─────┼─[3=HIGH,2=MED,else LOW]► HIGH/MED/LOW ──[80/62/40]──►       │
Yahoo dividend   ──[>0: +1]─────┘                            quality_score ◄──[80/62/40]──    │
                                                                  ▲            grounded       │
filing statements ──[favourable share ≥2/3, ≥2 answered]──► QualityBand (governs outright)    │
                                                                  │ [≥35 | ≥60 | ≥75]         │
price history vol ──[0.20|0.35|0.60]─┐                                                        │
price history dd  ──[0.20|0.40]──────┼─[worst level]► LOW/MOD/HIGH/SEVERE                     │
                                     └──[0.20/0.45/0.65/0.85 ×100]► risk_score ──[≤70]──┐     │
                                                                                        ▼     ▼
account concentration ──[max(.5, 1−c)]─┐                                        ┌──────────────────┐
market quote coverage ─────────────────┼─[mean ×100]─┐                          │  _determine_state │
constant 0.80 (risk analyst) ──────────┘             ├─[avg]► evidence_score ──►│  9 ordered gates  │
                                                     │        [≥30|≥60|≥75]    │                   │
BUY/HOLD/SELL vote strength ──[50+|s|×50]────────────┘                          │  conviction =     │
                                                                                │  mean(present)    │
policy target weight ──┐                                                        │  capped by state  │
policy concentration ──┼─[mean of rooms ×100]► portfolio_fit_score ──[≥60]─────►│  40/55/70/85/100  │
policy crypto cap ─────┘                                                        └──────────────────┘
                                                                                        ▲
Yahoo daily_change_pct ──[±0.5|±2.0]► BULLISH/NEUT/BEARISH ──[+1/0/−1 ×0.25]─┐          │
CHEAP/FAIR/EXPENSIVE ────────────────────────────────[+1/0/−1 ×0.40]─────────┼─[Σ≥0.5]► BUY ──► actionable_now
HIGH/MED/LOW ────────────────────────────────────────[+1/0/−1 ×0.35]─────────┘  [Σ≤−0.5]► SELL ─► analyst_veto
                                                                                              (REJECT, gate 2)
hard_reject: constructed False at the only call site — a dead input with total authority
security_evidenced: company is None — exits at INVESTIGATE before actionable_now is ever read
```

Sites: `value_signal_service.py`, `quality_signal_service.py`,
`momentum_signal_service.py`, `risk_signal_service.py`,
`business_quality.py`, `company_committee_service.py`,
`decision_evidence_builder.py`, `portfolio_fit.py`, `market_analyst.py`,
`portfolio_analyst.py`, `risk_analyst.py`, `decision_policy.py`,
`artificial_cio.py`.

---

## 2. Every decision-bearing transformation, classified

| # | transformation | site | class |
|---|---|---|---|
| 1 | volatility / drawdown → LOW…SEVERE | risk_signal_service (0.20/0.35/0.60; 0.20/0.40) | interpretation — **heuristic bands** |
| 2 | level → severity 0.20/0.45/0.65/0.85 | risk_signal.SEVERITIES | interpretation — arbitrary constants, *deliberately placed*: SEVERE sits above the policy's max 70 by design |
| 3 | risk_score ≤ 70 else REJECT | decision_policy | **risk constraint / preference** — the one gate with a written rationale |
| 4 | forward P/E <18 / <28 → CHEAP/FAIR/EXPENSIVE | value_signal_service | interpretation — **universal, sector-blind heuristic**; "historical market average" cited, unsourced |
| 5 | CHEAP/FAIR/EXPENSIVE → 80/55/25 | evidence builder VALUATION_SCORES | **preference** — aligned to the gates on purpose, so FAIR(55) < recommend-gate(60) is a *decision* that only cheap companies are recommendable |
| 6 | mcap ≥$10bn / eps>0 / dividend>0 → points | quality_signal_service | interpretation — **preference wearing a measurement's name**: large-cap and dividend-paying are favourable *by fiat* |
| 7 | points → HIGH/MED/LOW → 80/62/40 | BANDS + QUALITY_SCORES / BAND_SCORES | deterministic normalization of #6, ruler shared with grounded route |
| 8 | filing factors → favourable share ≥2/3 → band | business_quality (#81) | **evidence-quality assessment** — the one score with a licensed, measured basis |
| 9 | daily_change_pct ±0.5 / ±2.0 → BULLISH/BEARISH | momentum_signal_service | **heuristic** — one day's price move becomes a trend |
| 10 | 0.40·value + 0.35·quality + 0.25·momentum, BUY ≥0.5, SELL ≤−0.5 | company_committee_service | **investment preference** — an unsourced weight vector; the only three-signal combination on the platform |
| 11 | confidence = 50 + \|score\|·50 | company_committee_service | **unknown provenance** — confidence derived from the verdict's own strength, the exact defect `CommitteeOpinion`'s docstring names and fixed *for the other committee layer* |
| 12 | cognitive = mean(acct-concentration, quote-coverage, 0.80) | reasoning analysts | **accidental mixture** — two data-completeness readings and a constant |
| 13 | evidence_score = mean(cognitive×100, #11); ×0.6 with no company | evidence builder | heuristic over #11+#12 — the only never-None score, and it measures neither the security's evidence nor its quality |
| 14 | portfolio fit = mean of policy rooms ×100 | portfolio_fit | **portfolio constraint** — legitimately the investor's own policy |
| 15 | nine ordered gates → state | artificial_cio + decision_policy defaults 35/30/60/60/75/75/60/60/70 | **investment preference** — the ordering itself encodes priority (risk before quality before valuation), unsourced |
| 16 | conviction = unweighted mean of present scores, capped 40/55/70/85 | artificial_cio | heuristic — the caps quietly re-rank: CYD's measured 73 reports as 70 |
| 17 | BUY → actionable_now (final gate) | evidence builder | preference — #10's vote decides the last step to RECOMMEND |
| 18 | SELL → analyst_veto → REJECT (gate 2) | evidence builder | preference — #10's vote can end any case regardless of every score |

**Three claims, separated as the brief asked.** *Measurement* survives
intact everywhere — volatility, P/E, market cap and daily change are all
real readings, and absence stays absent (None is never zero, the
platform's genuine achievement here). *Interpretation* happens at #1,
#4, #6, #9 — unlicensed in all four. *Preference* happens at #5, #10,
#15, #17/#18 — unlicensed in all four, though #3 and #2 show that the
authors knew the difference: the risk gate's placement is argued in a
comment, which is the closest thing to a licensor the equity path has.

---

## 3. The hidden investment philosophy

What the constants, jointly, believe. Each entry answers: what fact,
what meaning, established where, could a reasonable investor prefer the
opposite, and can changing it alone change a decision.

1. **Only cheap companies are recommendable.** FAIR = 55 <
   recommend-valuation-gate 60, so a forward P/E of 18.1 permanently
   blocks RECOMMEND regardless of every other reading. Established
   nowhere. A growth investor prefers the opposite daily. Changing
   either constant alone flips decisions (proven, §6D).
2. **A dividend is a quality virtue.** Provider HIGH requires all three
   points, so a non-payer caps at MEDIUM 62 < recommend-quality-gate 75:
   **on the provider route, a company that pays no dividend can never be
   recommended.** Berkshire Hathaway fails this test by construction.
   Established nowhere.
3. **Big is good.** mcap ≥$10bn is a favourable finding. A small-cap
   value investor believes the opposite. Established nowhere.
4. **Today's price move is a trend.** +0.5% today = BULLISH, and that
   feeds 0.25 of the BUY vote that operates the *final* gate. This is
   the mechanism behind the standing observation that "per-security
   signals can flip between runs, which can flip a decision" — the
   flap is not noise on top of the system, it is input #9 working as
   built.
5. **Value matters 1.6× as much as momentum.** 0.40/0.35/0.25.
   Established nowhere.
6. **A strong vote is a confident vote.** confidence = 50 + \|score\|·50.
   The other committee layer's docstring calls this exact construction
   a defect and refuses it.
7. **Risk above 70 is intolerable; SEVERE volatility (≥60% annualised)
   must land above it.** The one preference with a written argument
   (`risk_signal.py` comment) — a heuristic, but an *owned* one.
8. **Priorities are: veto, then risk, then quality, then evidence, then
   valuation, then fit, then timing.** The gate ordering itself. A
   reasonable investor could invert several of these.

---

## 4. `DecisionEvidence.opinions` — the archaeology

Born in `af2f126` (2026-08-09, PR #77), replacing the older committee
output whose `Recommendation` (STRONG_BUY…SELL) named actions a
committee has no authority to name, and whose confidence float was
"an average of three numbers each of which was itself a judgment".

**It was intentionally informational from birth.** Producers: the two
`app/application/committees/` committees (Investment, Risk) via
`opinion_builder` — deterministic, named-rule stances over sensed
findings. Consumers: the synthesis builder's `Panel` (the "despite"
clause and committee-agreement display), four renderers, and the
`/today` route. All communication. The field's own comment in the CIO
says it is carried so "the synthesis can show an investor which
committee dissented from what was decided."

**One consumer *looks* decision-bearing and is unreachable.**
`_actionable_now` falls back to the Investment Committee's stance when
`company is None` — but `company is None` also sets
`security_evidenced=False`, and that gate exits at INVESTIGATE before
`actionable_now` is ever read. The fallback has never fired and cannot.

**So: not an abandoned mechanism — an anticipation.** #77's convergence
note says `CommitteeOpinion` is "the reference implementation of the
future Assessment layer". It is the equity side's half-built version of
what the crypto side finished in #117: a structural position, carried to
the decision layer and deliberately not consumed by it. The two sides
arrived at the same boundary from opposite directions.

Separately, the audit confirms **a second, older committee package is
still live**: `app/committee/` (chairman, cash, momentum, value, risk,
diversification) is consumed by `app/services/committee_service.py` and
the `movrvest committee` command — parallel to
`app/application/committees/`. The repository has been burned by
parallel committee implementations before. Recorded, not touched.

---

## 5. Where equity collapses fact → meaning → number

The crypto boundary (`InvestmentConsideration`) keeps three things
apart: the structural fact, the question contract that licenses its
meaning, and the (absent) investment effect. The equity path performs
all three in single expressions, at five sites:

| site | fact | silent meaning step | number |
|---|---|---|---|
| value_signal | P/E = 17 | "below average *is cheap, and cheap is good*" | 80 |
| quality_signal | pays a dividend | "*distribution is a quality virtue*" | +1 → 80/62/40 |
| momentum_signal | +0.6% today | "*today's move is a trend*" | +1 |
| company_committee | three bands | "*these three, at 40/35/25, sum to an action*" | BUY |
| decision gates | five scores | "*this ordering is what prudence means*" | state |

These five are the candidates for the missing investment-policy layer.
Note what is *not* a candidate: portfolio fit (the investor's own
policy), the grounded quality band (licensed by #81's measurements), and
the CIO's absence-handling (None never becomes a number — audited and
clean throughout).

---

## 6. The live corpus, measured

Fourteen unique securities (the portfolio), the real pipeline, no
journal, no network.

### A. The inputs and the decisions

| symbol | qual | evid | val | risk | fit | act | veto | state | conv |
|---|---|---|---|---|---|---|---|---|---|
| BTC | — | 68 | — | 65 | 36 | n | n | INVESTIGATE | 46 |
| ETH | — | 68 | — | 65 | 52 | n | n | INVESTIGATE | 52 |
| BNP.PA | 62 | 78 | 80 | 45 | 78 | n | n | PREPARE | 71 |
| VOW3.DE | 80 | 93 | 80 | 45 | 77 | Y | n | RECOMMEND | 77 |
| CYD | — | 68 | — | — | 78 | n | n | INVESTIGATE | 70 |
| UMI.BR | 62 | 84 | 80 | 65 | 78 | Y | n | PREPARE | 68 |
| AZN | — | 68 | — | — | 77 | n | n | INVESTIGATE | 70 |
| ETOR | 40 | 73 | 80 | 65 | 77 | n | n | INVESTIGATE | 61 |
| SPCX | 40 | 80 | 25 | 85 | 77 | n | **Y** | REJECT | 40 |
| SOL | — | 74 | — | 65 | 69 | n | n | INVESTIGATE | 59 |
| NOVO-B.CO | 80 | 93 | 80 | 65 | **59** | Y | n | PREPARE | 69 |
| ADBE | 62 | 84 | 80 | 65 | 78 | Y | n | PREPARE | 68 |
| META | 62 | 78 | 80 | 65 | 77 | n | n | PREPARE | 66 |
| DIS | 80 | 87 | 80 | 45 | 77 | Y | n | RECOMMEND | 76 |

Only DIS carries a grounded (filing-based) quality band; every other
quality score is the provider triad.

### B. What varies, what is inert

- **valuation takes two values in the entire corpus**: 80 or 25. No
  equity reads FAIR today — the corpus has never exercised its own
  FAIR band, and the FAIR wall (below) has therefore never been *seen*,
  only latent.
- **evidence_score spans 68–93.** Its two lower gates (30, 60) have
  never bound; **MONITOR is unreachable in practice** — with the risk
  analyst's constant 0.80 and quote coverage near 1.0, the cognitive
  term cannot fall low enough. A decision state exists that the live
  system cannot produce.
- **hard_reject is constructed `False` at its only call site.** A dead
  input with total authority: flipping it moves 13/14 securities.
- **risk never rejects**: max observed 85 (SPCX), but SPCX is already
  vetoed at gate 2 — the risk gate has never been the binding gate.
- NOVO-B.CO sits at fit **59** against the 60 gate: the one live
  binding of portfolio fit, and it is one point wide.

### C. Causal authority (change one input, hold the rest)

| input | state-changing trials | note |
|---|---|---|
| quality_score | 79/126 | the dominant score — binds on 8/14 today |
| evidence_score | 44/112 | can reach every state incl. the otherwise-unreachable MONITOR |
| risk_score | 28/98 | authority exists; never exercised live |
| valuation_score | 8/84 | authority concentrated entirely at the RECOMMEND boundary |
| portfolio_fit | 6/56 | narrowest |
| analyst_veto | 13/14 flips | **the single most powerful bit in the system** — one committee vote |
| actionable_now | 2/14 flips | only the two RECOMMENDs feel it; upstream gates mask it elsewhere |
| security_evidenced | 7/14 flips | |

### D. The FAIR wall, demonstrated

A perfect case — quality 100, evidence 100, risk 10, fit 100,
actionable, no veto — with valuation FAIR (55): **PREPARE**, "valuation
does not currently support action." Same case at CHEAP (80):
**RECOMMEND**. One band constant is the entire distance.

### E. Historical corroboration

The decision journal's recorded history (#122/F3) already showed
VOW3.DE moving PREPARE → INVESTIGATE → RECOMMEND within five hours
because quality and valuation *stopped being measurable* — provider
availability, not evidence content, has been the largest historical
mover of decision states. The audit explains why: the scores are thin
wrappers over single provider fields, so a field's absence is a state
change.

---

## 7. Verdict on the architectural question

**The decision philosophy is implicit.** It is not *incoherent* — the
bands are aligned to the gates deliberately, the comments repeatedly
show the authors distinguishing measurement from policy, and absence
handling is disciplined everywhere. But of the eighteen decision-bearing
transformations, **one** (grounded quality, #81) has a measured,
licensed basis; **one more** (the risk gate placement) has a written
argument; the other sixteen are constants nobody has established,
several of which a reasonable investor would invert, and at least four
of which (FAIR wall, dividend wall, daily-move momentum, veto power)
silently encode a specific, contestable investment style: *large-cap
dividend-paying value investing with a one-day timing trigger*.

Per the brief: the investigation demonstrates implicitness, and stops.

---

## 8. Recommendation: the smallest next boundary

Not a policy engine, and not new philosophy. The platform already owns
the right pattern, three times over: S5's named scoring rule
(`market-significance-floor@1`), #119's licensed meanings
(`EvidenceDemand.matters_because`), and #128's versioned
`LICENSED_EFFECTS`. The equity path lacks exactly that discipline.

**The smallest boundary: every decision-bearing constant becomes a
named, versioned rule, and `ScoreBasis` carries the rule's identity
beside the prose it already carries.** No behaviour change, no
threshold moved, no new layer — the same numbers, now signed. `forward
P/E < 18` becomes `pe-bands@1`; `0.40/0.35/0.25 → BUY` becomes
`signal-vote@1`; the gate ordering becomes `decision-gates@1`.

What that buys, concretely: the owner can then license, adjust or
retire rules *one at a time*, each with its reason written down, the
way every crypto rule already works — and a future investment-policy
layer has an inventory of exactly which meanings it must take ownership
of, rather than an archaeology project. The FAIR wall and the dividend
wall become one-line, named decisions for the owner instead of
side-effects of two constants aligned in different files.
