# Store isolation repaired; the header rule measured and declined

**Status: Part A built. Part B diagnosed, implemented, falsified by the
corpus, and reverted. No LLM call, no credit. Production evidence
byte-identical; 0 analytical changes. Stopped for ruling.**

---

## Part A — the statement store now obeys the evidence root

### 1. The defect and the repair

`JsonFinancialStatementStore.__init__` defaulted to the string literal
`"data/statements"`, so `MOVRVEST_EVIDENCE_ROOT` did not reach it. It
holds the statement corpus every grounded-quality answer rests on, and
it was the store #118 missed.

```python
self.directory = (
    Path(directory) if directory is not None else evidence_path("statements")
)
```

Resolved **at construction, never in the signature** — a default
evaluated at import would freeze the root before a test could redirect
it, which is the bug ruff caught in three stores during #118 itself.
An explicit path still wins, unchanged. Storage, file format and
production behaviour are untouched: with the variable unset the
directory is still `data/statements`.

**Three other repositories carry the same literal and are *not* touched
here** — `company_knowledge_store` (`data/knowledge`),
`investment_decision_store` (`data/decisions`) and
`json_event_repository` (`data/events`). #118 converted the provider
caches and missed every repository; this slice repairs the one in
scope and names the rest.

### 2. Isolation proved — and what it caught

Nine tests: the default resolves through the root; production is what
an unset root still means; the root is read per construction, not at
import; writes land under the isolated root; **an empty root reads
empty** for AAPL, JPM, KO and TSLA; the production corpus is
unreachable; an explicit path overrides and round-trips; and no literal
`"data/statements"` remains in the store's source.

**The repair immediately caught three tests reading production evidence
silently** — `test_score_derivation.py`'s `grounded()` helper built the
service with no arguments and read whatever the developer had acquired.
They now name `data/statements` **explicitly**. The corpus is tracked
in git, so they read the same evidence in CI as locally; what changed
is that the read is declared rather than ambient. That is exactly the
class of failure #118 exists to remove, and it was live.

**Production evidence: byte-identical.** `git status --porcelain data/`
is empty. 2,682 tests pass; ruff and mypy clean.

---

## Part B — HON's header, diagnosed and declined

### 3. The diagnosis (and a correction to BQ8)

BQ8 reported that HON's header row "names only column 0". **That was
wrong.** The measured structure:

```
row0: ['', '', '', 'Years Ended December 31,', '', …]   ← spanned title, correctly skipped
row1: ['2025', '', '', '', '', '', '2024', '', …]        ← header row, CHOSEN
row5: ['Net sales','Net sales','Net sales','37,442','','','34,717',…]
```

| | |
|---|---|
| candidate header rows | row 0 (one distinct string, not a pure number → skipped as a title) · **row 1 (three distinct strings → chosen)** |
| where the periods actually live | row 1, at columns **0, 6, 12** |
| where the figures live | row 5, at columns **3, 9, 15** |
| why the current algorithm fails | `column_header(3)` reads the cell *directly above* the figure, which is `''` |

So the header row is correctly identified and the periods are
present — the header text sits at the **start of its span** and the
figure three cells into it. `figure_at` then refuses the citation, and
the whole reading is discarded. **The refusal was correct at every
step.**

### 4. The candidate rule, and why it was rejected

Implemented and tested: **a column's header is the nearest header text
at or to its left** — the plain meaning of a span. It looks left only,
so a column can never borrow a period beginning after it, and an empty
header row still yields `""`.

Measured across every table of every statement in the 24-company
corpus:

| | count |
|---|---|
| resolutions unchanged | **1,359** |
| blanks filled | **407** |
| **existing headers overwritten** | **0** |

HON resolved correctly (`2025/2024/2023` → 37,442 / 34,717 / 33,009),
and TSLA, ALL and KO were unchanged. The rule is monotone: it can only
fill a blank.

**And the corpus falsified it anyway** — through a test written in BQ7,
before this rule existed:

> With headers at columns 3 and 5 and figures at 3, 4 and 5,
> forward-fill labels the column-4 figure **`2025`** when it is
> **2024**.

A blank header cell is genuinely ambiguous: *inside a span* and *no
header at all* are indistinguishable from the parsed grid. Forward-fill
resolves that ambiguity by assumption, and when it is wrong it does not
refuse — it attaches a **wrong period to a real financial figure**,
which is the Zero Fake Meaning class this platform treats as most
serious. The 407 filled blanks were never individually verified, and
verifying them is not something the corpus can settle.

The invariant governs: *prefer refusal over guessing*, and *a
decorative or spanned title is not a period header merely because it
appears above the data*. **The rule was reverted.** `column_header`,
`row_figures` and `historical_row` are byte-identical to `main`.

### 5. HON before → after

**No change.** HON's readings remain refused, correctly, and no
deterministic rule in this slice earned the right to change that.

### 6. Analytical invariance

Production statement files byte-identical · established current-period
values unchanged · consensus unchanged · Business Quality answers,
scores and bands unchanged — **0 differences across all 24**. HIGH 3 ·
MEDIUM 4 · LOW 1 · UNKNOWN 16.

### 7. What would earn the rule

The failure is that a blank header cell is ambiguous. Two routes could
remove the ambiguity deterministically, neither attempted here:

1. **Preserve colspan at parse time.** If the parser recorded that
   `2025` spanned columns 0–5, a figure at column 3 would be *inside a
   declared span* rather than *after a blank*, and the association
   would be a fact rather than a fill. This is the principled fix and
   it belongs to the table parser, not to `column_header`.
2. **Require a one-to-one shape match** — equal counts of non-empty
   header cells and non-empty figures, paired in order. Deterministic,
   but it pairs by **position**, which the invariant forbids.

Route 1 is the one worth ruling on.

### 8. Next funded experiment recommended

**None yet — and specifically not HON.** The parser cannot currently
read HON's table shape, so re-observing it would spend credits to
reproduce the same correct refusal. The next paid reading should wait
until either route 1 lands or the CTO rules that HON stays refused.

If credits are to be spent next, the highest-value target is unchanged
from BQ8: **the seven recoverable comparative instances** (TSLA, ALL,
WMT, MTB, RF), where the mechanism is proven twice and the only
remaining unknown is whether a full quorum re-read moves the bands.
HON is not in that set precisely because this slice failed to earn it.

## Scope compliance

`CONCEPT_LABELS` untouched · KO vocabulary untouched · no broad
re-observation · Citigroup untouched · Business Quality, completeness,
thresholds and financial models untouched · no immutable observation
changed · no read-time document fetching · six-company question-contract
problem untouched · no crypto, no UI, no PR #145 · **no LLM call and no
credit spent.**
