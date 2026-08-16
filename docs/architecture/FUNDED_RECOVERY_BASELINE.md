# The funded baseline: today's pipeline recovers, and the corpus is stale

**Status: experiment, BQ8. Five model readings spent. Production corpus
untouched — every observation written to an isolated store. No
vocabulary change, no code change, 0 Business Quality changes.
Stopped for ruling.**

BQ7 proved the historical cells are in the filings and predicted, from
deterministic parsing alone, what a fresh reading should capture. This
spends the authorised credits to test whether today's unchanged
pipeline actually captures them.

**It does.**

> **TSLA and ALL: fresh readings store the anchor under `2025` and
> carry three dated cells — exactly the values BQ7 predicted
> deterministically, to the digit.** The old corpus is stale; the
> pipeline is not broken.
>
> **KO: the negative control behaved exactly as predicted.** `Net
> Operating Revenues` still establishes nothing, while KO's *accepted*
> label `Gross Profit` captured three dated cells. Vocabulary is
> isolated as the cause, and the historical path is proven to work for
> KO the moment a label is accepted.
>
> **HON: a new defect, precisely located** — and not the one BQ7
> predicted.

---

## 1. Actual model usage

**Five readings**, all `gpt-5`, all against already-cached documents.

| Specimen | Readings | Outcome |
|---|---|---|
| TSLA | 1 | stored |
| ALL | 1 | stored |
| KO | 1 | stored |
| HON | 2 | refused both times (second run taken only to capture the reason) |

One earlier CLI invocation (`observe-statements TSLA --to 1`) made **no
model call at all** — five observations already existed, so the target
was met and it rendered the stored consensus. No credit was spent
there.

**Every observation was written to an isolated store** (`/tmp/bq8`),
not to `data/statements`. The production corpus's four specimen files
are byte-identical and still dated 9 August, and Business Quality is
unchanged for all 24 companies. This required an explicit harness: the
statement store **does not honour `MOVRVEST_EVIDENCE_ROOT`** — see §9.

## 2. TSLA — positive control, recovered

| | Before (stored, 9 Aug) | After (fresh reading) |
|---|---|---|
| anchor column header | `Year Ended December 31,` | **`2025`** |
| row cells | **1** | **3** |
| revenue | 94,827 | **94,827 · 97,690 · 96,773** under `2025 · 2024 · 2023` |
| net income | 3,855 | **3,855 · 7,153 · 14,974** |

Identical to BQ7's deterministic prediction, digit for digit. The
current-period values did not move.

## 3. ALL — positive control, recovered

| | Before | After |
|---|---|---|
| anchor column header | `Years Ended December 31,` | **`2025`** |
| revenue | 67,685 | **67,685 · 64,106 · 57,094** |
| net income | 10,266 | **10,266 · 4,599 · (213)** |

The stored current net income of 10,266 continues to agree with the
filing, as BQ7 verified. `gross_profit` remains absent — an insurer
prints none, and that supported absence is unchanged.

## 4. HON — refused, and the reason is new

Both fresh readings were **rejected whole**: `invalid_extraction`, with
the platform's own words:

> *The figure for 'total_revenue' cites table 0, row 5, column 3, whose
> column carries no header, so there is nothing to say what the number
> measures.*

**This is not BQ7's stale-anchor problem, and it is not a semantic
failure.** The model located the row correctly. The refusal is
structural, and reading HON's parsed table explains it exactly:

```
row0: ['', '', '', 'Years Ended December 31,', '', '']   ← spanned title
row1: ['2025', '', '', '', '', '']                        ← names ONLY column 0
row2: ['', '', '', '(Dollars in millions…)', …]
```

`header_row` skips row 0 as a title (one distinct string, not purely a
number) and settles on row 1 — which is a *pure number*, so the
title-skip correctly does not apply again. But row 1 labels **only
column 0**. The data columns therefore carry no header, `figure_at`
refuses the citation, and the whole reading is discarded.

**The guard behaved correctly at every step and `historical_row` was
never weakened.** HON's document simply typesets its periods in a shape
this platform's header detection cannot read. That is **a new defect**,
distinct from everything BQ5–BQ7 catalogued.

## 5. KO — negative control, exactly as predicted

| Concept | Result |
|---|---|
| `total_revenue` | **absent** — `Net Operating Revenues` still not accepted |
| `net_income` | **absent** — `Consolidated Net Income` still not accepted |
| `gross_profit` | **established**, anchor under `2025`, **3 cells** — 29,544 · 28,737 · 27,234 |

**The control did its job in both directions.** `CONCEPT_LABELS` was
not widened, and KO still establishes nothing for revenue or the bottom
line — confirming vocabulary, not the reader, as the cause. And because
KO's *accepted* label captured three dated cells, the historical path is
proven functional for KO independently of the vocabulary question.

## 6. Semantic recognition versus deterministic expansion

Kept strictly apart, and the model is credited with nothing the parser
supplied:

| Specimen | LLM semantic recognition | Deterministic expansion |
|---|---|---|
| TSLA | located the revenue and net-income rows | **supplied all three periods and their headers** |
| ALL | located both rows | **supplied all three periods** |
| KO | located `Gross Profit`; **failed** on revenue and net income | supplied gross profit's three periods |
| HON | located the revenue row correctly | **never ran** — the anchor was refused first |

**The model contributed exactly one thing in every success: which row.**
Every historical value and every period label came from
`row_figures` reading the filing's own table, with no model claim
involved — which is why BQ7 could predict all of them offline before a
single credit was spent.

Verified independently: `historical_row` accepts all five fresh anchors
(TSLA ×2, ALL ×2, KO ×1) and returns exactly the same cells.

## 7. Business Quality before → after

**Unchanged — 0 differences across all 24 companies.** HIGH 3 ·
MEDIUM 4 · LOW 1 · UNKNOWN 16.

This is correct and expected: the fresh observations live in an
isolated store, and each is a single reading against a quorum of five.
No band could move, and none did. **Business Quality did not change for
any reason at all**, which is the falsification condition inverted.

## 8. Falsification checks — none triggered

| Condition | Result |
|---|---|
| periods inferred from column order | **no** — every period is an explicit four-digit header |
| values attached to the wrong row | **no** — labels match the reading's own anchor |
| HON accommodated by weakening identity | **no** — HON was refused; `historical_row` untouched |
| KO became `TOTAL_REVENUE` via vocabulary change | **no** — `CONCEPT_LABELS` untouched, KO still absent |
| current-period values regressed | **no** — TSLA 94,827, ALL 10,266, KO 29,544 all unchanged |
| duplicate readings shown as independent corroboration | **no** — one reading each, reported as one |
| Business Quality changed for other reasons | **no** — it did not change |

## 9. Classification

# D — MIXED

Three boundaries, three different specimens:

- **TSLA, ALL → A.** The pipeline works now. The old corpus is stale,
  and re-observation is all these need.
- **KO → B.** Semantic recognition blocks. The deterministic evidence
  is recoverable and the reader will not authorise the row, for the
  vocabulary reason BQ3 identified.
- **HON → E.** A previously unidentified defect: a header row that
  labels only the label column, leaving the data columns unheaded and
  the entire reading refused.

## 10. A defect found in passing — the statement store is not hermetic

`JsonFinancialStatementStore.__init__` defaults to the **string literal
`"data/statements"`** rather than `evidence_path("statements")`, so it
**ignores `MOVRVEST_EVIDENCE_ROOT` entirely.** Every other store on the
platform was converted by #118; this one was missed.

Consequences: the test suite's isolation does not cover it — a test
constructing the store with no argument reads the developer's real
corpus — and this experiment could only be isolated by passing an
explicit path. **This is exactly the gitignored-cache trap #118 exists
to prevent, still live in one store.** Not repaired here (out of
scope); recorded as the smallest possible follow-up.

## 11. Next experiment or repair, justified by the evidence

**One slice, and it is not more readings.** The evidence now supports a
narrow, high-confidence repair sequence, in this order:

1. **Re-observe the seven recoverable comparative instances** (TSLA,
   ALL, WMT, MTB, RF — 5 companies × quorum 5 ≈ 25 readings). This is
   the only remaining unknown for them, the mechanism is proven twice,
   and it is the act that moves the four near-bound companies. **This
   is a funded repair, not an experiment** — and it is what a CTO
   ruling should authorise or defer.
2. **HON's header defect** — offline, no credits. A header row that
   names only column 0 while a spanned title above it names the
   period, is a table shape the detector does not handle. Worth
   measuring across the corpus before touching, since it silently
   refuses *whole readings*.
3. **KO's vocabulary slice** — separately attributable, exactly as the
   brief specifies: widen `CONCEPT_LABELS` → re-observe KO → show newly
   established evidence → verify no false positives elsewhere. The
   baseline it needs now exists and is recorded above.

**Citigroup remains untouched** and stays the next funded test after
the historical-period path is settled.

**Recommended immediate next step: the HON header defect (offline,
free)**, because it is the only remaining blocker that costs nothing to
investigate, and because it currently discards entire readings — which
means any broad re-observation would silently lose companies to it.

## Scope compliance

No corpus refresh · `CONCEPT_LABELS` untouched · row identity not
weakened · no historical observation mutated (the production store is
byte-identical, still dated 9 August) · no read-time document fetching
introduced · Business Quality, thresholds, completeness and
financial-model selection untouched · six-company question-contract
problem untouched · Citigroup not included · no crypto, no UI, no
PR #145.
