# Six banks with no top line, and the two that band on a quantity we refuse elsewhere

**Status: research, BQ21. Read-only over held evidence plus free
deterministic re-reads of the filings already named. No model call, no
new observation, no production write, no rule, threshold or vocabulary
change. Stopped for ruling.**

The question was whether the six no-top-line companies are an extraction
defect, a statement-representation fact, or the quality model asking the
wrong question. The answer is that they are **not one condition**, and
that the decisive finding is not about them at all.

> **`Total revenues net of interest expense` is refused and `Total net
> revenue` is accepted, and they are the same quantity.** BQ11 refused
> AXP's label saying it is *"a different economic quantity from
> consolidated total revenue, and refused for that reason rather than for
> its wording"*. Goldman's accepted `Total net revenues` is
> `Total non-interest revenues` + `Net interest income`, and JPMorgan's
> accepted `Total net revenue` is `Noninterest revenue` +
> `Net interest income` — both **net of interest expense**, both verified
> exact to the unit. One quantity, three labels, two accepted and one
> refused, on wording alone.
>
> **`FinancialModel.BANK` governs zero of twenty-four companies**, and
> would change nothing for the six if it did: its profitability question
> narrows to net margin, whose denominator is `TOTAL_REVENUE`.
>
> **The candidate that gives coverage is the one that manufactures the
> fake comparability**, and it is measured rather than argued: on the
> platform's own net-margin table, a constructed bank income base reads
> **excellent for six of seven banks** while **zero of four insurers**
> and Procter & Gamble read below it.

---

## 0. The UNP promotion, first

BQ20's recommended production action, executed before any research.

```bash
movrvest statement-import data/experiments/statement-observations/bq19/statements --apply
```

| Gate | Result |
|---|---|
| appended through the ordinary importer | **5**, no observation selected by hand |
| UNP band | **UNKNOWN → MEDIUM 62** — 1 favourable of 3 answered |
| aggregate | **HIGH 4 · MEDIUM 5 · LOW 3 · UNKNOWN 12** |
| second execution | **duplicate=5, 0 appended**, aggregate unchanged |

UNP is the only company that moved. The band lands because BQ20's rule
withdraws five stale absences, and it withdraws them for one concept:

```text
total_revenue      "Total operating revenues" = 24,510   given=5    withdrawn=5
gross_profit       no figure located                     given=10   withdrawn=0
operating_income   "Operating income" = 9,846            given=10   withdrawn=0
net_income         "Net income" = $ 7,138                given=10   withdrawn=0
```

Concept-locality, measured on production rather than on a fixture.
Merged as #169; the live control in `tests/test_absence_supersession.py`
now composes both sides from the one store and asserts that locality.

---

## 1–2. The statement shape of each of the six, and why the total is absent

Every figure below is the filer's own row label and printed value, read
structurally from the document this platform already names for the
symbol. No model was asked.

### COF — 10-K, $m

`Total interest income` 58,696 · `Total interest expense` 15,818 ·
**`Net interest income` 42,878** · `Provision for credit losses` 20,655 ·
`Net interest income after provision` 22,223 ·
**`Total non-interest income` 10,556** · `Total non-interest expense`
30,498 · `Income from continuing operations before income taxes` 2,281 ·
**`Net income` 2,453**

**Why the total is absent: it is out of the concept's scope, not out of
the document.** COF's management report prints

```text
Net interest income 42,878 · Non-interest income 10,556 · Total net revenue 53,434
```

and 42,878 + 10,556 = **53,434 exactly**. The filer states a
consolidated total and states this construction as its definition — it
even defines *"Total net revenue margin … total net revenue for the
period divided by average interest-earning assets"*. It is simply not on
the face of the audited statement, and `TOTAL_REVENUE` is scoped to the
statement. **This is the only one of the six where the filer publishes
the figure.**

### FITB — 10-K, $m

`Total interest income` 9,903 · `Total interest expense` 3,921 ·
**`Net Interest Income` 5,982** · `Provision for credit losses` 662 ·
`Net Interest Income After Provision` 5,320 · **`Total noninterest
income` 3,035** · `Total noninterest expense` 5,144 ·
`Income Before Income Taxes` 3,211 · **`Net Income` 2,522**

**Why absent: genuine representation.** No consolidated total on the
face and none anywhere in the located management report or business
description. Both addends are printed.

*A note on the shape tool.* `movrvest statement-shape FITB` reports
`total_revenue` as **UNREAD**, naming `Wealth and asset management
revenue`. That is `CONCEPT_WORDS` working as designed — bare `revenue`
weakens an absence one-directionally — but the label it found is a fee
**component**, not a hidden total. The downgrade is correctly cautious
and is not evidence that a total exists. Same for MTB (`Mortgage banking
revenues`) and for DB's `net_income` (`Net income (loss) from equity
method investments`).

### MTB — 10-K, $m

`Total interest income` 10,486 · `Total interest expense` 3,538 ·
**`Net interest income` 6,948** · `Provision for credit losses` 505 ·
**`Total other income` 2,742** · `Total other expense` 5,493 ·
`Income before taxes` 3,692 · **`Net income` 2,851**

**Why absent: genuine representation** — and the non-interest block is
labelled `Other income`, not `Noninterest income`, so even the addend
has no shared vocabulary across the six. Its management report does
print `Total revenue`, three times, and each one is a **segment** figure
(2,947 · 4,868 · 1,562, summing to 9,377 against a consolidated
6,948 + 2,742 = 9,690). A segment total is not a consolidated total.

**Second blocker: MTB holds no income-statement consensus at all.**
BQ15's audit withdrew all five readings. It is not at the revenue
question; it has no readings.

### RF — 10-K, $m

`Total interest income` 7,073 · `Total interest expense` 2,082 ·
**`Net interest income` 4,991** · `Provision for credit losses` 470 ·
**`Total non-interest income` 2,535** · `Total non-interest expense`
4,313 · `Income before income taxes` 2,743 · **`Net income` 2,156**

**Why absent: genuine representation.** No total anywhere; its
management report was located at 96 characters, which is a location
failure rather than a filer silence, so the *document-wide* claim is
weaker than FITB's. **Second blocker: no consensus held** — BQ15
withdrew all five readings.

### DB — 20-F, IFRS, €m

`Interest and similar income` 44,440 · `Interest expense` 28,766 ·
**`Net interest income` 15,673** · `Provision for credit losses` 1,707 ·
`Net commission and fee income` 10,891 · **`Total noninterest income`
15,761** · `Total noninterest expenses` 20,658 · `Profit (loss) before
income taxes` 9,069 · **`Profit (loss)` 6,814** · `Profit (loss)
attributable to Deutsche Bank shareholders` 6,606

**Two absences, and only one is the filer's.** No consolidated total —
genuine representation. But **`net_income` is absent for a vocabulary
reason**: `CONCEPT_LABELS[NET_INCOME]` accepts `profit for the period`
and `profit for the year` and refuses the bare IFRS `Profit (loss)`.
Verified: `matches_concept(NET_INCOME, "Profit (loss)")` is `False`.
This is BQ19's shape, one concept over, and free to falsify.

### MUFG — 20-F, ¥m

`Interest income:` components → bare **`Total`** 8,613,865 ·
`Interest expense:` components → bare **`Total`** 4,929,611 ·
**`Net interest income` 3,684,254** · `Provision for credit losses` ·
`Non-interest income:` components → bare **`Total`** ·
`Non-interest expense:` components → bare **`Total`** 3,741,366

**Why absent: extraction, and the statement is truncated.** Two separate
facts:

- MUFG's four subtotals are labelled `Total` with no qualifier, so none
  is groundable to a concept — a bare `Total` under `Non-interest
  income:` is owned by its heading, and this platform's concept check
  reads the row label alone;
- **the located section ends at row 45.** `income_statement_text` is
  3,162 characters and contains **zero** occurrences of *net income*.
  Pre-tax income, tax and the bottom line are outside what was located
  (`contenders=2`).

**A residual hole this exposes, recorded not fixed.** `evidences_absence`
guards against claiming *the filer prints no such line* on an unread
statement by requiring `is_read` — some concept located. MUFG's
`net_interest_income` **is** located, so `is_read` is `True`, and the
platform therefore reports `net_income: the statement prints no such
line` about a section that stops before it. The guard catches a statement
read *not at all* and not one read *partially*.

### Summary — five distinct causes, not one

| | first decisive cause | consensus held? | net income? | factors answered |
|---|---|---|---|---|
| **COF** | total printed in the management report, out of concept scope | yes, 5 | yes | 1 of 3 |
| **FITB** | filer prints no consolidated total; both addends printed | yes, 5 | yes | 1 of 3 |
| **MTB** | same; MD&A total is per-segment only | **no — 5 withdrawn** | — | 0 |
| **RF** | same; MD&A not located | **no — 5 withdrawn** | — | 0 |
| **DB** | no total **and** `Profit (loss)` refused by vocabulary | yes, 5 | **no** | 0 of 3 |
| **MUFG** | bare `Total` labels **and** the located statement is truncated | yes, 5 | **no** | 0 of 3 |

**Is any of it a parser failing to preserve a printed total? No.** One
candidate was investigated and cleared: DB's IFRS table carries a
`Notes` column, so rows with a note reference put `5` in the first
numeric position and rows without one do not. A naive left-to-right
reader takes the note number as the figure — but `row_figures` pairs
cells with the header above them and preserves the empty cell, so
`Net interest income` reads 15,673 under `2025` and `Total noninterest
income` reads 15,761 under `2025`, both correct. The hazard is real for
any reader that indexes; the platform's reader is not one.

**Is any total available only by calculation? Yes, for four** — COF,
FITB, MTB and RF each print both addends and no sum. **No calculated
fact was created in this slice.**

---

## 3. The GS/JPM control — lexical compatibility, not economic assessability

| | accepted top line | its components | exact? |
|---|---|---|---|
| **GS** | `Total net revenues` **58,283** | `Total non-interest revenues` 44,724 + `Net interest income` 13,559 | **58,283 — EXACT** |
| **JPM** | `Total net revenue` **182,447** | `Noninterest revenue` 87,004 + `Net interest income` 95,443 | **182,447 — EXACT** |

Neither prints a gross profit line and neither prints an operating
income line. Both ride entirely on **net margin**, and both answer all
three factors:

| | profitability | revenue growth | earnings growth | band |
|---|---|---|---|---|
| GS | net margin **29.5%** → excellent | +8.9% → moderate | +20.3% → strong | **HIGH 80** (2 of 3) |
| JPM | net margin **31.3%** → excellent | +2.8% → weak | −2.4% → declining | **MEDIUM 62** (1 of 3) |

### The core research question, answered

**Merely more lexically compatible.** The four US regionals print the
identical two addends in the identical structure and the identical order;
GS and JPM typeset one additional row containing their sum. Nothing
economic separates them — and the platform's own vocabulary decides the
outcome:

| printed | in `CONCEPT_LABELS`? | outcome |
|---|---|---|
| GS `Total net revenues` | yes | **accepted**, HIGH 80 |
| JPM `Total net revenue` | yes | **accepted**, MEDIUM 62 |
| AXP `Total revenues net of interest expense` 72,229 | no — **BQ11 refused it** | UNKNOWN |
| C `Total revenues, net of interest expense` 85,225 | no — **BQ11 refused it** | UNKNOWN |
| COF/FITB/MTB/RF — the sum, unprinted | n/a | UNKNOWN |

**BQ11 refused a quantity that is accepted twice over.** Its test says
so in its own words:

> *"AXP and Citigroup print revenue after deducting interest. A different
> economic quantity from consolidated total revenue, and refused for that
> reason rather than for its wording."*

Goldman's `Total net revenues` is that quantity: `Net interest income` is
already interest income less interest expense, so the total is non-interest
revenue plus a net-of-interest-expense figure. So is JPMorgan's. BQ19
flagged this in passing (*"a real inconsistency for whichever slice argues
BQ11's ruling"*); it is now measured, and it is the gate on everything
below.

**And it is load-bearing in both directions.** Applying BQ11
consistently, on a copy of the consensus in memory:

| | HIGH | MEDIUM | LOW | UNKNOWN |
|---|---|---|---|---|
| production today | 4 | 5 | 3 | 12 |
| net-of-interest-expense totals refused | **3** | **4** | 3 | **14** |

GS **HIGH → UNKNOWN**, JPM **MEDIUM → UNKNOWN**. Two bands, and they
are the only two companies in the corpus carrying such a label.

---

## 4. What `FinancialModel.BANK` actually changes

**It exists, it is coherent, and it is unreachable.**

What it defines (`app/domain/financial_question.py`, `OWNED`):

- asks all five questions;
- **narrows** profitability to `NET_MARGIN` alone, on the measured
  grounds that a bank prints neither gross profit nor operating income;
- **declines** `LEVERAGE` with a worded reason and three named needs
  (CET1, Tier 1, the regulatory leverage ratio);
- **declines** `CASH_GENERATION` likewise.

What it does **not** define:

- **no bank-specific statement concept.** `NET_MARGIN`'s recipe is
  `NET_INCOME / TOTAL_REVENUE` (`app/services/financial_engine.py`,
  `RECIPES`), so BANK still requires `TOTAL_REVENUE` — for profitability
  **and** for revenue growth, two of its three quality questions;
- **no bank-specific measure.** `FinancialMeasure` has no member a bank
  answers differently.

**Is `NET_INTEREST_INCOME` represented? Yes — and consumed by nothing.**
It is a `StatementConcept`, established for nine companies (AXP, BCS,
COF, DB, FITB, GS, JPM, MUFG, NWG), and it **appears in no recipe**. Its
only consumer is `StatementLanguage`.

**Measured: BANK changes no band anywhere.** Running both models over the
same held understanding:

| | GENERIC | BANK |
|---|---|---|
| GS | HIGH 80, 2 of 3 | **HIGH 80, 2 of 3** |
| JPM | MEDIUM 62, 1 of 3 | **MEDIUM 62, 1 of 3** |
| COF | UNKNOWN, 1 of 3 | **UNKNOWN, 1 of 3** |
| FITB | UNKNOWN, 1 of 3 | **UNKNOWN, 1 of 3** |

The only difference is the sentence: GENERIC says *"Gross margin needs
gross_profit, which is not established"*, BANK says *"Net margin needs
total_revenue, which is not established"*. **Today, BANK is a wording
distinction.**

**And it governs nothing.** `StoredPlaybookSelection.governing` over all
24 companies returns `generic` for every one, with `from_playbook=None`
for every one — because no narrative knowledge is held at all
(*"No filing has been read for JPM"*), so `select_grounded` can never
produce a playbook and `model_for` is never reached with
`PlaybookKind.BANK`. It is unreachable a second time over as well: the
executive pipeline calls `quality_of(symbol, financial)` with the default
`GENERIC` and passes no model.

**Which held concepts could support profitability without new data?**
`NET_INCOME`, `NET_INTEREST_INCOME`, `TOTAL_LIABILITIES`, `TOTAL_EQUITY`,
`OPERATING_CASH_FLOW`, `CAPITAL_EXPENDITURES`. There is **no concept for
noninterest income, total interest income, total interest expense, or
pre-tax income** — so every construct richer than net income over net
interest income needs a new concept, and a new concept needs a new
reading.

---

## 5. The candidate profitability shapes

| | inputs printed | mechanically checkable | coverage, the six | GS/JPM | verdict |
|---|---|---|---|---|---|
| **A** net income / printed total revenue | only where the filer prints the total | yes — one ratio, one column, one table | **0 of 6** | 2 of 2 | the status quo |
| **B** net income / net interest income | **yes, all held today** | yes, same ratio | 2 of 6 (COF, FITB) | 2 of 2 | **refuted — see below** |
| **C** net income / (NII + noninterest income) | needs a **new concept**; label present for 5 of 6 | the sum is two checked cells under one header | 2 of 6 realisable | 2 of 2 | **blocked by BQ11** |
| **D** pre-provision profit / a filer aggregate | needs new concepts; **no filer of the six prints pre-provision profit** | — | 0 | 0 | nothing to read |
| **E** a bank-specific factor asserting no equivalence | — | — | — | — | no rule table exists |

### B is refuted by its own numbers

| | COF | FITB | JPM | **GS** | every insurer | every industrial |
|---|---|---|---|---|---|---|
| net income / NII | 5.7% | 42.2% | 59.8% | **126.7%** | undefined | undefined |
| actual net margin | — | — | 31.3% | 29.5% | 4.4–17.9% | 4.1–26.9% |

**It exceeds 1, so it is not a margin.** Goldman keeps more than its
entire net interest income because it is mostly a fee and trading
business — B ranks a bank by its revenue *mix*, not its profitability.
And `NET_INTEREST_INCOME` is absent for all four insurers and all nine
industrials, so B is **undefined for 13 of 24 companies** and can never
be compared across the corpus.

### C is the filer's own definition, verified twice

`NII + noninterest income` reproduces GS's printed `Total net revenues`
and JPM's printed `Total net revenue` **exactly**, to the unit. It is
not this platform's invention; it is the identity used by the two filers
who print a total. Simulated with the platform's own threshold tables and
`band_for`, reading figures through `row_figures`:

| | base(t) | base(t−1) | margin | profitability | rev growth | earn growth | band |
|---|---|---|---|---|---|---|---|
| COF | 53,434 | 39,112 | 4.59% | weak | +36.62% strong | −48.36% declining | MEDIUM |
| FITB | 9,017 | 8,479 | 27.97% | excellent | +6.35% moderate | +8.99% moderate | MEDIUM |
| MTB | 9,690 | 9,279 | 29.42% | excellent | +4.43% weak | +10.16% moderate | MEDIUM |
| RF | 7,526 | 7,083 | 28.65% | excellent | +6.25% moderate | +13.89% moderate | MEDIUM |
| DB | 31,434 | 31,505 | 21.68% | excellent | −0.23% declining | +52.06% strong | HIGH |
| MUFG | — | — | — | — | — | — | net income unavailable |
| **GS** | 58,283 | 53,512 | 29.47% | excellent | +8.92% moderate | +20.31% strong | **HIGH — matches production** |
| **JPM** | 182,447 | 177,556 | 31.27% | excellent | +2.75% weak | −2.43% declining | **MEDIUM — matches production** |

The harness validates itself: GS and JPM reproduce their live bands
exactly from the constructed base, because the construct equals the
printed total.

**COF's own management report publishes 53,434 and 39,112**, the two
figures the construct produces — so for COF the sum is not even
arithmetic this platform performs alone.

---

## 6. Fake comparability — measured, and already live

The same net-margin rule table scores every company: ≥20% excellent,
≥10% strong, ≥5% moderate, ≥0% weak.

| excellent (≥20%) | strong (10–20%) | moderate / weak |
|---|---|---|
| AAPL 26.92% · UNP 29.12% · **GS 29.47%** · **JPM 31.27%** | PG 18.55% · CB 17.88% · ALL 15.17% · DIS 14.22% · TRV 12.88% · HON 12.75% | MET 4.41% · TSLA 4.07% |

Add candidate C's constructed bases: FITB 27.97%, MTB 29.42%,
RF 28.65%, DB 21.68% — **four more excellents.**

> **Six of seven banks would read excellent. Zero of four insurers do.
> Two of six industrials do. Procter & Gamble scores strictly worse on
> profitability than every solvent regional bank in the corpus.**

The cause is structural, not incidental: the bank base already excludes
interest expense, a bank's largest single cost. COF's gross income is
58,696 + 10,556 = 69,252 and its constructed base is 53,434 — the
denominator is **23% smaller** before any judgement is made. An
industrial's revenue excludes nothing.

**And this is not a risk the candidate would introduce. It is a defect
production already has.** GS's 29.5% and JPM's 31.3% are net-of-interest-
expense margins, scored against AAPL's 26.9% on gross sales by one
threshold table. JPMorgan's single favourable point — the one that makes
it MEDIUM rather than LOW — is exactly that margin.

### The architecture choice

| | option | verdict |
|---|---|---|
| **A** | one normalized profitability factor with model-specific input semantics | **unavailable offline.** It needs `FinancialModel.BANK` to be selectable, which needs a grounded playbook, which needs funded **narrative** re-observation of the corpus (no filing has been read for any company). Nothing in the statement store can select it, and `StatementLanguage` → `FinancialModel` is forbidden by the accepted domain boundary. |
| **B** | separate bank semantics feeding the same qualitative direction | **refused on evidence.** This is precisely §6's measurement: the same word *excellent*, reached on a denominator two-thirds the size, entering the same band arithmetic. It is Invariant 10 in its semantic form — an established number is authority to report the number, not to invent what it means. |
| **C** | a different bank factor altogether | **not earned.** No rule table exists, nothing in the corpus grounds a threshold, and S5.3's ruling applies — *magnitude does not make quality*. Seven banks is not a corpus for a new band. |
| **D** | **no safe offline remedy from existing statements** | **this one, for the profitability factor.** |

**D is the honest answer, and it is not a dead end** — because the
profitability factor is not the first blocker for four of the six, and
because the one thing standing between COF/FITB and a band is a ruling
this platform owes itself anyway.

---

## 7. Leverage — what the best-supported reading does for each of the six

| | under candidate C, if it were admitted | without a ruling on the quantity |
|---|---|---|
| **COF** | **immediately assessable** — MEDIUM, 3 of 3, and the filer publishes both figures | unaffected |
| **FITB** | **immediately assessable** — MEDIUM, 3 of 3 | unaffected |
| **MTB** | **partially more complete, still UNKNOWN** — no consensus held; needs paid re-observation first, then bands MEDIUM | unaffected |
| **RF** | **partially more complete, still UNKNOWN** — same | unaffected |
| **DB** | **still UNKNOWN** — needs a `NET_INCOME` label for `Profit (loss)` *and* the base. With the label alone it answers earnings growth only: 1 of 3 | unaffected |
| **MUFG** | **unaffected** — its subtotals are bare `Total` and its statement is truncated before net income. No vocabulary and no base reaches it |

**Directly addressable: 2 of 6** (COF, FITB), and only after a ruling
and a funded re-reading under a new concept. **4 of 6 are blocked by
something that is not the profitability question**: two hold no readings
at all, one is refused on a bottom-line label, one was never fully
located.

No production value was altered to obtain this. The simulation runs the
platform's own `_metric_score`, `_verdict`, `sense_of` and `band_for`
over figures read with `row_figures`; the only arithmetic added is the
candidate sum itself, stated as the candidate under evaluation.

---

## 8. False positives outside the six

The discriminator any bank rule would key on, swept over the whole corpus
from the store:

| | `NET_INTEREST_INCOME` | `PREMIUM_REVENUE` | `StatementLanguage` |
|---|---|---|---|
| AXP, BCS, COF, DB, FITB, GS, JPM, MUFG, NWG | **established, 9 of 9** | none | interest based |
| CB, MET, TRV | none | **established, 3 of 3** | insurance based |
| AAPL, ALL, DIS, HON, KO, PG, TSLA, UNP, WMT | none | none | neither established |

**Zero overlap. No insurer and no industrial carries the bank
discriminator, and the three insurers are separated positively by their
own concept.** The insurer/bank confusion `FINANCIAL_LANGUAGE_CORPUS`
measured came from *statement shape* — absent gross profit, absent
operating income — and the two positive concepts do not reproduce it.

**This does not license a rule.** It is the same 5-of-5, zero-false-
positive result `FINANCIAL_LANGUAGE_EVIDENCE` already recorded, and
`StatementLanguage` is still connected to nothing on purpose:
`FINANCIAL_DOMAIN_BOUNDARY` forbids connecting it to `FinancialModel`
*even as one term of a larger rule*. A clean discriminator for
*financial language* remains not a discriminator for *prudential
status*.

What it does establish is narrower and useful: **a candidate keyed on
the presence of the two bank concepts would not fire on any insurer or
industrial in this corpus.** That is a false-positive measurement, not a
warrant.

---

## 9. Paid acquisition

**No conclusion in this report required funded re-observation, and none
was performed.** Everything came from held statement consensus plus free
deterministic re-reads of filings already named by the resolver
(`statement-shape` and `row_figures` over `PrimarySourceResolver` — SEC
EDGAR, no model, nothing stored). The owner's expectation was NO; it is
measured NO.

What *realising* a remedy would cost, stated separately:

| | free | paid |
|---|---|---|
| rule on net-of-interest-expense totals | **entirely** — the sweep, the arithmetic and the corpus impact are all offline | — |
| falsify `Profit (loss)` as a `NET_INCOME` form | **yes** — one sweep, BQ19's method | 5 readings for DB to realise it, and DB still would not band |
| introduce a noninterest-income concept | the concept, the recipe and the tests | **10 readings** (COF, FITB at quorum 5) to realise a band |
| MTB, RF | — | **10 readings**, and BQ18 already measured that re-observation alone leaves both UNKNOWN |
| MUFG | — | **no amount of reading fixes a locator** |

---

## 10. Recommended implementation slice — exactly one

> ### One quantity, one ruling: what is a revenue net of interest expense?
>
> Resolve the contradiction between BQ11's refusal and the two accepted
> labels that carry the same quantity, and measure each outcome against
> the live corpus before choosing.

**The defect**: the platform accepts `Total net revenue(s)` as
`TOTAL_REVENUE` and refuses `Total revenues net of interest expense` on
the stated ground that the latter is *"a different economic quantity …
refused for that reason rather than for its wording"*. Verified exact,
both ways: GS's accepted total is `Total non-interest revenues` +
`Net interest income`, JPM's is `Noninterest revenue` +
`Net interest income`, and AXP's refused total is
`54,865 + 25,598 − 8,234`. One quantity, and the outcome turns on
wording alone — which is the thing the ruling says it is not doing.

**What becomes better for the investor**: two live bands currently rest
on a quantity this platform elsewhere declares is not the top line. Either
they are sound and four more banks are reachable on the same principle,
or they are not and two HIGH/MEDIUM verdicts should be withdrawn.
Recommendations become easier to trust because the platform stops giving
two answers to one question, and an investor comparing JPMorgan with
Apple learns which denominators were used.

**Three outcomes, each with its consequence already measured**:

| outcome | live effect |
|---|---|
| **admit** the quantity consistently | AXP and C become vocabulary candidates under BQ19's arithmetic standard; GS and JPM unchanged; a constructed base for COF and FITB becomes defensible on the same principle — **and §6's comparability question must then be answered before any band is published** |
| **refuse** it consistently | **GS HIGH → UNKNOWN, JPM MEDIUM → UNKNOWN**; aggregate 4·5·3·12 → **3·4·3·14** |
| **distinguish** them on a named ground other than wording | requires naming that ground; none is currently evidenced, and this report found none |

**Why this slice and not a bank factor**: because a bank profitability
architecture cannot be coherent before this is ruled. Every candidate
that gives the six coverage puts a net-of-interest-expense figure in the
`TOTAL_REVENUE` slot, which is the quantity BQ11 refused — so building
it first would resolve the contradiction silently, in favour of one side,
inside a slice about something else.

**It is free, deterministic and touches no production evidence.** Scope:
the ruling, its vocabulary consequence, and the corpus measurement. Not
in scope: the noninterest-income concept, any comparability normalisation,
any band.

---

## Recorded, not solved

- **`evidences_absence` cannot tell a partially-read statement from a
  fully-read one.** MUFG's `net_interest_income` is located, so `is_read`
  passes, so the platform reports *the filer prints no such line* for
  `net_income` about a section that stops 200 rows before it. The guard
  was built against a statement read *not at all*.
- **MUFG prints four subtotals labelled `Total`.** A row label owned by
  the heading above it is unreachable by a concept check that reads the
  label alone. No fix is proposed; the case is one company.
- **DB's bottom line is `Profit (loss)`** and every IFRS filer's will
  be. `CONCEPT_LABELS[NET_INCOME]` carries `profit for the period` and
  `profit for the year` and not the bare form. Free to falsify, and it
  does not band DB by itself.
- **`FinancialModel.BANK` is unreachable twice over** — nothing selects
  it, and the pipeline passes the default anyway. Its question set,
  narrowing and two declines are correct and inert. Recorded rather than
  deleted: it is the specification a Prudential Understanding layer
  would satisfy.
- **`NET_INTEREST_INCOME` is established for nine companies and read by
  no recipe.** That is by design — its consumer is `StatementLanguage` —
  and it is also the one held concept a bank profitability factor would
  reach for first.
- **COF's consolidated total exists and is out of scope.** `TOTAL_REVENUE`
  is scoped to the income statement, which is right; whether a
  management-report figure may ever answer a statement concept is a
  separate boundary question and is not raised here.

## Scope compliance

HON untouched · KO untouched · no vocabulary widened beyond #167 · no
parser behaviour changed · no rule, threshold or band altered · the BANK
model not altered · no calculated financial fact created · no model call
· no new observation · no production write (`git status --porcelain
data/` empty after the #169 merge) · every figure in this document is a
filer's printed row or the platform's own arithmetic over two checked
cells.
