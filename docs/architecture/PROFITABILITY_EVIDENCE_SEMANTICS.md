# Profitability evidence semantics — what the gap sentences actually claim

**Status: research report, BQ3. No implementation. Offline over the
tracked 24-company statement corpus. Stopped for ruling.**

BQ2 found that 22 of 24 companies carry a profitability gap naming a
line unlocated across 5 of 5 observations. BQ3 asks whether MOVRvest is
confusing unacquired evidence, a concept the issuer does not report,
a valid alternative representation, and genuine insufficiency.

**The premise survives falsification, but not in the shape BQ2 left it.**
Two findings reframe it:

> **1. The question contract is innocent.** Profitability already treats
> gross, operating and net margin as *alternatives* — it answers from
> whichever are established and reports the rest as gaps. It demands no
> particular representation. **12 of 24 companies are answered, 10 of
> them while carrying gaps.** There is no representation defect to fix.
>
> **2. The gap sentences are not one population.** For 11 companies the
> named absence is a claim this platform can support. For **13** it
> names a concept whose strong-absence claim **can never be weakened**,
> because the protective vocabulary that exists for other concepts was
> never written for `total_revenue` and `net_income`.

And the load-bearing correction to how all of this is worded:

> **"5 of 5 observations" is five readings of one document by one model
> in forty seconds — not five independent opportunities to observe.**

---

## 1. The semantics, traced

```text
FinancialStatementConsensus        data/statements, schema 3, quorum 5
   │  concept located?  → StatementFact.figure | unlocated_because
   ↓
FinancialUnderstanding.measures    EstablishedMeasure per FinancialMeasure
   │  margin = numerator / denominator, both checked cells
   ↓
QUESTIONS[PROFITABILITY].requires = (GROSS, OPERATING, NET)   ← alternatives
   ↓  answer_questions() → _answer()
QuestionAnswer   state=ANSWERED where ANY required measure is established
   │             gaps = absent_because of the others
   ↓  assess()
QualityFactor.gaps → BusinessQuality → ScoreBasis → dossier / DecisionEvidence
```

**Where each decision is made:**

| Decision | Owner | Rule |
|---|---|---|
| which concepts are acceptable | `CONCEPT_LABELS` (`financial_statements.py`) | **exact equality** after normalisation, never containment |
| which measures are alternatives | `FinancialQuestion.requires` | *"answered from the ones that are established … only where none is established is the question unanswerable"* |
| that a concept is missing | the reading, per observation | `unlocated_because` on the fact |
| what evidence would resolve it | `EstablishedMeasure.absent_because` | *"needs `X`, which is not established"* |
| whether absence is structural | **`StatementShape.evidences_absence`** | statement read **and** no near label left unread |

**The last row is the only place in the platform that distinguishes
"the filer prints no such line" from "this platform could not read it"**
— and it lives in `movrvest statement-shape`, not in the quality path.

## 2. The 24 companies measured

`G`/`O`/`N` = gross/operating/net margin established.

| Symbol | Established | Gaps blame | Profitability | Unprotected blame |
|---|---|---|---|---|
| AAPL | G O N | — | answered *excellent* | — |
| TSLA | G O N | — | answered *weak* | — |
| PG | O N | gross_profit | answered *strong* | — |
| WMT | O | gross_profit, **net_income** | answered *weak* | net_income |
| ALL, CB, DIS, GS, HON, JPM, MET, TRV | N | gross_profit, operating_income | answered | — |
| AXP, COF, FITB, MTB, NWG, RF | — | gross_profit, operating_income, **total_revenue** | **unanswerable** | total_revenue |
| BCS, C, DB, MUFG | — | gross_profit, operating_income, **net_income** | **unanswerable** | net_income |
| KO | — | **total_revenue** ×2, **net_income** | **unanswerable** | both |
| UNP | — | gross_profit, **total_revenue** ×2 | **unanswerable** | total_revenue |

Blame totals: `gross_profit` 21, `operating_income` 18, **`total_revenue` 10**, **`net_income` 6**.

**Profitability is answered for exactly 12 and unanswerable for exactly
12.** Every unanswerable company is blocked by a **denominator or a
last-resort numerator**, never by the absence of a *preferred*
representation.

## 3. Classification

**The discriminator is `CONCEPT_WORDS`** (`statement_shape.py`), the
table that downgrades *"the filer prints no such line"* to *"this
platform did not read it"*. It has **four entries**:

```python
GROSS_PROFIT: ("gross",)
OPERATING_INCOME: ("operating income", "operating profit", … 7 forms)
TOTAL_CURRENT_ASSETS / TOTAL_CURRENT_LIABILITIES
```

**`TOTAL_REVENUE` and `NET_INCOME` are absent from it.** For those two
concepts the downgrade can never fire, so any label the matcher misses
falls straight to `NOT_PRINTED`, and where the statement was read at all
`evidences_absence` returns `True` — **the platform asserts the filer
prints no such line, and is structurally unable to say otherwise.**

| Class | Companies | Evidence |
|---|---|---|
| **A — acquisition/extraction gap** | **C** | `statement-shape`: Citigroup's income statement **prints `'Net income'`**, a label `matches_concept` accepts. The model-based reading failed to locate it in 5 of 5. The document and the platform's own vocabulary agree; only the extraction failed. |
| **A — vocabulary too narrow** | **KO, UNP, AXP** (+ likely COF, FITB, MTB, NWG, RF) | `CONCEPT_LABELS[TOTAL_REVENUE]` holds 12 exact forms and **not** *"Net Operating Revenues"* (KO), *"Operating revenues"* (UNP) or *"Total revenues net of interest expense"* (AXP). Verified: `matches_concept(TOTAL_REVENUE, "Net Operating Revenues")` is `False`. KO's gross profit was located **at table 0, row 3** of the very table whose row 1 carries the revenue line — the table was read. |
| **B — representation mismatch** | **none** | The contract demands no representation: it answers from whatever exists. B is refuted by construction. |
| **C — semantically insufficient substitution** | **10** (the answered-with-gaps set) | The analytical outcome is correct — profitability *is* answered. Only the wording is at issue (§6). No substitution is needed or offered. |
| **D — genuinely absent** | **JPM, GS, TRV, CB, MET, ALL, DIS, HON** for `gross_profit`/`operating_income` | Here the strong claim **is** supported: the statement was read, the `'gross'` and operating-income downgrade words exist and did **not** fire, so no near label was left unread. Banks and insurers genuinely print neither line. |
| **E — unknown** | **BCS, DB, MUFG** | `net_income` unlocated and `statement-shape` reports no such line, but `CONCEPT_WORDS` has no entry to weaken it — so *"IFRS filer using a label outside our 6 accepted forms"* and *"genuinely absent"* are **indistinguishable from this corpus**. MUFG additionally rests its whole language claim on one located line. |

## 4. Falsification of the substitution rule

**The tempting rule — "if net margin is absent, use operating margin" —
is already refused by the architecture, and correctly.**

`ProfitabilityAnalyst._metric_score` grades each margin on **its own
scale**: gross 60/40/20, operating 30/20/10, net 20/10/5. The three are
not interchangeable numbers and the platform already knows it. A
substitution rule would have to claim they answer the same economic
question, and the corpus refuses that:

- **Cross-archetype incomparability.** GS's *excellent* rests on net
  margin 29.5%; AAPL's on gross 46.9% + operating 32.0% + net 26.9%.
  A bank's net margin is struck on *net revenue* (after interest
  expense) — the denominator is not a comparable base to an
  industrial's sales. MET's 4.4% and TRV's 12.9% are insurer net
  margins on premium-dominated revenue, a third base again.
- **Divergence where both exist.** AAPL 32.0% vs 26.9%, PG 22.7% vs
  18.5%, TSLA 4.6% vs 4.1% — ratios 1.19, 1.23, 1.12. Different
  quantities, different scales, not proxies for one another.
- **WMT is the standing counterexample.** Operating margin 4.2%
  established, net margin absent. Substituting operating for net would
  score 4.2% against the *net* scale (0.05 → 70) instead of the
  *operating* scale (0.00 → 40) — inventing a better verdict out of a
  scale mismatch.

**Verdict parity with unequal support is a real, separate finding.**
JPM's *excellent* rests on one measure; AAPL's on three. Both print the
same word. The mechanism that would express the difference —
`QuestionAnswer.confidence`, 0.333 vs 1.0 — is **dropped by `assess()`**
and reaches no surface (BQ2 §5).

## 5. What "5 of 5" means

Measured from the stored provenance:

| Symbol | Observations | Distinct documents | Reader | Wall-clock span |
|---|---|---|---|---|
| KO | 5 | **1** (10-K 0001628280-26-010047) | gpt-5 | 06:55:03 → 06:55:42, **39 s** |
| C | 5 | **1** (10-K 0000831001-26-000011) | gpt-5 | 06:52:26 → 06:53:16, **50 s** |
| JPM | **10** | **1** (10-K 0001628280-26-008131) | gpt-5 | two batches, 06:48 and 07:04 |

**Five readings of one document, by one model, one prompt, within a
minute, on one day (2026-08-09).** Not five filings, not five periods,
not five sources, not five models.

So repeated absence is evidence of **consistent reader behaviour on one
document**, not of structural non-reporting. The clause *"(5 of 5
observations.)"* appears in an investor-facing sentence where it reads
as corroboration; it is **repetition**. This is the intelligence
journal's own rule (#111) — *three captures across three weeks are not
three weeks of monitoring* — arriving in the statement domain.

## 6. Investor-language audit

What the four honest statements would be, and what MOVRvest actually
says:

| Meaning | Should read | What is rendered today |
|---|---|---|
| we haven't acquired this | *"the reading located no cell…"* | **quality gap sentence** — honest at fact level |
| the company doesn't report this | *"the statement prints no such line"* | **`statement-shape`** — supported for gross/operating on banks; **unsupported for `total_revenue`/`net_income` anywhere** |
| not applicable here | `NOT_APPLICABLE_FOR_PLAYBOOK` | reserved for model declines; never used for profitability |
| we cannot assess profitability | `NOT_ANSWERABLE_FROM_ESTABLISHED_FACTS` | correct for the 12 |

**The defect is precisely located and it is narrow.** The quality-layer
sentence — *"Gross margin needs gross_profit, which is not established:
The reading located no cell holding…"* — is **honest**: it says the
reading located no cell, which is exactly true. What it adds is *"(5 of
5 observations.)"*, which overstates the independence of the evidence
(§5), and it is phrased as an **acquisition demand** for concepts that
for banks and insurers will never be satisfiable.

The **unsupported claim** lives one surface over: `statement-shape`
tells an investor *"the statement prints no such line"* about Coca-Cola's
revenue and Citigroup's net income. Coca-Cola prints *"Net Operating
Revenues"*; Citigroup prints *"Net income"* — the platform's own matcher
accepts the latter. **That is MOVRvest manufacturing a missing-evidence
claim by demanding a representation it has no right to demand** — Zero
Fake Gaps, exactly as the brief frames it.

## 7. Counterfactual

**None computed, and deliberately.** No substitution is independently
authorised (§4), so there is no semantically valid alternative
representation whose effect could honestly be modelled. Manufacturing
one to show a coverage gain is the thing this slice exists to refuse.

What *is* measurable without any rule change: **fixing the
`total_revenue` vocabulary alone would unblock the denominator for 8 of
the 12 unanswerable companies** — but whether their margins would then
establish depends on re-reading, which is funded work and outside this
slice. **No counterfactual band, score or coverage figure is claimed.**

## 8. Verdict

# D — MIXED

The exact partition of the 24:

| Partition | n | Companies | Failure |
|---|---|---|---|
| No gap | 2 | AAPL, TSLA | — |
| **Answered; gap wording only** | **10** | ALL, CB, DIS, GS, HON, JPM, MET, PG, TRV, WMT | analytical outcome correct; sentence overstates independence and demands unsatisfiable lines |
| **Unanswerable; extraction failed on an accepted label** | **1** | C | class A — document and vocabulary agree, reading failed 5/5 |
| **Unanswerable; vocabulary too narrow** | **8** | AXP, COF, FITB, KO, MTB, NWG, RF, UNP | class A — real revenue lines outside `CONCEPT_LABELS`, reported as the filer's absence |
| **Unanswerable; cannot distinguish** | **3** | BCS, DB, MUFG | class E — no downgrade vocabulary exists to tell narrow-matching from true absence |

**Both halves are real and they are different defects.** The 10 answered
companies have a *language* problem; the 12 unanswerable have an
*evidence* problem, of which at least 9 are the platform's own
vocabulary or extraction rather than the filer's reporting.

**BQ2's "22 of 24" was true but conflated these.** It is not one
population and not one repair.

## 9. Smallest slices, if the ruling warrants them — not implemented

Two, independent, in this order:

**Slice 1 — close the strong-claim escape hatch (language, no evidence
change).** Add `CONCEPT_WORDS` entries for `TOTAL_REVENUE` and
`NET_INCOME` so the existing downgrade can fire for them, exactly as it
already does for `gross_profit`. Then KO reads *"UNREAD — the statement
prints 'Net Operating Revenues', which this platform does not read as
answering it. This absence is this platform's, not the filer's"* instead
of asserting Coca-Cola prints no revenue. **Adds no concept, no
question, no threshold, no model; changes no arithmetic** — `statement-shape`
stores nothing and reaches no decision. Regression specimens: KO, UNP,
AXP (must downgrade), JPM and TRV (`gross_profit` must **stay**
`NOT_PRINTED` — the bank claim is supported and must not be weakened).

**Slice 2 — word the observation count honestly.** *"(5 of 5
observations.)"* becomes a phrasing that cannot be read as five
independent sources, reusing `ObservationSpan`'s discipline from #111.
Arithmetic-neutral; the decision corpus must be byte-identical.

**Deliberately not proposed**: widening `CONCEPT_LABELS` itself. That
changes what the platform *accepts as evidence* and would alter stored
readings' meaning on re-observation — a funded evidence change, ruled
separately, and it must not ride along with a wording repair.

## Scope compliance

Business Quality unmodified · financial models unmodified · no narrative
restore · no schema migration · no re-observation · **no LLM call, no
credit spent** · extraction unchanged · no provider-industry fallback ·
no threshold changed · no crypto · no UI · PR #145 untouched. Every
figure above is read from `data/statements` or produced by executing
existing code unchanged; all of it is reproducible offline.
