# Total-revenue vocabulary: one label, earned by arithmetic

**Status: Stage 1 passed offline; Stage 2 spent one funded reading.
One label added. Production evidence untouched. Stopped for ruling.**

BQ11 is the first slice authorised to change what counts as financial
evidence. The change is exactly one filing label, and it was earned by
the filing's own arithmetic rather than by containing the word
*revenues*.

---

## 1. The revenue-like label audit

Every row in the 24-company deterministic statement tables whose label
carries a revenue, sales or income token — **243 rows**, of which 48
are revenue/sales-shaped. Started from the corpus, never from a
synonym list.

**Already accepted (13 rows), and each is genuinely a top line**:
`Total net sales` (AAPL) · `Total revenues` (ALL, CB, DIS, MET, TRV,
TSLA, WMT) · `Total net revenues` (GS) · `Net sales` (HON, WMT) ·
`Total net revenue` (JPM) · `NET SALES` (PG).

**Not accepted, and correctly so** — the adversarial population:

| Label | Company | Why it is not the top line |
|---|---|---|
| `Mortgage banking revenues` | MTB | one product line, 550 against a bank's whole income |
| `Wealth and asset management revenue` · `Commercial payments revenue` · `Consumer banking revenue` | FITB | segment components |
| `Discount revenue` · `Service fees and other revenue` | AXP | components |
| `Total non-interest revenues` | AXP, C, GS | a **subtotal** of one revenue class |
| `Other revenue(s)` | ALL, TRV, C | a residual component |
| `Freight revenues` | UNP | one component |
| `Total automotive revenues` · `Automotive sales` | TSLA | one segment |
| `Product sales` · `Service sales` | HON | components |
| `Total revenues net of interest expense` | AXP, C | **economically different** — a revenue measure struck *after* deducting an expense |

## 2. The KO candidate, decided by arithmetic

`Net Operating Revenues` contains the word *revenues*, which the brief
correctly says is not authority. The authority is the filing's own
statement, three consecutive printed rows:

```
row 1   Net Operating Revenues        47,941
row 2   Cost of goods sold            18,397
row 3   Gross Profit                  29,544
```

**47,941 − 18,397 = 29,544 — exactly the gross profit the filing
prints.** The label is therefore the top line from which Coca-Cola's
gross profit is struck, established by the document's own arithmetic
and not by its wording. No component, segment or subtotal in the
corpus stands in any such relation to the lines beneath it — the test
that separates `Net Operating Revenues` from `Mortgage banking
revenues` is arithmetic, not vocabulary.

## 3. The change

One entry, exact-match only. No `contains("revenue")`, no regex, no
fuzzy matching, no embeddings, no LLM label classification, no
company-specific check:

```python
StatementConcept.TOTAL_REVENUE: (
    …,
    "net operating revenues",   # earned by KO's own arithmetic
)
```

**`CONCEPT_WORDS` was not touched.** The distinction this slice turns
on is now pinned in tests: the broad vocabulary exists only to *weaken
an unsupported absence claim*; the narrow one *establishes a financial
fact*. Sixteen real corpus components are pinned as never-total, and
the revenue-token subset among them is pinned as still weakening — the
property proved in both directions.

## 4. Corpus-wide deterministic counterfactual

Run over every table of every statement of all 24 companies:

> **Rows newly accepted: exactly 1** — `KO`, income statement, table 0,
> row 1, `Net Operating Revenues` = $47,941.

**Zero components, segments or subtotals became `TOTAL_REVENUE`.**
Stage 1's failure condition was not met, so the credits were
authorised.

## 5. Stage 2 — the funded KO reading

**One model reading**, `gpt-5`, against the already-cached 10-K
`0001628280-26-010047`, written to an **isolated evidence root**
(`/tmp/bq11`) — which BQ10 made possible, since the statement store now
honours `MOVRVEST_EVIDENCE_ROOT`. **Production evidence is untouched.**

| Concept | Result |
|---|---|
| `total_revenue` | **47,941**, `Net Operating Revenues`, header `2025`, **3 dated cells** — 47,941 / 47,061 / 45,754 |
| `gross_profit` | 29,544, 3 dated cells |
| `operating_income` | 13,762, 3 dated cells |
| `net_income` | **absent** — `NET_INCOME` deliberately not widened |

The semantic crossing is validated: the reader recognised the row, and
the deterministic expansion supplied every period.

## 6. KO Business Quality, before → after

| | production (5 stale readings) | isolated (1 fresh reading) |
|---|---|---|
| gross margin | absent | **61.63%** |
| operating margin | absent | **28.71%** |
| net margin | absent | absent |
| revenue growth | absent | **+1.87%** |
| earnings growth | absent | absent |
| quorate | 5/5 ✔ | **1/5 ✘** |
| Business Quality | UNKNOWN, 0 answered | **no band — below quorum** |

**Two of the three quality questions become answerable** —
profitability (from gross and operating margin) and revenue growth —
which is exactly the 2-of-3 completeness boundary. **No band is
claimed**: one reading is not a quorum, and `quality_of` correctly
returns nothing. Whether KO banks a band is a question for a funded
quorum re-read, which this slice was not authorised to run.

## 7. Exact API usage

**One reading.** Stage 1 spent nothing.

## 8. Remaining `TOTAL_REVENUE` vocabulary cases

Reported, not implemented:

- **`Total operating revenues`** (UNP, 24,510). Arithmetically earned by
  the same test — `Freight revenues` 23,220 + `Other revenues` 1,290 =
  24,510 exactly — and the strongest next candidate.
- **`Total revenues net of interest expense`** (AXP 72,229, C). A
  filer's true top line, but **economically different**: revenue struck
  after an expense is not consolidated total revenue, and admitting it
  would silently change what the margin denominator means for banks.
  Needs its own ruling, not a vocabulary entry.
- **A pre-existing ambiguity, found in passing and not touched**: WMT
  has **two** accepted rows — `Net sales` 706,413 and `Total revenues`
  713,163. Both match today; the second is the top line. Which one a
  reading anchors is currently undetermined.
- **`NET_INCOME` was not widened**, as instructed, so attribution stays
  clean. KO's bottom line (`Consolidated Net Income`) remains absent
  and is the obvious next candidate for a separate slice.

## 9. Suite status — stated plainly

**2,718 pass.** One failure and one error remain, both in
`tests/test_crypto_dossier_route.py` / `test_crypto_dossier_reaches_the_page.py`.
**They are pre-existing and environmental**, verified by stashing this
slice's changes and re-running: identical failures, 6 failed / 3 passed
both ways, each run ~145 s of network attempts. They are not caused by
BQ11 and are not repaired by it (crypto is out of scope).

## 10. Recommendation for the next slice

**A funded quorum re-read of KO alone** — four more readings to reach
the quorum of five, which would settle whether the first company
unblocked by a vocabulary change actually earns a band. It is the
smallest possible test of the whole chain, it needs no new code, and
it is the natural completion of this slice rather than a new one.

Not recommended yet: widening `NET_INCOME`, UNP's label, or the
comparative cohort refresh. Each is a separate attribution.

## Scope compliance

`CONCEPT_WORDS` untouched · no fuzzy matching, regex, embeddings or
LLM label classification · Business Quality, thresholds, completeness
and financial models untouched · HON not touched, not re-observed ·
Citigroup not touched · TSLA/ALL/WMT/MTB/RF not refreshed · production
evidence not mutated · no crypto, no UI, no PR #145.
