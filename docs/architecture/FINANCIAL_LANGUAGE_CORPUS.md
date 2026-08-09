# Can statement shape select a financial model?

**Status: measured, 2026-08-09. Conclusion B — the signal is real and
insufficient. No rule was earned, and none was implemented.**

`model_for()` derives `FinancialModel` from `PlaybookKind` today. That
coupling is explicit, intentional and not the intended final route. The
intended route is:

```text
FinancialUnderstanding → FinancialModel
```

Before building it, one question had to be answered against evidence
rather than plausibility: **does the shape of a company's primary
statements, on its own, identify a distinct financial language?**

JPMorgan says it might. At 5 of 5 readings its income statement prints
no gross profit line and no operating income line, and its balance sheet
is unclassified. Those are canonical statement facts. They are also one
company, which is why this document exists.

The answer is that statement shape identifies **financial-institution
language** — reliably, across four jurisdictions and two filing forms —
and cannot separate a bank from an insurer. That is not enough to select
`FinancialModel.BANK`, for a reason sharper than the false-positive
count: `BANK` asserts things about deposit funding and regulatory
capital that the shape never evidenced.

---

## What was measured, and with what evidence

Two evidence classes, kept apart because they are not equally strong.

**Structural shape** (`movrvest statement-shape SYMBOL`,
`app/domain/statement_shape.py`). Deterministic: the filer's own row
labels are compared against `CONCEPT_LABELS` by `matches_concept`, the
same rule a reading is held to. No model is asked. This is the stronger
evidence for an *absence*, because a model reading can fail to find a
line that exists and can never invent one that does not.

It reports three findings where the consensus reports one, and the
distinction turned out to matter more than the rule under test:

| Finding | Means | Is it evidence about the company? |
|---|---|---|
| `printed` | a row this platform reads as answering the concept prints a figure | yes |
| `not printed` | no such row, and no label near it left unread | yes — **only** if some other concept on that statement was located |
| `unread` | the statement prints a label a reader would expect to answer it, which this platform does not accept | no — the gap is this platform's |
| `unlocated` | no statement located, or no readable table under the one located | no |

**Reading quorum** (`movrvest observe-statements SYMBOL --statement …`).
The platform's own reading, five times, consensus by content-blind
strict majority. Thirteen companies were taken to quorum in this slice
(JPMorgan was already there). Every quorum taken agreed **5 of 5 on
every concept** — the reader does not wobble on statement tables the way
it wobbles on prose.

The two classes never disagreed where both were available.

### The measurement that nearly went wrong

MUFG's 20-F returns, at 5 of 5 readings, *every one of the eight
concepts absent*. Read as shape, that is a perfect bank: no gross
profit, no operating income, no current assets, no current liabilities.
It is in fact a section this platform could not read at all — its rows
are labelled `Total`, `Total`, `Total`.

**An absence-based rule cannot tell a bank from a filing it failed to
read.** So no absence in this corpus counts as evidence unless the same
statement also *located* something — `StatementShape.evidences_absence`.
Citigroup's balance sheet and Deutsche Bank's income statement are
excluded by the same guard, and both would otherwise have counted as
confirming instances.

---

## The corpus

44 companies swept, 4 jurisdictions, 2 filing forms. `none` = the filer
prints no such line, and this platform can show it read the statement.
*(not read)* = missing, but the guard above refuses it as evidence.
`—` = the statement was never located.

The **Expected language** column is an evaluation label. It exists in
this document and in no production module, which is the point: nothing
in `app/` classifies a company as a bank or an insurer from its
statements.

| Symbol | Expected language | Source and period | Quorum taken | Gross profit | Operating income | Current assets | Current liabilities |
|---|---|---|---|---|---|---|---|
| **AXP** | bank | 10-K 0000004962-26-000080, FY2025 | BS 5/5 | none | none | none | none |
| **BAC** | bank | 10-K 0000070858-26-000157, FY2025 | — | — | — | — | — |
| **BCS** | bank (UK, 20-F) | 20-F 0000312069-26-000004, FY2025 | — | — | — | none | none |
| **C** | bank | 10-K 0000831001-26-000011, FY2025 | BS 5/5 | none | none | *(not read)* | *(not read)* |
| **COF** | bank | 10-K 0000927628-26-000024, FY2025 | — | none | none | none | none |
| **DB** | bank (DE, 20-F) | 20-F 0001159508-26-000017, FY2025 | BS 5/5 | *(not read)* | *(not read)* | none | none |
| **FITB** | bank | 10-K 0000035527-26-000124, FY2025 | — | none | none | none | none |
| **GS** | bank | 10-K 0000886982-26-000091, FY2025 | IS+BS 5/5 | none | none | none | none |
| **HSBC** | bank (UK, 20-F) | 20-F 0001089113-26-000010, FY2025 | — | — | — | — | — |
| **ITUB** | bank (BR, 20-F) | 20-F 0001132597-26-000132, FY2025 | — | — | — | — | — |
| **JPM** | bank | 10-K 0001628280-26-008131, FY2025 | IS+BS 5/5 | none | none | none | none |
| **LYG** | bank (UK, 20-F) | 20-F 0001160106-26-000010, FY2025 | — | — | — | — | — |
| **MTB** | bank | 10-K 0000036270-26-000010, FY2025 | — | none | none | none | none |
| **MUFG** | bank (JP, 20-F) | 20-F 0001628280-26-047095, FY ended 2026-03-31 | IS+BS 5/5 | *(not read)* | *(not read)* | *(not read)* | *(not read)* |
| **NWG** | bank (UK, 20-F) | 20-F 0001104659-26-016245, FY2025 | — | — | — | none | none |
| **PNC** | bank | 10-K 0000713676-26-000020, FY2025 | — | — | — | none | none |
| **RF** | bank | 10-K 0001281761-26-000019, FY2025 | IS+BS 5/5 | none | none | none | none |
| **SAN** | bank (ES, 20-F) | 20-F 0000891478-26-000030, FY2025 | — | — | — | none | none |
| **SCHW** | bank | 10-K 0000316709-26-000009, FY2025 | — | — | — | — | — |
| **TFC** | bank | 10-K 0000092230-26-000030, FY2025 | — | none | none | none | none |
| **USB** | bank | 10-K 0000036104-26-000011, FY2025 | — | — | — | — | — |
| **WFC** | bank | 10-K 0000072971-26-000133, FY2025 | — | — | — | — | — |
| **AIG** | insurer | 10-K 0000005272-26-000023, FY2025 | — | none | none | none | none |
| **ALL** | insurer | 10-K 0000899051-26-000031, FY2025 | IS 5/5 | none | none | none | none |
| **CB** | insurer | 10-K 0000896159-26-000005, FY2025 | — | none | none | none | none |
| **MET** | insurer | 10-K 0001099219-26-000013, FY2025 | IS 5/5 | none | none | none | none |
| **PGR** | insurer | 10-K 0000080661-26-000086, FY2025 | — | — | — | — | — |
| **TRV** | insurer | 10-K 0000086312-26-000065, FY2025 | IS+BS 5/5 | none | none | none | none |
| **BRK-B** | diversified financial | 10-K 0001193125-26-083899, FY2025 | — | — | — | none | none |
| **BLK** | asset manager | 10-K 0001193125-26-071966, FY2025 | — | — | — | — | — |
| **AAPL** | generic | 10-K 0000320193-25-000079, FY2025 | IS+BS 5/5 | **`Gross margin`** | **`Operating income`** | **printed** | **printed** |
| **CAT** | generic | 10-K 0000018230-26-000008, FY2025 | — | — | — | — | — |
| **DE** | generic | 10-K 0001104659-25-122321, FY ended 2025-11-02 | — | — | — | none | none |
| **DIS** | generic | 10-K 0001744489-25-000155, FY2025 | IS 5/5 | none | none | **printed** | **printed** |
| **GE** | generic | 10-K 0000040545-26-000008, FY2025 | — | — | — | — | — |
| **HON** | generic | 10-K 0000773840-26-000013, FY2025 | IS 5/5 | none | none | **printed** | **printed** |
| **JNJ** | generic | 10-K 0000200406-26-000016, FY2025 | — | — | — | — | — |
| **KO** | generic | 10-K 0001628280-26-010047, FY2025 | — | **`Gross Profit`** | **`Operating Income`** | **printed** | **printed** |
| **MSFT** | generic | 10-K 0001193125-26-323660, FY ended 2026-06-30 | — | — | — | — | — |
| **NVDA** | generic | 10-K 0001045810-26-000021, FY ended 2026-01-25 | — | *(not read)* | *(not read)* | **printed** | **printed** |
| **PG** | generic | 10-K 0000080424-26-000103, FY ended 2026-06-30 | — | none | **`OPERATING INCOME`** | **printed** | **printed** |
| **TSLA** | generic | 10-K 0001628280-26-003952, FY2025 | — | **`Gross profit`** | **`Income from operations`** | **printed** | **printed** |
| **UNP** | generic | 10-K 0000100885-26-000037, FY2025 | — | none | **`Operating income`** | **printed** | **printed** |
| **WMT** | generic | 10-K 0000104169-26-000055, FY ended 2026-01-31 | — | none | **`Operating income`** | **printed** | **printed** |

**21 companies are fully evaluable** — both statements located *and*
read, so all three features are evidence: 8 banks (AXP, COF, FITB, GS,
JPM, MTB, RF, TFC), 5 insurers (AIG, ALL, CB, MET, TRV), 8 ordinary
operating companies (AAPL, DIS, HON, KO, PG, TSLA, UNP, WMT).

---

## Every candidate rule, and its errors

Evaluated over the 21 fully evaluable companies. "False positive" means
the rule fires on a company whose expected language is not a bank's.

| Rule | Fires | Banks caught | False positives | False negatives |
|---|---|---|---|---|
| **R1** no gross profit | 18 | 8/8 | **10** — AIG, ALL, CB, MET, TRV *(insurers)*; DIS, HON, PG, UNP, WMT *(operating)* | 0 |
| **R2** R1 ∧ no operating income | 15 | 8/8 | **7** — AIG, ALL, CB, MET, TRV; DIS, HON | 0 |
| **R3** unclassified balance sheet | 13 | 8/8 | **5** — AIG, ALL, CB, MET, TRV | 0 |
| **R4** R2 ∧ R3 *(the JPMorgan triad)* | 13 | 8/8 | **5** — AIG, ALL, CB, MET, TRV | 0 |

Three things fall out of that table.

**The income-statement half of JPMorgan's triad contributes nothing.**
R4 and R3 fire on exactly the same 13 companies. Every company in this
corpus whose balance sheet is unclassified also prints no gross profit
and no operating income; the converse is false. Whatever a future rule
is built from, "no gross profit" and "no operating income" earn no
independent place in it on this evidence.

**Two of the three features are ordinary.** Walt Disney and Honeywell
print neither a gross profit line nor an operating income line, at 5 of
5 readings each. Procter & Gamble, Union Pacific and Walmart print no
gross profit. None of them is a financial institution. A rule resting on
the income statement alone would call five ordinary operating companies
banks.

**No rule in this corpus separates a bank from an insurer.** Travelers,
at 5 of 5 on both statements, is indistinguishable from JPMorgan on
every canonical concept the domain has. So are Allstate, MetLife, AIG
and Chubb.

### Ambiguous and unresolved cases

| Company | Why unresolved | What it would have tested |
|---|---|---|
| **BRK-B** | balance sheet read and **unclassified**; income statement never located | the diversified non-bank most likely to be a false positive — a conglomerate satisfying R3 already |
| **DE** | balance sheet read and **unclassified**; income statement never located | a *manufacturer* satisfying R3, on a captive-finance balance sheet |
| **MUFG**, **C** (BS), **DB** (IS), **NVDA** (IS) | statement located, nothing read | the guard held; they are neither for nor against |
| **PGR**, **BLK**, **SCHW**, **CAT**, **GE**, **JNJ**, **MSFT**, **HSBC**, **ITUB**, **LYG**, **BAC**, **WFC**, **USB** | statements not located | 13 of 44. The demands below diagnose nine of them; CAT, GE, JNJ and BLK were not individually diagnosed |

Berkshire Hathaway and Deere matter most. Both already satisfy the one
feature that carries all the discrimination, and neither is a bank. If
either also prints no gross profit and no operating income — which their
statements very likely do — R4's false-positive set grows beyond
insurers to include a conglomerate and a manufacturer, and the signal
degrades further. **This corpus cannot rule that out, and that is the
single largest reason the answer is B rather than A.**

---

## Why the insurer false positive is fatal, not cosmetic

The tempting reading is that insurers are a small, tolerable error. They
are not, and the reason is in what `FinancialModel.BANK` actually
carries (`app/domain/financial_question.py`):

| What BANK does | Its stated justification | Does statement shape evidence it? |
|---|---|---|
| narrows profitability to net margin | "a bank's income statement prints neither a gross profit line nor an operating income line" | **yes** — this *is* the shape fact, and it holds for insurers too |
| declines **leverage**, needing CET1, Tier 1 capital, the regulatory leverage ratio | "a deposit-taking bank… the liabilities that make it look levered are the deposits it exists to take" | **no** — deposit funding is nowhere in the statement shape |
| declines **cash generation**, needing customer deposits, their share of total liabilities, the LCR | "a bank's operating cash flow is dominated by deposit and lending flows" | **no** |

*(That last row read "needing deposit funding quality, LCR" when this
was measured. The phrase was later found to name a verdict rather than a
fact and was corrected; the finding above is unaffected, since neither
wording is evidenced by statement shape.)*

`BANK` bundles a statement-shape claim with two deposit-funding claims.
Selecting it from shape alone would license the second pair from
evidence that only supports the first — and the platform would then tell
an investor that Travelers' leverage cannot be assessed until its
**Common Equity Tier 1 ratio** is established. Travelers has no CET1
ratio. Its liabilities are claim reserves, not deposits.

That is not an imprecise answer. It is a confident, specific, false
statement about a company, generated by a rule whose evidence never
mentioned deposits — the exact failure invariant 1 exists to prevent.

---

## The liquidity ruling, measured

The ruling was to leave liquidity unresolved and to measure whether
current assets and current liabilities are consistently absent across
bank filings. They are.

- **13 of 13** bank balance sheets that this platform both located and
  read print neither `total current assets` nor `total current
  liabilities`: AXP, BCS, COF, DB, FITB, GS, JPM, MTB, NWG, PNC, RF,
  SAN, TFC — US 10-K, and UK, German and Spanish 20-F.
- No unread label anywhere near either concept. Santander's only
  near-miss is *"Non-current assets held for sale"*, which is not a
  current-asset subtotal.
- Therefore **the current ratio is structurally unavailable for every
  bank in this corpus** — measured, not assumed.

And the ruling stands, because the same absence holds for all five
insurers, for Berkshire Hathaway and for Deere. An unclassified balance
sheet is a property of the balance sheet, not a marker of a bank. It
cannot license a bank-specific liquidity decline.

No third `BANK` decline was added. The existing machinery already does
the honest thing: `CURRENT_RATIO` is reported absent, in the consensus's
own words, for every one of these companies.

---

## Conclusion — B: promising, insufficient

The signal is real. Over 21 fully evaluable companies, R4 separates
financial-institution statements from ordinary operating-company
statements with no errors in either direction: 13 for 13, and 0 of 8
ordinary companies. It holds across two filing forms and four
jurisdictions. It is deterministic and cheap.

It is insufficient to earn the rule this slice was asked about, for
three independent reasons, any one of which would be enough:

1. **It cannot name the language it detects.** Statement shape says
   *not generic*. It does not say *bank*, and the five insurers prove it
   cannot be made to. Naming what it does detect would mean a third
   `FinancialModel`, which this slice was told not to add — correctly,
   since a model invented before a rule table needs it is the
   taxonomy-first move this platform keeps shut out.
2. **`BANK` is more than its shape.** Two of its three behaviours rest
   on deposit funding and regulatory capital, which no canonical
   statement fact establishes. Selecting it from shape would assert
   them anyway.
3. **The two cases that would most test it are unmeasurable.** Berkshire
   Hathaway and Deere already satisfy the discriminating feature and are
   not banks. Until their income statements can be located, the
   false-positive set is a lower bound.

### The exact additional cases needed

Acquisition first — the corpus is limited by what can be located, not by
what exists. Each class below is named with the companies that prove it.

| # | Demand | Proven by |
|---|---|---|
| 1 | **Follow the exhibit that holds the statements.** The primary document carries only cross-references; the audited statements are filed in a separate exhibit. | **WFC** (whole 10-K is 89k characters and contains no statement title), **USB** (every title occurrence is a cross-reference) |
| 2 | **Statement titles outside the vocabulary.** `statement_locator.TITLES` misses three real forms: the word order inverted, the word "Consolidated" absent, and a combined statement of comprehensive income used *as* the income statement. | **DE** — "Statements of Consolidated Income"; **MSFT** — "INCOME STATEMENTS", "BALANCE SHEETS"; **PGR** — "Consolidated Statements of Comprehensive Income" |
| 3 | **A title typeset inside the statement's own table.** The located span begins mid-table, so no `<table>` opens inside it and the statement arrives as flattened prose with zero tables. | **BAC** (income statement and balance sheet both located, 0 tables), **SCHW**, **HSBC** (BS), **ITUB**, **LYG** (BS) |
| 4 | **Row labels the reading vocabulary refuses.** One refusal discards the whole observation, so these cost entire balance sheets and income statements. | equity as *"Total &lt;Company&gt; shareholders' equity"* — **ALL**, **MET**, **CB**, **DIS**, **HON**, **WMT** (JPMorgan's form is currently accepted **by name**); revenue as *"Total revenues, net of interest expense"* — **C**, **AXP**; IFRS net income as *"Profit (loss)"* — **DB** |

Then the cases that would settle the question itself:

5. **Berkshire Hathaway and Deere at quorum on both statements.** They
   decide whether R4's false positives are five insurers or a whole
   family of diversified non-banks. Blocked on demands 2 and 3.
6. **A canonical fact that separates a bank from an insurer.** The
   documents contain one and this platform cannot see it: every bank in
   the corpus partitions its income statement by interest
   (`Total interest income`, `Total interest expense`,
   `Total noninterest income`), while every insurer prints
   `Total revenues` against `Total benefits, losses and expenses`. None
   of those is a `StatementConcept`. Acquiring one is a real option and
   deliberately not taken here: a concept enters when a consumer asks
   for it, and today's consumer would be a rule that has not been
   earned.
7. **A positive-anchor guard on any future rule.** Whatever is
   eventually built must require that the statement was read, not merely
   located. MUFG is the proof, and `evidences_absence` is the guard
   already implemented.

### What was deliberately not done

`PlaybookSelector` unchanged. Every playbook route unchanged.
`model_for()` unchanged. No new `FinancialModel`. No ticker special-cased
— JPMorgan holds no privileged position in anything above. No CET1,
Tier 1, leverage ratio, deposit-funding or LCR acquisition. No third
`BANK` decline. No filing constructor generalised. The `CONCEPT_LABELS`
vocabulary was **not** grown, though demand 4 shows exactly where it
must be: growing it mid-measurement would have changed what the corpus
measured while it was being measured.

The only production change in this slice is a measurement that stores
nothing and decides nothing: `movrvest statement-shape`.
