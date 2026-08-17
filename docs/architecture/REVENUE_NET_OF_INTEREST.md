# One formula, three labels: what a revenue net of interest expense is

**Status: research and recommended ruling, BQ22. Read-only over held
evidence plus free deterministic re-reads. No model call, no new
observation, no production write, no vocabulary, rule or threshold
change. Stopped for ruling.**

> **The three statements are one construction, exact three times.**
> `non-interest revenues + net interest income` equals the printed total
> for Goldman (58,283), JPMorgan (182,447) **and American Express
> (72,229)**. American Express prints its own `Net interest income`
> subtotal, so BQ11's description — `54,865 + 25,598 − 8,234` — was the
> *expanded* form of the identical two-term identity, and expanding it is
> exactly what hid the equivalence.
>
> **The contradiction is generational, not an oversight.** The four `net`
> forms in `CONCEPT_LABELS[TOTAL_REVENUE]` were declared in the founding
> commit by *plausible wording*, before any semantic standard existed.
> The standard arrived later, in BQ11 and BQ19, and is written into the
> file: *"an addition of two revenue components with **no expense
> deducted, which is what makes it a gross top line rather than a net
> one**"*. Nobody ruled that Goldman's label was gross. It was on a list
> written before the question was asked.
>
> **`TOTAL_REVENUE` is not broadly mixed — the exceptions are isolated.**
> Of thirteen accepted top lines in the corpus, **eleven are gross before
> financing cost and two are net of it.** Ruling A costs two companies,
> not eleven.
>
> **Recommended: Ruling C.** And it costs **GS its HIGH 80 and JPM its
> MEDIUM 62** — reported plainly, as the brief requires. A band computed
> on a denominator two-thirds the size of a peer's is not a band worth
> preserving.

---

## 1. The three statements, side by side

Every figure is the filer's own printed row, read through `row_figures`
from the document the resolver already names.

| | GS — Consolidated Statements of Earnings | JPM — Consolidated statements of income | AXP — Consolidated Statements of Income |
|---|---|---|---|
| the filer's section heading | `Revenues` | `Revenue` | `Revenues` |
| non-interest component subtotal | `Total non-interest revenues` **44,724** (r8) | `Noninterest revenue` **87,004** (r11) | `Total non-interest revenues` **54,865** (r6) |
| gross interest income | (r9) | `Interest income` 193,341 (r12) | `Total interest income` 25,598 (r11) |
| interest expense | (r10) | `Interest expense` 97,898 (r13) | `Total interest expense` 8,234 (r15) |
| net interest subtotal | `Net interest income` **13,559** (r11) | `Net interest income` **95,443** (r14) | `Net interest income` **17,364** (r16) |
| **the printed total** | **`Total net revenues` 58,283** (r12) | **`Total net revenue` 182,447** (r15) | **`Total revenues net of interest expense` 72,229** (r17) |
| **reconciliation** | 44,724 + 13,559 = **58,283 EXACT** | 87,004 + 95,443 = **182,447 EXACT** | 54,865 + 17,364 = **72,229 EXACT** |
| interest expense deducted? | **yes**, inside `Net interest income` | **yes**, inside `Net interest income` | **yes**, inside `Net interest income` |
| non-interest revenue included? | yes | yes | yes |
| altitude | face of the primary statement | face of the primary statement | face of the primary statement |
| scope | consolidated | consolidated | consolidated |
| bottom line | `Net earnings` 17,176 | `Net income` $ 57,048 | `Net income` $ 10,833 |
| current treatment | **accepted** as `TOTAL_REVENUE` | **accepted** as `TOTAL_REVENUE` | **refused** (BQ11) |

**One formula, three filers, three labels, and the same altitude and
scope.** Nothing but the wording separates them. Every one places the
total immediately below its own net interest subtotal and immediately
below a heading it calls *Revenue(s)*.

Held state, all three quorate at 5 readings, all three unstamped
(pre-BQ17):

```text
GS   total_revenue  "Total net revenues" 58,283  5 of 5    net_interest_income 13,559  5 of 5
JPM  total_revenue  "Total net revenue" 182,447  5 of 5    net_interest_income 95,443  5 of 5
AXP  total_revenue  no figure located            5 of 5    net_interest_income 17,364  5 of 5
```

**AXP's absence is settled, not missing** — `by_majority=True` on *no
figure located*, five of five. The platform positively holds that AXP
prints no acceptable top line, and the figure it declines is the one
Goldman's is.

---

## 2. What `TOTAL_REVENUE` was meant to mean — and the overload, dated

Four sources, and they do not agree.

**a. The concept's own question is silent.**
`CONCEPT_QUESTIONS[TOTAL_REVENUE]` reads *"the company's total revenue for
the most recent period the statement reports"* — no qualifier about gross
or net. It cannot settle the question.

**b. The vocabulary's own comment says gross, explicitly.** BQ19, in
`CONCEPT_LABELS`:

> *"Union Pacific totals `Freight revenues` 23,220 and `Other revenues`
> 1,290 to 24,510 exactly — **an addition of two revenue components with
> no expense deducted, which is what makes it a gross top line rather
> than a net one**."*

**c. BQ11's pinned test says gross, explicitly.**
`test_a_revenue_net_of_an_expense_is_not_the_top_line`:

> *"A different economic quantity from consolidated total revenue, and
> refused for that reason rather than for its wording."*

**d. Every consumer treats it as a margin denominator.** `RECIPES` has
four entries touching it — `GROSS_MARGIN`, `OPERATING_MARGIN`,
`NET_MARGIN` as denominator, `REVENUE_GROWTH` as base — and nothing else
in the platform reads it. It is *only* a denominator.

### The concept is overloaded, and the overload has a date

| generation | commit | forms | standard applied |
|---|---|---|---|
| **1** | `f45c912`, 8 Aug 2026 — the founding FSA slice | 12, including `net revenue`, `net revenues`, **`total net revenue`, `total net revenues`** | **none.** The docstring's only stated concern is *equality, never containment* — a rule about matching, not about meaning |
| **2** | `6c96ea0` (BQ11), `c49955b` (BQ19) | 2 — `net operating revenues`, `total operating revenues` | **the filer's own arithmetic**: no expense deducted |

The founding twelve were a list of plausible spellings. Four of them
carry `net`, and one of those four is the label the whole contradiction
rests on. **Generation 2's standard was never applied backwards to
generation 1.** So this slice does not overturn a decision — no decision
was ever made. It applies the platform's own written standard to forms
that predate it.

*(A note on the other `net`. `CONCEPT_WORDS[TOTAL_REVENUE]` in
`statement_shape.py` carries `net sales` too, but it is deliberately
one-directional and can only ever weaken an absence. It decides nothing
and is not part of the overload.)*

---

## 3. Every accepted top line in the corpus, classified

Classified by structure rather than by wording: **where does the filer
typeset its financing cost relative to the accepted total?**

| | company | accepted label | figure | interest expense row | net interest row | total row | class |
|---|---|---|---|---|---|---|---|
| 1 | AAPL | `Total net sales` | 416,161 | none | none | 5 | **A** |
| 2 | ALL | `Total revenues` | 67,685 | 17 — **below** | none | 8 | **A** |
| 3 | CB | `Total revenues` | 59,402 | 15 — **below** | none | 9 | **A** |
| 4 | DIS | `Total revenues` | 94,425 | none | none | 4 | **A** |
| 5 | HON | `Net sales` | 37,442 | none | none | 5 | **A** |
| 6 | MET | `Total revenues` | 77,084 | none | none | 8 | **A** |
| 7 | PG | `NET SALES` | $ 87,032 | 6 — **below** | none | 1 | **A** |
| 8 | TRV | `Total revenues` | 48,828 | 12 — **below** | none | 7 | **A** |
| 9 | TSLA | `Total revenues` | 94,827 | 25 — **below** | none | 9 | **A** |
| 10 | UNP | `Total operating revenues` | 24,510 | 15 — **below** | none | 4 | **A** |
| 11 | WMT | `Total revenues` | 713,163 | none | none | 3 | **A** |
| 12 | **GS** | `Total net revenues` | 58,283 | 10 — **above** | **11 — above** | 12 | **B** |
| 13 | **JPM** | `Total net revenue` | 182,447 | 13 — **above** | **14 — above** | 15 | **B** |

| class | meaning | count |
|---|---|---|
| **A** | gross sales/revenue before financing expense | **11** |
| **B** | net revenue after interest expense | **2** |
| **C** | another accounting construct | **0** |
| **D** | ambiguous or unsafe | **0** |

**The `net` in the class-A labels is a different `net`.** `Total net
sales`, `Net sales` and `NET SALES` are net of returns, discounts and
allowances — revenue *adjustments*, not an expense line on the statement
— and the structure proves it: no financing cost is typeset above any of
them. `Net Operating Revenues` (KO, currently unsettled) is the same, and
BQ11 established it by arithmetic: 47,941 − 18,397 = 29,544, exactly the
printed `Gross Profit`.

**GS and JPM are isolated exceptions.** `TOTAL_REVENUE` does *not*
already mix economic meanings broadly — 11 of 13 occurrences are one
meaning. That is the fact that makes a coherent ruling affordable.

### The discriminator, and it is not a word

> A located `TOTAL_REVENUE` whose row sits **below** a located
> `NET_INTEREST_INCOME` on the same statement is net of financing cost.

Swept over the whole corpus from established facts alone:

- **fires for 2 of 13** — GS (`Net interest income` t0 r11 precedes
  `Total net revenues` t0 r12) and JPM (t0 r14 precedes t0 r15);
- **clears all 11 class-A totals**, and every one for the same structural
  reason: *no net interest income on this statement*;
- **zero false positives.**

`NET_INTEREST_INCOME` accepts exactly one label — `net interest income` —
the tightest vocabulary in the concept table, and no insurer and no
industrial in the corpus establishes it (measured: 0 of 13).

**And it generalises correctly to the next candidates.** Barclays prints
`Net interest income` at r4 and `Total income` at r12; NatWest at r5 and
r11. Both would fire. BQ19 refused `total income` for a parent-company
collision at M&T; the discriminator refuses it a second time on an
independent semantic ground. **Four of four financial-institution top
lines identified, eleven of eleven others cleared — fifteen cases, no
error.**

---

## 4. The three rulings

### Ruling A — strict gross top line

`TOTAL_REVENUE` excludes measures net of financing cost.

| | |
|---|---|
| semantic coherence | **high** — it is the platform's own written standard (BQ19's comment, BQ11's test), applied consistently |
| compatibility with existing concepts | **full** — no new concept, no schema change, no vocabulary edit |
| downstream comparability | **restored** — every surviving `TOTAL_REVENUE` is class A |
| GS / JPM | top line refused → **both UNKNOWN** |
| AXP | stays refused, and now for a reason that holds |
| COF / FITB | unaffected — they print no total at all |
| migration / provenance | BQ20-shaped: derived on read, nothing written |
| false positives outside financials | **zero measured** (11 of 11 cleared) |
| **its cost** | it discards a **real, quorate, checked figure**. Goldman's 58,283 is a genuine consolidated measure; only its *slot* is wrong. A is right about the slot and silent about the figure |

### Ruling B — filer-defined consolidated top line

A printed consolidated top line maps to `TOTAL_REVENUE` whatever the
filer deducts.

| | |
|---|---|
| semantic coherence | **low** — `TOTAL_REVENUE` becomes *whatever the filer calls its top line*, so a margin denominator varies in economic content by presentation. It also requires overturning BQ11 **and** contradicting BQ19's own written standard |
| compatibility | full for GS/JPM; AXP needs a vocabulary widening **and** re-observation |
| downstream comparability | **destroyed, measurably.** This is the architecture BQ21 refused: on one threshold table the construct puts **6 of 7 banks in the top bucket** where 0 of 4 insurers and Procter & Gamble are not |
| GS / JPM | keep their bands |
| AXP | **MEDIUM 62** after 5 paid readings — net margin 15.00% *strong*, revenue growth +9.52% moderate, earnings growth +6.95% moderate |
| COF / FITB | **still blocked.** B does not solve the six at all: they print no total, so there is nothing for a filer-defined rule to accept |
| false positives | none new — but it *legitimises* the mixing rather than risking it |
| **its cost** | it preserves two scores and preserves the defect that produced them |

### Ruling C — split the concepts

Measures net of interest expense are not `TOTAL_REVENUE`; they belong to
a semantically distinct concept. *(Not implemented in this slice.)*

| | |
|---|---|
| semantic coherence | **highest** — it is the only ruling that says the true thing about both halves: the figure is a real consolidated measure, **and** it is not total revenue |
| compatibility | needs one new `StatementConcept` later. **Until it exists the figure is unacquired, so C's corpus effect today is identical to A's** |
| downstream comparability | restored — and it creates the honest home for a future bank profitability factor that does not pretend equivalence |
| GS / JPM | **both UNKNOWN today**, with the figure named as belonging elsewhere rather than as absent |
| AXP | refused as `TOTAL_REVENUE`, and named as the same concept as GS's and JPM's — which is the fact §1 establishes |
| COF / FITB | unaffected today; the new concept is where their constructed base would eventually live, if a ruling ever earns one |
| migration / provenance | identical to A today; the new concept later requires re-reading GS, JPM and AXP to establish it |
| false positives | same zero |

**C dominates A**: identical cost today, strictly more truth, and it does
not permanently discard a figure three filers print. **C dominates B** on
coherence and on the measured comparability defect.

---

## 5. Downstream simulation — for visibility, not as evidence

| | HIGH | MEDIUM | LOW | UNKNOWN |
|---|---|---|---|---|
| today (Ruling B, the status quo) | 4 | 5 | 3 | 12 |
| **Rulings A and C** | **3** | **4** | 3 | **14** |

**GS `HIGH 80` → `UNKNOWN`. JPM `MEDIUM 62` → `UNKNOWN`.** Stated
plainly, and it is not an argument against the ruling.

Both currently answer all three factors. Under the ruling each keeps
`earnings_growth` alone — GS *strong* (+20.3%), JPM *declining* (−2.4%) —
and one answered factor never bands, by `MINIMUM_ANSWERED`. Two
companies lose a verdict; nothing about either business changed.

Ruling B extended to AXP would add **MEDIUM 62** after five paid
readings. That is the whole of B's upside, and it buys one band by
widening the inconsistency to a third company.

---

## 6. Extraction and profitability are two questions

They must be answered separately, and the answers differ.

**Question 1 — what financial concept does `Total net revenue(s)`
represent?** A real one. It is `non-interest revenues + net interest
income`: the standard top-line presentation for a financial institution,
printed on the face of the audited statement, consolidated, and
reconciling exactly to two of the filer's own subtotals. **It is
legitimate, and it is not total revenue.** The figure deserves a concept;
it does not deserve this one.

**Question 2 — should that concept be the denominator of the generic
profitability factor?** **No.** BQ21 measured it: on the platform's own
net-margin table, the construct reads *excellent* for six of seven banks
while zero of four insurers and Procter & Gamble do — because the
denominator already excludes a bank's largest cost. Capital One's
constructed base is 23% smaller than its gross income before any
judgement is made.

So the honest position is the one the brief anticipated: **the extraction
concept is legitimate and the generic comparison is not.** Ruling C is
the only one of the three that can hold both at once — A discards the
figure to protect the comparison, B keeps the figure and breaks the
comparison, and C keeps the figure *out of* the comparison.

**Neither answer is forced on the other.** This slice rules on question 1
only. Question 2 is already answered in the negative by BQ21 and needs no
further ruling; what it does *not* have is a place for the figure to go,
and that is a later slice.

---

## 7. Provenance and migration

**Which observations were produced under contracts that accepted the old
mapping?** GS's five income readings and JPMorgan's five, all unstamped
(`produced_under` empty — pre-BQ17, like every observation in the corpus
except UNP's newest five). Under BQ20's entailment their candidate
contracts are the era's non-stamping vocabularies, `{ba55a427,
3cdbddd6}`, and **both accept `total net revenue(s)`** — it is a founding
form. So those readings were **validly produced**. Nothing about them was
wrong at the time.

**Are they historically valid but analytically supersedable?** Yes, and
this is exactly BQ17/BQ20's architecture working as designed. The reading
recorded what its contract accepted; the guard decides only whether that
recording may settle today's claim. Nothing is rewritten, no
`produced_under` is altered, no observation is deleted, and
`movrvest statements GS` continues to hold five readings of a real cell.

**One genuinely new direction, and it must be named.** BQ20 withdraws
**absences**; this withdraws a **positive**. That is not BQ20's exclusion
#1 (*"two positives that disagree remain a disagreement"* — there is no
disagreement here); it is a positive refused on structural grounds, and
it therefore belongs in its own module rather than folded into
`absence_supersession`. The refusal must also be **reported rather than
silent**: a `TOTAL_REVENUE` refused for structure must never render as
*the filer printed no such line*, which would be a false claim about
Goldman.

**Would correction require re-reading?** Two different answers:

- **for the guard, no.** Both concepts are already established for GS and
  JPM with checked cells and positions. The refusal is derivable from
  held evidence alone.
- **for the new concept, yes.** A new `StatementConcept` is a new
  question a reading must be *asked*, so establishing it would need a
  funded re-observation of GS, JPM and AXP — and for AXP its label as
  well. **No re-read was performed and none is recommended in this
  slice.**

**No `CONCEPT_LABELS` edit is recommended**, so
`vocabulary_contracts.PUBLISHED` needs no extension and no fingerprint
moves. That is deliberate: a lexical deletion of the four `net` forms
would wrongly refuse an industrial that prints `Net revenues` meaning net
of returns, which is class A. **The wording was never the problem, so the
wording is not the fix.**

---

## 8. The recommended semantic invariant — one

> ### `TOTAL_REVENUE` is gross revenue before financing cost.
>
> A row may not answer `TOTAL_REVENUE` where the same statement prints a
> **net interest income** subtotal above it. Such a row is a measure net
> of financing cost — a different economic quantity — and belongs to a
> different concept.
>
> **The refusal is structural, decided by the filer's own typesetting of
> two concepts this platform already reads, and never by the row's
> wording.** A label carrying the word *net* is not refused; a row
> printed beneath a financing cost is.

It is stated to be testable in exactly the form a permanent test needs:
two established facts, two cell positions, one comparison. It fires for
GS and JPM, clears eleven class-A totals, and would fire for Barclays'
and NatWest's `Total income` — fifteen corpus cases, no error.

**Ruling C.** The invariant above is the half that can be built now; the
concept the refused figure belongs to is the half that waits.

---

## 9. The smallest implementation slice — one

> **Refuse a net-of-financing top line at the consensus, derived on read,
> and pin the invariant against the live corpus.**

**What becomes better for the investor**: the platform stops publishing
two answers to one question. Today Goldman's `Total net revenues` is a
total revenue and American Express's identical figure is not, and a
profitability verdict rests on the difference. After the slice, a net
margin means one thing across the corpus, and where the platform cannot
say it, it says so.

**Scope**:

1. A domain module — the sibling of `absence_supersession`, not part of
   it — holding one function: given one statement's consensus facts,
   return the structural refusal where `NET_INTEREST_INCOME` is located
   at a cell preceding a located `TOTAL_REVENUE`.
2. `statement_consensus_of` applies it. The `TOTAL_REVENUE` fact becomes
   unlocated **with the structural reason**, carried in a field distinct
   from `unlocated_because` so a refusal can never read as *the filer
   printed no such line*. Same shape as `withdrawn_absences`: reported
   beside the agreement, never subtracted in silence.
3. The invariant test: fires for GS and JPM; clears all eleven class-A
   totals; a control asserting that a `net`-worded class-A label is
   **not** refused, so the rule cannot decay into a word blacklist; and a
   control asserting the observations are byte-identical afterwards.

**Expected effect, stated before it is built**: GS `HIGH 80` → `UNKNOWN`,
JPM `MEDIUM 62` → `UNKNOWN`, aggregate **4·5·3·12 → 3·4·3·14**. No other
company moves.

**Not in scope**: the new concept, any vocabulary edit, any re-reading,
any bank profitability factor, and any change to a threshold, a band or a
stored observation.

---

## 10. Gates and production mutation

| | |
|---|---|
| `pytest` | **2,805 pass** |
| `ruff check` | clean |
| `ruff format` | clean |
| `mypy app` | clean, 593 files |
| `git status --porcelain data/` | **empty** |

**Zero production mutation.** This slice writes one document. Every
figure in it is a filer's printed row, read from the documents the
resolver already names, or arithmetic over two such rows. No model was
called, no observation was taken, and no stored evidence was read for
anything but reporting.

## Scope compliance

BANK routing not activated · no bank quality factor · COF/FITB not fixed ·
DB/MUFG not fixed · HON untouched · KO not re-read · **no revenue
vocabulary widened or narrowed** · no production observation changed · no
model or API call · no re-observation of GS, JPM or AXP.

## Recorded, not solved

- **The concept the refused figure belongs to is unnamed.** Naming it is
  the next slice, and it is what turns GS's and JPM's UNKNOWN from a loss
  into a relocation. It also needs a funded re-observation to establish,
  which is why it is not bundled here.
- **`net revenue` and `net revenues` remain in the vocabulary and occur
  nowhere.** They are the two founding forms with no live occurrence; the
  structural guard makes them harmless, and deleting them lexically would
  be the word-blacklist mistake. Left alone deliberately.
- **NatWest prints `Profit for the year`, an accepted `NET_INCOME`
  form, and `Total income` above it.** Out of scope, and noted because it
  means NWG's position under the guard is settled in advance.
- **The guard reasons across two concepts of one statement**, which no
  existing derivation does — every current one is per-concept. It is safe
  here because `statement_consensus_of` already builds one statement's
  facts together, but it is a new kind of derivation and should be named
  as such rather than arriving as a helper.
