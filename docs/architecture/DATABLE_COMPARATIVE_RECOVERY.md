# The earlier period is in the document and not in the store

**Status: research report, BQ6. No implementation. Offline over the
tracked corpus and the acquired documents; no model call, no credit
spent. Stopped for ruling.**

BQ5 asked one question and made it the critical path: *for a concept
whose current period is established, does the stored corpus already
carry an earlier cell this platform could date?*

**The answer is no — and the reason matters more than the answer.**

> **Store: nothing.** All nine instances store **exactly one cell**,
> carrying the filer's *group* header (`Year Ended December 31,`) —
> which names no year. No earlier value, no datable period, in any of
> the five readings, for any of the six companies.
>
> **Document: everything.** The same filings, parsed by the platform's
> own deterministic table reader, carry **three numeric cells per row**
> under an explicit **`2025 / 2024 / 2023`** header row.

So the evidence was never absent. It was **not captured by the
reading**, and the reading is what the store holds.

---

## 1. The nine instances

Every company/factor in the `established-but-comparative-undatable`
state, with what the store holds against what the document holds.

| # | Company | Factor | Concept | Stored cells | Stored column header | Document row | Document header row |
|---|---|---|---|---|---|---|---|
| 1 | ALL | revenue_growth | total_revenue | **1** — 67,685 | `Years Ended December 31,` | **3** — 67,685 / 64,106 / 57,094 | `2025 / 2024 / 2023` |
| 2 | ALL | earnings_growth | net_income | **1** — 10,266 | `Years Ended December 31,` | **3** — 10,266 / 4,599 / (213) | `2025 / 2024 / 2023` |
| 3 | HON | revenue_growth | total_revenue | **1** | `Years Ended December 31,` | **3** — 37,442 / 34,717 / 33,009 | `2025 / 2024 / 2023` |
| 4 | HON | earnings_growth | net_income | **1** — 4,772 | `Years Ended December 31,` | **3** — 4,772 / 5,740 / 5,672 | `2025 / 2024 / 2023` |
| 5 | TSLA | revenue_growth | total_revenue | **1** — 94,827 | `Year Ended December 31,` | **3** — 94,827 / 97,690 / 96,773 | `2025 / 2024 / 2023` |
| 6 | TSLA | earnings_growth | net_income | **1** — 3,855 | `Year Ended December 31,` | **3** — 3,855 / 7,153 / 14,974 | `2025 / 2024 / 2023` |
| 7 | WMT | revenue_growth | total_revenue | **1** — 713,163 | `Fiscal Years Ended January 31,` | **3** — 713,163 / 680,985 / 648,125 | `2026 / 2025 / 2024` |
| 8 | MTB | earnings_growth | net_income | **1** — 2,851 | `Year Ended December 31,` | **3** — 2,851 / 2,588 / 2,741 | `2025 / 2024 / 2023` |
| 9 | RF | earnings_growth | net_income | **1** — 2,156 | `Year Ended December 31` | **3** — 2,156 / 1,893 / 2,074 | `2025 / 2024 / 2023` |

**Every stored current-period value matches the document's own most
recent column** — checked cell by cell for all nine. The reading is
accurate about what it captured; it simply captured one column of
three.

**All observations agree.** Five readings each (ten for WMT and RF, of
which the second batch addressed these concepts not at all), and every
one stores the same single cell with the same undated group header.
This is not reader variance; it is uniform reader behaviour.

**Exact reason the comparison is refused today**: `GrowthAnalyst`
receives one dated figure and nothing to compare it against, so it
reports *"the row prints no earlier period this platform can date from
the filer's own column headers"*. That sentence is true of the
**stored reading** and false of the **document**.

**No date was inferred from row order or observation order** anywhere
in this audit. Every period claim above is the filer's own printed
header text.

## 2. Provenance, layer by layer

```text
source document        3 columns, header row prints 2025 / 2024 / 2023   ✔ HELD
  ↓ statement_tables() deterministic parse, no model                     ✔ HELD
  ↓ THE READING       ← the loss happens here: one cell captured,
                        column_header taken from the group header row
  ↓ StatementFact.row  1 cell, header names no year                      ✘ LOST
  ↓ consensus          agrees, 5 of 5, on the single cell                ✘
  ↓ FinancialUnderstanding                                               ✘
  ↓ growth question    refuses, correctly, on what it was given          ✘
```

**Classification, per the brief's four states:**

| Layer | Class |
|---|---|
| Stored statement corpus (observations → consensus → understanding) | **D — NOT HELD.** The earlier period is absent from every stored reading. |
| Acquired source document + deterministic parse | **A — HELD AND ACCESSIBLE.** Years and values are both present, offline, with no model. |

**All nine instances are D at the boundary Business Quality reads
from.** None is B: no adapter or domain object discards a date the
store holds — the store never held one. None is C: the document's
headers are unambiguous four-digit years.

**No capture timestamp was treated as a reporting period** at any point.
The `observed_at` fields (2026-08-09) are read times and are used
nowhere in this audit.

## 3. Independence of the candidate pairings

Tested against the document evidence, since the store offers no pair:

| Check | Result |
|---|---|
| same economic concept | ✔ same row, same filer label, same table |
| compatible unit / denomination | ✔ same table, one units caption governs the row |
| compatible reporting basis | ✔ one filing, one statement, consecutive annual columns |
| valid period ordering | ✔ explicit four-digit headers; no order inferred from position alone |
| no duplicate value mistaken for a period | ✔ values differ in all nine (e.g. TSLA 94,827 / 97,690 / 96,773) |
| annual vs quarterly | ✔ all annual — `Year(s) Ended December 31` / `Fiscal Years Ended January 31` |
| **column-to-header alignment** | ⚠ **clean for HON, TSLA, RF** (header row is exactly the three years); **requires column-index care for ALL, WMT, MTB**, whose header rows carry three repeated caption cells before the years |

The pairing is chosen by **position in the filer's own header row**, not
by which pairing yields growth. Note the direction is unflattering in
several cases — TSLA revenue and earnings both **decline**, HON
earnings decline — which is evidence the selection is not answer-driven,
and is reported here for exactly that reason.

## 4. Impact — deliberately not computed

The brief permits a counterfactual **only where the existing corpus
already contains independently authorised comparative periods.** The
stored corpus is **D — NOT HELD** for all nine, so **no factor answer,
completeness transition or band is computed or claimed here.**

The document figures are printed in §1 because they are visible facts
about the filing, not because they are established evidence. Turning
them into evidence requires an authority this platform has not granted:
**is a cell read from the deterministic table parse the same evidence as
a cell reported by a funded reading?** That is a boundary question and
the CTO's to rule on, not a calculation.

## 5. Near-bound cohort — the load-bearing measurement

BQ5's seven, re-examined:

| Symbol | Current | Comparative finding | Offline repair could answer? | Band possible? |
|---|---|---|---|---|
| **ALL** | profitability *strong* (1/2) | **D in store, A in document** — both growth factors | yes, if the parse is granted authority | **yes — reaches 2/2** |
| **HON** | profitability *strong* (1/2) | same | yes | **yes** |
| **TSLA** | profitability *weak* (1/2) | same | yes | **yes** |
| **WMT** | profitability *weak* (1/2) | revenue growth D/A; earnings blocked by **vocabulary** | yes, via revenue | **yes** |
| **AXP** | earnings *moderate* (1/2) | **not affected** — blocked by vocabulary | no | no |
| **FITB** | earnings *moderate* (1/2) | **not affected** — vocabulary | no | no |
| **UNP** | earnings *moderate* (1/2) | **not affected** — vocabulary | no | no |

> **Four of the seven near-bound companies — ALL, HON, TSLA, WMT — are
> addressed by comparative recovery, and could each reach 2 of 3
> without any funded re-observation** *if* the parse is granted
> evidential authority. The other three are vocabulary cases and remain
> funded-only.

## 6. The six structurally mismatched companies

Two of the nine instances belong to that cohort, and the brief's
warning applies exactly:

- **RF** — its `Net income` comparative is recoverable from the
  document. It would answer **one** factor. RF needs **two**, and its
  other two are supported absences. **RF stays UNKNOWN**, and its
  recoverable earnings-growth answer is **not** evidence that the
  generic question set fits a regional bank.
- **MTB** — earnings growth recoverable; revenue growth still blocked by
  vocabulary; profitability supported-absent. Reaches **1 of 2**.
  **Stays UNKNOWN.**

COF, NWG, MUFG, BCS and DB are untouched by this investigation. Their
question-contract problem remains a separate future slice, and nothing
here should be read as progress on it.

## 7. Remaining blockers after this investigation

1. **The authority question** — may a deterministically parsed cell
   establish evidence, or must a reading? Blocks all nine instances.
   Offline to decide, offline to build.
2. **Vocabulary population** — 9 factor-instances across AXP, BCS, C,
   DB, FITB, KO, MTB, UNP, WMT. **Funded re-observation only.**
3. **Citigroup's extraction failure** — one instance. **Funded only.**
4. **Six-company question-contract mismatch** — parked.

## 8. Funding gate

# NOT YET

A meaningful offline repair remains on the critical path, and it is now
the *most* valuable one available:

- it reaches **4 of the 7 near-bound companies** (ALL, HON, TSLA, WMT);
- it requires **no acquisition** — the documents are already held;
- it requires **no model call** — `statement_tables()` is deterministic;
- and the evidence it would consume is **already proven present**, in
  this report, for all nine instances.

Funding remains *useful* and is still not *necessary*. It becomes
necessary the moment the authority question in §7.1 is ruled either
way: **if the parse is granted authority**, the nine instances resolve
offline and the remaining blockers (vocabulary, extraction) are
funded-only; **if it is refused**, the nine instances join the funded
queue immediately and every remaining blocker in the corpus requires
re-observation.

**One caution against over-reading this result.** The finding is that
the reading captured less than the document offers. That is a statement
about the reader, and the cheapest honest test of a reader is to run it
— which costs credits. This report shows a deterministic path around
that test for one specific defect; it does not show that the reader is
sound. What it does show is narrower and worth stating exactly: on
these nine instances the reader was **accurate and incomplete** — every
value it captured is the document's own, and it captured one column of
three.

## Scope compliance

No code modified, no comparative logic added, no change to Business
Quality, `CONCEPT_LABELS`, extraction, schemas, financial-model
selection, narrative knowledge, crypto, UI or PR #145. Nothing
re-observed, no model called, no credit spent. Every figure is read
from `data/statements` or from the already-acquired documents via the
platform's own deterministic parser, and is reproducible offline.
