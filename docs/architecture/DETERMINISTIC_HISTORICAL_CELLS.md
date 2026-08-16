# Deterministic historical cells — the boundary, built and unwired

**Status: built. `historical_row`, the authority boundary the CTO
ruling defines. No LLM call, no credit, no analytical change. The
consumption boundary is reported rather than crossed — see §7. Stopped
for review.**

BQ6 measured that seven stored readings hold one cell where the filing
prints three, and that the loss happens before the store. BQ7 builds
the boundary at which those cells may be preserved.

**The first measurement changed what the slice needed to be.**

> The deterministic row expansion **already exists** — `row_figures`,
> called by the extractor since the tabular slice, and documented as
> *"the rest of the row is then read by this platform with no model
> claim anywhere in it"*. It works: Coca-Cola's stored gross profit
> carries three dated cells.
>
> What failed for the nine was **header detection**, repaired on
> 2026-08-09 in `301cfdf` — the same day the readings were taken.
> `header_row` now skips a spanned title (`Year Ended December 31,`)
> and finds the year row beneath it.
>
> **Run today against the *stored* anchors, `row_figures` recovers
> three dated cells for seven of the nine.** The values were never
> missing from the document, and the code that reads them is no longer
> missing either. Only the store predates the fix.

So BQ7 is not a new expander. It is the **identity guard** that makes
re-expansion of an existing anchor safe.

---

## 1. The authority boundary implemented

`historical_row(table, anchor, row)` in `app/domain/tabular_evidence.py`
— between the two authorities, touching neither:

| Authority | Establishes | Where it lives |
|---|---|---|
| **the reading** | that row *R* answers a financial concept | the extractor's model reading, already checked by `figure_at` |
| **the parser** | that the same source row literally prints values under named headers | `statement_tables` / `row_figures`, deterministic |

`historical_row` takes an anchor a reading produced and returns the
dated cells of **that row**. It names no concept, takes no concept and
returns no concept — asserted structurally by a test that greps its own
source for `StatementConcept`, `matches_concept`, `CONCEPT_LABELS`,
`total_revenue` and `net_income`, and finds none.

## 2. Why deterministic cells establish source evidence and not meaning

The claim a parsed cell supports is literal: **this document's row R
prints 97,690 under the header `2024`**. That is a fact about the
document, checkable by anyone holding it, and no model is involved.

What it cannot support is *97,690 is Tesla's total revenue for 2024* —
because the parser has no way to know what the row means. That
knowledge came from a reading, and it attaches to **the row**, not to
the concept vocabulary: the reading said *this row is total revenue*,
and the parser says *this row prints these numbers under these years*.
Composing them is legitimate; letting the parser pick the row is not,
which is precisely what a second classifier would be.

## 3. Provenance shape

Each recovered cell is a `ReportedFigure`, carrying what the boundary
requires: `label` (row identity, the filer's own), `column_header`
(period, the filer's own), `printed` (raw, separators and currency
intact), `value`, `cell` (`table`/`row`/`column`) and `caption`
(statement/table). The source document and unit context travel with the
observation that owns the fact, unchanged.

**Acquisition provenance is not yet distinguished in the type.**
`ReportedFigure` has no field saying *model-read* versus
*deterministically expanded*, and the anchor is currently the only cell
whose acquisition is recorded — by being the anchor. The ruling
requires those to remain distinguishable; **this is the one part of §3
the slice does not deliver**, and it is deliberate: adding the field is
a schema change, and §7 shows nothing can consume the cells yet, so the
field would be stored by nothing and read by nothing. It belongs to the
consumption slice, and is recorded here as its prerequisite.

## 4. The nine instances, before → after

Measured by running today's code against the **stored** anchors and the
**already-acquired** documents. No re-observation, no model.

| # | Company · factor | Stored | Recovered today | Verdict |
|---|---|---|---|---|
| 1 | ALL · revenue | 1 cell, `Years Ended December 31,` | **3** — 2025 67,685 · 2024 64,106 · 2023 57,094 | ✔ |
| 2 | ALL · earnings | 1 cell | **3** — 10,266 · 4,599 · (213) | ✔ |
| 3 | HON · revenue | 1 cell | **0 — abstains** | ✘ row identity |
| 4 | HON · earnings | 1 cell | **0 — abstains** | ✘ row identity |
| 5 | TSLA · revenue | 1 cell | **3** — 94,827 · 97,690 · 96,773 | ✔ |
| 6 | TSLA · earnings | 1 cell | **3** — 3,855 · 7,153 · 14,974 | ✔ |
| 7 | WMT · revenue | 1 cell | **3** — 2026 713,163 · 2025 680,985 · 2024 648,125 | ✔ |
| 8 | MTB · earnings | 1 cell | **3** — 2,851 · 2,588 · 2,741 | ✔ |
| 9 | RF · earnings | 1 cell | **3** — 2,156 · 1,893 · 2,074 | ✔ |

**Seven recover; HON's two abstain**, because its stored row index no
longer names the row the reading read. That is the guard working, not
failing: HON's parse carries a stray `2025` label row, the index has
moved beneath the stored anchor, and attaching a period to the wrong
row is the error the whole slice exists to prevent.

Regression fixtures are the corpus's own values — TSLA
94,827/97,690/96,773 and ALL's stored 10,266 agreeing with its document
— not newly acquired data.

## 5. Refusal cases, all pinned

| Case | Behaviour |
|---|---|
| moved row index (HON's live shape) | `()` |
| tempting similar row the reading never authorised | `()` |
| label matches but the anchor's figure is gone | `()` |
| unheaded column | that cell is dropped; the headed ones survive |
| header row itself | `()` |
| out-of-range row | `()` |
| crossing tables or documents | **unexpressible** — the signature takes one `SourceTable` |
| inferring a period from column order | **unexpressible** — headers are read, never positions |

Twelve tests. The rule they encode: **a missing prior period is
preferable to one attached to the wrong row or period.**

## 6. Analytical isolation — proved

Across all 24 statement companies, compared against the pre-BQ7
baseline: **current-period established values, consensus values,
Business Quality answers, scores and bands — 0 differences.** Bands
remain HIGH 3 · MEDIUM 4 · LOW 1 · UNKNOWN 16. 2,673 tests pass; ruff
and mypy clean.

This is guaranteed by construction as well as by measurement: nothing
calls `historical_row` yet.

## 7. Downstream impact — none, and the next boundary

**No Business Quality answer changes, and none can yet.** The brief's
condition — *report the effect only if existing comparative logic
naturally consumes the newly dated observations* — is not met, and the
reason is the boundary this slice stops at:

> The dated cells exist in the **document**. The consensus, the
> understanding and the growth question all read the **store**. The
> store holds one cell per fact, and the observations that hold it are
> **immutable by design** — correcting one would destroy the
> disagreement the consensus exists to measure.

So consuming the recovery requires one of three things, none of which
is inside this slice:

1. **Re-observation** — the model re-reads, the extractor's existing
   `row_figures` call captures three cells under today's fixed header
   detection, and nothing else is needed. **Costs credits.**
2. **A re-expansion pass** that rebuilds facts from stored anchors plus
   the cached document, and writes them as new observations. **This
   conflicts with immutability**: five re-expanded observations of one
   reading are not five readings, and the consensus would count them as
   such. A schema-level distinction between *reading* and *expansion*
   would be required first — which is also where §3's missing
   acquisition-provenance field belongs.
3. **Read-time expansion**, deriving dated cells when the understanding
   is built. This needs the source document at a boundary that has none
   today, and a page view must never fetch.

**Option 1 is the only one that requires no new architecture.** That is
the finding this slice ends on.

## 8. Remaining blockers

| Blocker | Companies | Class |
|---|---|---|
| comparative recovery, consumption | ALL, TSLA, WMT, MTB, RF (7 instances) | **mechanism proven; needs re-observation** (or new architecture) |
| comparative recovery, row identity | HON (2 instances) | **abstains — would resolve on re-observation**, which re-anchors the row |
| concept vocabulary | AXP, BCS, C, DB, FITB, KO, MTB, UNP, WMT | **funded re-observation only** |
| extraction failure | C | **funded re-observation only** |
| question-contract mismatch | COF, NWG, MUFG, BCS, DB, RF | **parked; more readings would not help** |

**Still solvable offline: nothing material.** The one offline question
BQ5 and BQ6 identified has now been answered, and its answer is that
the mechanism is already correct and the stored evidence is stale.

## 9. Funding ruling

# YES — FUND NOW

Every remaining blocker converges on the same act. Re-observation would
simultaneously: capture three dated cells for all nine comparative
instances under the already-fixed header detection (including HON's,
whose anchors would be re-taken); test whether widened vocabulary
changes what a reading accepts; and settle Citigroup's extraction
failure. Further offline work would postpone that test, not replace it.

**Smallest funded validation plan — not run.**

- **Specimen set: 4 companies, ~20 readings.** **TSLA** and **ALL**
  (comparative recovery, clean row identity); **HON** (comparative
  recovery where identity currently fails — the one that tests
  re-anchoring); **KO** (the pure vocabulary case, blocked on all three
  factors by labels alone).
- **Hypotheses.** *TSLA/ALL*: a fresh reading stores three dated cells
  where the old one stored one — proving the header fix reaches the
  store. *HON*: re-anchoring restores row identity. *KO*: with
  `CONCEPT_LABELS` unchanged, KO still establishes nothing — which
  isolates vocabulary as the remaining cause rather than the reader.
- **Success**: TSLA and ALL each store ≥2 dated cells per affected row,
  with current-period values unchanged; HON's anchor matches its parse.
  **Failure**: one cell still stored, which would mean the loss is in
  the reading prompt rather than the parse and would redirect the work
  entirely.
- **Prepared before spending**: nothing is strictly required — the
  extractor already calls `row_figures` and the header fix is already
  merged. Optional and cheap: the acquisition-provenance field from §3,
  if the owner wants expanded cells distinguishable in the store from
  the first funded reading onward rather than retrofitted.

**Do not widen `CONCEPT_LABELS` before this specimen set runs.** KO is
the control: if a re-read still establishes nothing for it, vocabulary
is confirmed as the cause; widening first would destroy the control.

## Scope compliance

`CONCEPT_LABELS` untouched · financial concept semantics untouched ·
Business Quality questions, thresholds and completeness untouched ·
financial-model selection untouched · nothing re-observed · no LLM
call · no credit spent · Citigroup not repaired · the six-company
question-contract problem not touched · no narrative knowledge, UI,
crypto, or PR #145.
