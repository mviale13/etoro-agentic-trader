# Growth Metric Authority — the measurement

**Status: research, stopped for the owner's ruling. Nothing here is a
repair.**

The question set by the owner on 2026-08-23: the merged DIS dossier
presents filing-established earnings growth of **+132.7%** in its
Fundamentals section while the Growth Analyst's prose on the same page
reports Yahoo's **−48.3%** under the same unqualified label, *"Earnings
growth"*. Before the analyst or any decision is changed: what are the
correct authority and semantics for `revenue_growth` and
`earnings_growth`?

Everything below is measured against the held corpus — no funded
acquisition, no model call, no production-data mutation. The replay
harnesses are deterministic and read the stored doors only.

---

## 1. The overlap corpus

Two populations intersect: the 24 companies with statement consensus
(the filing route) and the 79 companies with a stored fundamentals
snapshot (the provider route, the live book). Growth coverage:

| population | count | members |
|---|---|---|
| filing growth established | 17 of 24 | AAPL, ALL, AXP*, CB, COF*, DIS, FITB*, GS*, HON, JPM*, MET, NWG*, PG, TRV, TSLA, UNP, WMT† (\* = earnings only, † = revenue only) |
| provider growth held (in book) | 42 of 79 | the held/watched equities |
| **both — the overlap** | **2** | **DIS, TSLA** |
| filing growth + a provider record that itself carries no growth | 2 | AAPL, PG |

Most filing-corpus companies (JPM, KO, WMT…) hold **no fundamentals
record at all** — the statement corpus was read for measurement, not
because the book holds them. AAPL and PG are a third state worth
naming: the provider record exists (2026-08-09) and **the provider
itself served no growth fields in it** — a record without the metric,
not a missing record.

## 2. The overlap, in full

| | filing value | filing period and calculation | provider value | provider observed | provider period/formula stated? |
|---|---|---|---|---|---|
| **DIS** revenue growth | **+3.35%** | FY2025 vs FY2024 (ended 2025-09-27; 10-K `0001744489-25-000155`): "Total revenues" 94,425 vs 91,361, checked cells | **+6.8%** | 2026-08-22 (fresh) | **No** — the payload carries the bare ratio |
| **DIS** earnings growth | **+132.65%** | same statement: "Net income" 13,431 vs 5,773 | **−48.3%** | 2026-08-22 | No |
| **TSLA** revenue growth | **−2.93%** | FY2025 vs FY2024 (ended 2025-12-31; 10-K `0001628280-26-003952`): 94,827 vs 97,690 | **+25.5%** | 2026-08-09 (dated, served as dated) | No |
| **TSLA** earnings growth | **−46.11%** | same statement: 3,855 vs 7,153 | **−3.0%** | 2026-08-09 | No |

Disagreement, absolute and directional:

| | absolute gap | direction |
|---|---|---|
| DIS revenue | 3.4 pp | same sign |
| DIS earnings | **181.0 pp** | **sign flip** (filing up, provider down) |
| TSLA revenue | **28.4 pp** | **sign flip** (filing down, provider up) |
| TSLA earnings | 43.1 pp | same sign |

Both overlap companies disagree materially, and each carries one sign
flip — in opposite directions. **These are not two observations of one
quantity in disagreement; they are two different quantities.**

## 3. What the provider says the fields mean

**Nothing, authoritatively.** Yahoo publishes no official documentation
of its `quoteSummary/financialData` fields — the public API programme
was retired years ago and the endpoint this platform's integration
reads is unofficial. The installed integration (yfinance 1.5.2)
requests the whole `financialData` module and passes it through; its
entire account of the fields is one comment — *"Financial KPIs
(revenue, gross margins, operating cash flow, free cash flow, and
more)"* — which names neither field. Third-party guides
([AlgoTrading101](https://algotrading101.com/learn/yahoo-finance-api-guide/),
[python-yahoofinance](https://python-yahoofinance.readthedocs.io/en/latest/api.html))
list the field names without defining period or formula.

**The period and formula of `revenueGrowth` and `earningsGrowth` are
undocumented. This measurement does not infer them.**

One thing *can* be measured without inferring: neither provider figure
is reproducible from any pair of figures this platform holds. DIS's
−48.3% matches no arithmetic over the filing's FY figures (+132.65%
net income, +3.35% revenue); TSLA's +25.5% matches none of its
(−2.93%, −46.11%). So the provider's window is **not** the filing's
fiscal-year window — and what it is cannot be established from held
evidence.

## 4. Where each value reaches, exactly

**The provider value** (`ValuationSnapshot.revenue_growth` /
`earnings_growth`):

```text
ValuationSnapshot ── CompanyFactsService ──> CompanyFacts
    └─> GrowthAnalyst (bands ≥30%→100 · ≥20%→85 · ≥10%→70 · ≥5%→55 ·
        ≥0%→45 · ≥−10%→25 · else 0; verdict ≥80 strong / ≥55 moderate /
        ≥40 weak / else declining)
        └─> GrowthOpinion ──> CompanyResearch.opinions[GROWTH]
            └─> DecisionEvidenceBuilder._research_findings
                └─> ONE ledger Finding (favourable ≥75 / adverse ≤40 /
                    else neutral, Dimension.RESEARCH)
                    └─> WORDING SURFACES ONLY:
                        · decision.key_strengths / key_risks
                        · committee supporting/opposing references
                        · blocker.despite quotes
                        · dossier analyst prose and the synthesis
                        · the executive writer's material
    └─> the dossier Fundamentals section (labelled provider fallback,
        #240 — the only surface that already names the authority)
    └─> the provider claim ledger (#134, descriptive)
```

**What it does NOT reach — each verified in source, then confirmed by
replay:**

- **No score.** The quality signal's factors are size, earnings (eps
  sign) and dividend; the company committee's vote is value + quality +
  momentum (`research` appears zero times in
  `company_committee_service.py`); the evidence score is cognitive
  confidence + committee confidence; conviction averages the five
  families, and growth is not one.
- **No gate.** `_research_findings`' own contract: *"weighed as
  evidence not gated"*.
- **No missing-evidence clause.** `_missing_evidence` names valuation,
  quality and risk gaps only — a silent growth analyst names nothing,
  so growth absence cannot reach `named_gaps` and **cannot starter-cap
  a capital envelope**.
- **No CIO branch, no blocker kind, no conviction term.** A blocker's
  `despite` list may *quote* a growth finding; the gate fires on
  scores the finding never touches.

**The filing value** (`FinancialUnderstanding` measures) reaches: the
dossier's filing section, the Fundamentals section's filing-evidence
rows (#240), the filing-grade analysts (`filing_growth`, which
delegates its rule table to `GrowthAnalyst` but reads established
measures), and the `movrvest financials` question surface. It reaches
no score and no gate either.

**The conviction subtlety, checked:** conviction is *withheld* when
`strengths` is empty (`conviction-mean@2`). A favourable growth finding
is a strengths member, so removing it could in principle withhold a
conviction. Measured below: it never does — no company's strengths
consist of the growth finding alone.

## 5. The replays

Three variants, replayed offline over every in-book company with any
growth input (44 at the analyst layer; 78 full decision pipelines ran
clean, holdings held constant so every difference is the variant's):

- **A — filing-first per metric**: filing value where established,
  provider fallback otherwise.
- **B — separate metrics**: no analytical change; the two values are
  named apart wherever both appear.
- **C — refuse the provider value analytically** where its period or
  definition is unstated (Yahoo states neither, so C refuses all 42
  provider readings; filing values stand).

### Analyst movements

| variant | verdict/finding movements | detail |
|---|---|---|
| A | **4 of 44** | DIS declining/adverse → moderate/neutral · TSLA moderate/neutral → **declining/adverse** · AAPL unknown → moderate/neutral · PG unknown → weak/neutral |
| B | 0 (by construction) | naming only |
| C | **44 of 44 touched; 40 silenced** | every provider-only company → unknown/no finding; the four filing companies as under A |

A's TSLA movement deserves its sentence: filing-first makes TSLA's
growth reading **worse** (the filing says revenue fell 2.9% and net
income fell 46%; the provider's unknown window says revenue grew
25.5%). Filing-first is not a euphemism pump.

### Decision movements — none, anywhere

| variant | state | conviction | blocker kind | envelope | wording lists |
|---|---|---|---|---|---|
| A | 0 | 0 | 0 | 0 | **2** (DIS's risks lose the declining line; TSLA's risks gain one) |
| B | 0 | 0 | 0 | 0 | 0 |
| C | 0 | 0 | 0 | 0 | **22** (14 lose a strengths line, 8 lose a risks line) |

No strengths list emptied under any variant, so no conviction was
withheld. The structural trace of §4 is therefore confirmed end to end:
**the growth fields decide sentences, and only sentences.**

### What C costs

C deletes the growth sentence from 40 of 44 companies — including
readings that are almost certainly directionally true (NVDA, MSFT,
AMZN "strong") — and buys **no decision correction**, because nothing
decides from the value. Its entire yield is the removal of 40 true
observations from investor-facing prose in exchange for period purity.

---

## 6. Conclusion

### B — SEPARATE METRICS READY

The measurement's central fact is that these are **two different
economic quantities**: one sign flip in each direction across the only
two overlap companies, a provider window that reproduces from no held
figure, and a provider that documents neither period nor formula. A
precedence between them (A) would treat them as one metric with two
sources — swapping the metric's window company-by-company inside one
name, and feeding fiscal-year values into rule bands that have only
ever read the provider's unknown window. A refusal (C) would delete 40
true observations to correct decisions that were never influenced.
Separation is what the data says they already are.

**The names.** The filing metric is *"Revenue growth (FY, from the
filing)"* / *"Earnings growth (FY, from the filing)"* — the period is
the two fiscal years the `stated` arithmetic already cites. The
provider metric is *"Revenue growth (provider, period not stated)"* /
*"Earnings growth (provider, period not stated)"*. No surface may
print either bare where the other could appear; the short badge forms
are the #240 standings already built ("Filing evidence" / "Provider
fallback").

**The periods.** The filing metric's period is established per company
by its own source citation. The provider metric's period is
**undocumented and must be presented as such** — never FY, never TTM,
never quarterly, exactly as #240 already words monetary fallbacks.

**The analytical roles.**

- The **filing metric** owns the Fundamentals section's evidence rows
  (built, #240) and the filing-grade question surfaces. It acquires no
  new analytical consumer in this slice.
- The **provider metric** keeps its current — and now *measured* —
  role: a descriptive, wording-level reading. `GrowthAnalyst` remains
  its consumer, and its finding sentence must carry the qualification
  (*"provider-reported, period not stated"*), so the analyst's claim is
  as qualified as the Fundamentals row quoting the same number. This is
  not cosmetic suppression, because the measurement established there
  is nothing analytical to suppress: the finding reaches no score, no
  gate, no conviction term and no envelope. The analyst decides
  sentences, and the sentences stop overclaiming.
- **No double-counting** is possible: nothing counts either metric
  today (§4), and the contract keeps both out of every score and gate
  until a future ruling licenses one — which would first require the
  provider metric's window to be established, or the filing metric to
  earn bands of its own.

**Acceptance under B**: DIS never displays +132.7% and −48.3% as the
same unqualified fact (each carries its name and period status);
nothing overrides filing evidence (the two never occupy one label);
different-period values are never presented as direct contradictions
(they are presented as different measurements); the provider fallback
stays descriptive with its period honestly absent; no threshold, band,
committee policy, conviction arithmetic or envelope policy moves.

### What A would need (not ready)

Filing-first *as an analyst authority* would be ready only with a
growth rule table calibrated for fiscal-year windows — the current
bands have only ever read the provider field — and a per-company
window disclosure on the metric identity itself. Both are new rules
the freeze reserves to an owner ruling.

### What C would need (not recommended)

Nothing technical — it is one line — but the measurement prices it:
40 of 44 companies fall silent about growth to fix zero decisions.
If the owner values period purity above reading breadth in investor
prose, C is buildable as measured.

---

## Appendix: harnesses

`/private/tmp/claude-501/growth_overlap.py` (the corpus),
`growth_replay.py` (analyst variants), `growth_decisions.py` (78 full
offline pipelines, three variants, stored doors only). Results:
`growth_overlap.json`, `growth_replay.json`, `growth_decisions.json`.
