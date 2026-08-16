# A reading loses its vote, never its record

**Status: built, BQ15. No schema bump. 30 of 175 stored readings
superseded on the evidence of the filings themselves; **zero bands
lost**; every fact, figure and provenance line byte-identical.**

**One unintended model call was made and is disclosed in §10.** The
audit spent nothing; `movrvest financials ALL`, run to check a rendered
surface, acquired one narrative reading because that command is not the
read-only door it documents itself as. The brief said no API spend, and
one reading was spent.**

BQ14 ruled targeted supersession. This implements it and nothing wider.

> **The audit withdrew 30 readings across six companies and cost the
> corpus nothing.** HIGH 3 · MEDIUM 4 · LOW 1 · UNKNOWN 16, before and
> after — where a schema bump would have taken all eight bands to
> UNKNOWN and destroyed 325 provably-valid anchors.
>
> **Honeywell changed the rule.** Its rows and labels are exactly where
> the reading said and its figures are the filer's; today's header
> detection reads that table so poorly every column comes back unheaded.
> BQ14's research classifier called that INVALID. It is not — it is this
> platform failing to look, and withdrawing evidence for it would punish
> a reading for our own regression. **Only what today's parse positively
> reads may refute a reading**, so Honeywell keeps its authority and the
> corpus shows `undecidable=5` where BQ14 recorded ten invalid anchors.
>
> **And KO is measured, not asserted: supersession does not reach it.**
> Appending its five paid readings leaves it UNKNOWN, because its stored
> readings are valid — its blocker is vocabulary, which is a different
> axis and is not implemented here.

---

## 1. The representation

One defaulted field on the observation:

```python
superseded_because: str | None = None
```

- **The record survives whole.** A superseded reading stays in the file,
  in the order it was taken, with every fact, figure, row and provenance
  line untouched. It loses a vote, not its history.
- **No migration, and none possible to need.** The field is written only
  when set, so a store of entirely active readings encodes
  byte-identically to one written before the field existed, and an entry
  without the key loads as authoritative. `located_among`'s precedent,
  applied again — *defaulted, never invented*.
- **Not the schema version.** `STATEMENT_SCHEMA_VERSION` is untouched at
  3, because adding a defaulted field changes neither what a reading was
  shown nor what it was asked.
- **Write-once.** `store.supersede` records a reason where there is none
  and refuses to restate, soften or clear one that exists. That is what
  keeps it from becoming a general write door onto stored evidence: the
  only transition expressible is active → superseded, once.

Measured on the live corpus: the six changed files show **60 insertions
and 30 deletions**, and every deletion is a `"statement":
"income_statement"` line gaining a trailing comma. **No evidence line
moved** — checked programmatically, `facts` and `reading` compared
observation by observation across all 175: **0 mutated.**

## 2. The rule for removing authority

> **A reading loses its vote only where today's parse of the same
> immutable filing positively reads something different at the cell the
> reading cited.**

Every verdict terminates in a printed cell — the label the filer typeset
on that row, the figure printed in that column, the header above it, and
how many headed cells the row carries.

**The asymmetry is the safety property**, and Honeywell forced it. Where
the parse produces *nothing* at the address — a moved row, a row that no
longer exists, a table this platform can no longer head, fewer cells
than the reading captured — the audit has not found a contradiction, it
has failed to look. All of those are `UNDECIDABLE` and **keep**
authority.

| Source evidence | Verdict |
|---|---|
| the filer prints the same figure under the same header, and the row is the same width | ACTIVE |
| the filer heads that figure with a year and the reading recorded the banner above it | **STALE_PROVENANCE** |
| the filer prints more headed cells on that row than the reading captured | **STALE_PROVENANCE** |
| the filer prints a *different figure* on that row at that column | **INVALID_EXTRACTION** |
| today's parse heads no column there / the row moved / the row is gone / today's parse finds fewer cells | UNDECIDABLE |
| the reading located nothing at all | UNDECIDABLE |

**Pinned structurally, not by intention.** `tests/test_statement_audit.py`
walks the audit module's own syntax tree — docstrings excluded, so a
module that explains what it refuses to import does not fail for saying
so — and asserts it uses none of `BusinessQuality`, `QualityBand`,
`quality_of`, `band`, `band_for`, `score`, `favourable`, `adverse`,
`sense_of`, `FinancialUnderstanding`, `financial_engine`,
`answer_questions`, `assess`, `recommendation`, `portfolio`, `decide`.
A second test asserts no company symbol appears as a string literal.
A third rules a rising row and a falling row and asserts the verdicts are
identical.

**The proof it worked is the outcome**: one rule promoted ALL to HIGH,
demoted TSLA and WMT to LOW, and reached KO not at all — and it names no
company anywhere.

### Why absences are not audited

A stored absence — *"no cell was located for this concept"* — is a claim
about the reading, and the document cannot refute it. The tempting rule
is that today's `CONCEPT_LABELS` admits a figure-bearing row the reading
recorded absent, so the reading must be wrong. **It is declined**, for
two measured reasons:

1. **It would let the parser decide which row answers a concept** — the
   authority BQ7 deliberately kept out of the parser.
2. **It fires on ordinary reader fallibility**, which is what the quorum
   exists to absorb. BQ14 measured the label-match test across the corpus
   and found **two of its four hits were false**: AXP's `Revenues` and
   C's `Revenues (1)` are bare section headings carrying no figures, and
   C's `Net income` match returns EPS (`$ 7.11`) under a header of
   `1,832.0`.

**The consequence is stated rather than hidden: KO is not reached**, and
§9 measures exactly what that costs.

## 3. The operator

```bash
movrvest statement-audit [SYMBOL] [--supersede]
```

Read-only by default — it classifies and prints and changes nothing.
`--supersede` is the explicit maintenance action. **Nothing supersedes
from an ordinary read**; no page, service or consensus can reach the
audit, which is why it lives in a command and takes a flag.

It costs one fetch per company, asks no model, and spends nothing.

## 4. Consensus behaviour

- `statement_consensus_of` counts only readings that still hold
  authority, and carries `superseded_count` beside `observation_count`.
- `supersession_caveat()` says what was not counted, in full: *"This
  filing holds 10 stored readings of this statement and 5 of them carry
  authority… Those readings are **superseded rather than deleted**: each
  is still stored, still dated and still attributable."*
- `_answer` and `_settled` are **untouched**. The quorum is **untouched**
  at 5. What changed is which readings are handed to them.
- A statement whose every reading was withdrawn is an **absence**, not an
  error: `authoritative()` is the door every caller knocks on first, so a
  page view words it rather than raising.

Four read paths needed that door, and three of them were live defects
found by running the surfaces rather than by reading them:

| Path | Was | Now |
|---|---|---|
| `FinancialStatementService._latest` | **raised** — every dossier for TSLA, C, MTB, ALL 500s | absent, worded |
| `FinancialsCommand` | **raised** — `movrvest financials TSLA` tracebacks | worded refusal naming the audit |
| `statements()` cached branch | would serve a set that can settle nothing | re-reads |
| `observe()` stopping rule | **counted superseded readings toward the target, so an audited statement could never be re-read** | counts authoritative readings; target unchanged |

That last one is the one that mattered most: without it, supersession
would have been irreversible.

**And two absences are told apart.** `withdrawn()` sits beside
`established()`, so the platform says *"TSLA's income statement has been
read, and an offline audit of the filing withdrew all 5 of those
readings"* and never *"no financial statement has been read for TSLA"*.
`movrvest financials ALL` prints *not yet observed: cash flow statement*
on one line and *read and withdrawn: income statement* on the next.

### Measured, before → after

| | ALL | TSLA | WMT | KO |
|---|---|---|---|---|
| agreement groups before | 1 group, 5 readings | 1 group, 5 | 1 group, 5 | 1 group, 5 *(no figure)* |
| active after | 0 income (5 balance sheet) | **0** | 0 income (5 balance sheet) | **5 — unchanged** |
| superseded after | 5 | 5 | 5 | **0** |

## 5. The 400-anchor partition, reproduced

| BQ14 research | BQ15 operator | Agrees? |
|---|---|---|
| 400 anchors | 400 anchors | ✔ |
| 325 VALID | 325 unrefuted | ✔ |
| 65 STALE | **65 stale** — ALL 10, C 5, MTB 10, RF 10, TSLA 20, WMT 10 | ✔ |
| 10 INVALID (HON) | **10 UNDECIDABLE** | ✘ **explained, not tuned** |
| 17 companies wholly valid | 17 | ✔ |
| defect confined to 7 income statements | **6 superseded + HON kept** | ✔ |
| all 26 balance-sheet anchors valid | 26 | ✔ |

**The one difference is Honeywell, and the implementation is right.**
BQ14's classifier treated *"no headed figure at that cell"* as proof the
stored claim was unsupportable. Measured directly: HON's row 5 is still
labelled `Net sales`, row 21 is still `Net income`, and today's parse
returns **zero** headed figures on either, because `header_row` settles
on a row that labels only column 0. The reading is not refuted; it is
unreadable *by us*. BQ14's report also attributed HON to a moved row
index — that is wrong too, and this measurement corrects it.

At the observation level: **active 140 · stale_provenance 30 ·
undecidable 5.**

| Company | Readings superseded | Why |
|---|---|---|
| ALL | 5 | the filer heads 67,685 with `2025`; the reading recorded `Years Ended December 31,` |
| C | 5 | the filer heads $ 59,792 with `2025`; the reading recorded `Years ended December 31,` |
| MTB | 5 | the filer heads $ 2,851 with `2025`; the reading recorded `Year Ended December 31,` |
| RF | 5 | the filer heads $ 2,156 with `2025`; the reading recorded `Year Ended December 31` |
| TSLA | 5 | four concepts, all headed `2025`; the reading recorded `Year Ended December 31,` |
| WMT | 5 | the filer heads 713,163 with `2026`; the reading recorded `Fiscal Years Ended January 31,` |
| **HON** | **0** | undecidable — today's parse heads no column on those rows |

## 6. Surviving paid observations

Inventoried before any claim was made, and copied out of `/tmp` into the
session scratchpad on first sight, because `/tmp/bq12` was already gone.

| Company | Paid originally | Still present | Durable location | Reproducible without a model call? | Enough provenance to append? |
|---|---|---|---|---|---|
| **KO** | 5 (BQ11 ×1 + BQ12 ×4) | **5** | `/tmp/bq11/statements` (+ scratchpad copy) | **no** — an LLM reading cannot be regenerated offline | **yes** — schema 3, own `PrimarySource`, own `Provenance`, dated `2025`, 3 cells |
| **ALL** | 5 (BQ13) + 1 (BQ8) | **6** | `/tmp/bq13`, `/tmp/bq8` | no | yes |
| **TSLA** | 5 (BQ13) + 1 (BQ8) | **6** | `/tmp/bq13`, `/tmp/bq8` | no | yes |
| **WMT** | 5 (BQ13) | **5** | `/tmp/bq13` | no | yes |

**Nothing is lost.** All twenty BQ11–BQ13 readings survive, plus three
from BQ8. Every one is a real stored observation carrying its own source
and reading provenance — **none was reconstructed from a report**, and
none could be: a report describing a paid reading is prose, not an
observation.

**They are still only in `/tmp` and a session scratchpad.** Neither is
durable. Preserving them is a precondition of §11, not an afterthought.

## 7. The promotion boundary

**No authorised path exists, and this slice does not invent one.**

Checked against the brief's own requirements:

| Requirement | Ordinary `observe-statements` | Ingesting a surviving paid observation |
|---|---|---|
| append only | ✔ | ✔ — `store.append` is the same door |
| no mutation of history | ✔ | ✔ |
| no copying from prose | ✔ | ✔ |
| no manual JSON surgery | ✔ | ✔ |
| explicit / operator-driven | ✔ | **✘ — no command does this** |
| source provenance intact | ✔ | ✔ |

The one unmet requirement is the operator itself: `observe-statements`
**re-reads and spends**; nothing ingests an observation already taken
against a different evidence root. Building one is not implementing
BQ14's ruling — it is answering the provenance question BQ14 explicitly
left open (*may an observation acquired outside `data/` enter it?*).

**So production stops here, superseded and ready.** The `observe` fix
(§4) is what makes "ready" true: TSLA has 0 authoritative readings, so a
funded `observe-statements TSLA` would take all five.

## 8. Supersession alone — the analytical effect

Production, before against after, with **no fresh observation involved**:

| Bands | before | after |
|---|---|---|
| HIGH | 3 | **3** |
| MEDIUM | 4 | **4** |
| LOW | 1 | **1** |
| UNKNOWN | 16 | **16** |

**Zero bands lost.** Three companies lost a factor, and every one was
already UNKNOWN:

| Company | active readings | answered factors | band |
|---|---|---|---|
| ALL | 10 → 5 | 1 → **0** | UNKNOWN → UNKNOWN |
| TSLA | 5 → **0** | 1 → **0** | UNKNOWN → UNKNOWN |
| WMT | 10 → 5 | 1 → **0** | UNKNOWN → UNKNOWN |
| C, MTB | 5 → **0** | 0 → 0 | UNKNOWN → UNKNOWN |
| RF | 10 → 5 | 0 → 0 | UNKNOWN → UNKNOWN |
| the other 18 | unchanged | unchanged | unchanged |

**That the cost is zero is a fact about this corpus, not a property of
the mechanism.** Every defective reading happened to sit under a company
already below the two-factor minimum. A future audit could withdraw a
band, and should.

Against the alternative BQ14 costed: a schema bump takes **all 24
companies to no evidence and loses all 8 bands** to fix the same 30
readings.

## 9. Lazy rebuilding, proved

On a copy of the superseded corpus, appending the surviving paid
readings through the ordinary `append` door, **one company at a time**:

| Stage | ALL | TSLA | WMT | KO | other 20 |
|---|---|---|---|---|---|
| superseded, nothing appended | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | **unchanged** |
| + 5 for ALL | **HIGH 80** | UNKNOWN | UNKNOWN | UNKNOWN | **unchanged** |
| + 5 for TSLA | HIGH 80 | **LOW 40** | UNKNOWN | UNKNOWN | **unchanged** |
| + 5 for WMT | HIGH 80 | LOW 40 | **LOW 40** | UNKNOWN | **unchanged** |
| + 5 for KO | HIGH 80 | LOW 40 | LOW 40 | **UNKNOWN** | **unchanged** |

All four properties hold:

- **unaffected companies retain authority** — 0 of the other 20 moved at
  any stage;
- **affected companies temporarily lose factors** — and say so honestly;
- **a fresh reading restores authority for exactly the company re-read**,
  and for no other;
- **no global rebuild is required.**

**And KO is the honest negative result.** Five paid readings appended, and
it stays UNKNOWN with 0 answered factors — because its stale readings
were *not* superseded, so the five *no figure located* answers still tie
against the five that find `Net Operating Revenues`. Exactly what BQ14
predicted, now measured through the real append path.

This is the advantage over a schema bump stated as a measurement rather
than an argument: under a bump, every one of those rows would read
UNKNOWN until the whole corpus was re-read.

## 10. One unintended spend, and the defect that caused it

**`movrvest financials` is not read-only, and its own docstring says it
is**: *"Read-only and free. It derives from what is stored and never
observes."* It does observe. `FinancialsCommand.run` asks
`PlaybookSelectionService.select`, which calls
`CompanyKnowledgeService.knowledge()` — the **acquiring** door — rather
than `established()`. Running `movrvest financials ALL` to check a
rendered surface therefore read ALL's 10-K with `gpt-5`.

**What it cost**: one narrative reading, written to
`data/knowledge/ALL.0000899051-26-000031.json`, schema 14, timestamped
`2026-08-16T22:10:38Z`. Nothing else in `data/` was acquired; the audit
itself fetches filings and asks no model.

**What it changed analytically**: nothing. It is **one** observation
against a quorum of five, so it reads `insufficient_quorum`, grants no
consensus, and the corpus bands are identical — HIGH 3 · MEDIUM 4 ·
LOW 1 · UNKNOWN 16 — measured after the fact.

**The observation is kept, not deleted.** It is a genuine, correctly
formed, append-only reading of an immutable filing, and this platform
does not delete evidence to tidy a slice's scope. It is disclosed here
instead.

**This is the same defect class as the four in §4** — a surface reaching
an acquiring door — and it is *older* than this slice. It is recorded
rather than repaired, because repairing it means deciding what
`financials` should do when the playbook is ungrounded, which is a
separate ruling.

## 11. Recorded, not solved

- **The vocabulary axis is unimplemented**, so KO cannot be released by
  supersession. Its blocker needs a *contract record* — which labels this
  platform accepted when — and that is the general fix BQ14 named and
  deferred. It is not a parse question and does not belong in this audit.
- **The paid observations are not durable.** Twenty readings sit in
  `/tmp` and a session scratchpad.
- **`superseded_count` is 0 for every live consensus today**, because
  every affected statement was withdrawn *wholly*. The caveat is written,
  tested and verified against a mixed set — it fires the moment a fresh
  reading is appended beside a withdrawn one.
- **Honeywell's real defect is now precisely located** and still not
  repaired: `header_row` settles on a row labelling only column 0. Out of
  scope, and the audit refuses to punish the reading for it.

## 12. The next funded action

**Ingest the four surviving sets, once a promotion path is ruled — 0 new
readings.**

The evidence for ALL, TSLA and WMT is bought, validated, contract-valid
and measured to deliver HIGH 80, LOW 40 and LOW 40 through the ordinary
append door. What is missing is a ruling and a small operator, not money.

**Before anything else, the artifacts should be moved somewhere durable.**
They are the whole value of BQ11–BQ13 and they are one `/tmp` sweep from
being a re-spend.

If the ruling is that isolated observations may not enter production,
then the funded action is **15 readings** — ALL, TSLA, WMT at quorum,
taken directly against the production root, which the `observe` fix now
permits. KO needs 5 more *and* the vocabulary axis before it can move at
all.

## Scope compliance

`STATEMENT_SCHEMA_VERSION` unchanged at 3 · `_answer` and `_settled`
untouched · quorum untouched at 5 · Business Quality, its questions,
thresholds and completeness untouched · vocabulary untouched · **no
statement re-observed** · **the audit itself makes no model call**, and
**one unintended narrative reading was spent** through `movrvest
financials` and is disclosed in §10 · no isolated
observation copied into production · HON, Citigroup and the
financial-company question contract untouched · no UI, no crypto, no
PR #145 · every stored fact, figure and provenance line byte-identical,
verified across all 175 observations.
