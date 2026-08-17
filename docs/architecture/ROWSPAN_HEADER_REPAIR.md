# The stub that spans down, and the year that landed on the label column

**Status: built, BQ28. Phase 0 executed and merged (#177). The parser
repair is offline, generic, and inert on every stored byte: no model
call, no vocabulary change, no fingerprint moved, no production write.
Stopped for ruling on the one paid slice the provenance demands.**

> **Honeywell's income statement returned zero headed figures because the
> parser ignored two assertions the filer wrote.** The empty label stub
> above its year row carries `rowspan="2"`, so it occupies the first three
> columns of the year row — and a grid that dropped it shifted `2025`,
> `2024` and `2023` three columns left, onto the label columns, leaving
> every figure under nothing. The repair honours rowspan exactly as
> colspan has always been honoured, and preserves a spanned *number's*
> extent so a year can head the columns its colspan asserted without the
> number ever gaining a second address.
>
> **The corpus sweep found no second company.** Eight concept-rows heal,
> all Honeywell's, across all three of its statements; **zero stored
> anchors anywhere change their verification** — nothing was correct by
> coincidence.
>
> **And the stored evidence cannot be rescued, measured two ways.** The
> stored readings carry the old parse's title-as-header and single-figure
> rows, so HON's band is byte-identical before and after the repair — and
> the audit, re-run under the repaired parse, now rules all five income
> readings **stale_provenance**. New observations are genuinely required,
> and BQ13's lesson says the audit must land first.

---

## 0. Phase 0 — the BQ26 batch appended (#177)

| gate | result |
|---|---|
| appended | **15** — GS 5, JPM 5, AXP 5 · 0 incompatible · 0 unproven |
| new concept | **majority for all three** — 58,283 / 182,447 / 72,229 |
| GS/JPM historical `TOTAL_REVENUE` | **withdrawn by BQ27**, 5 each |
| GS/JPM `TOTAL_REVENUE` | **still REFUSED** — BQ23's sentence, byte-identical |
| aggregate | **HIGH 3 · MEDIUM 4 · LOW 3 · UNKNOWN 14**, unchanged |
| second execution | **duplicate=15, appended=0**, state unchanged |

Three tests that pinned the pre-append world were re-specimened to pin the
appended one, none weakened — BQ27's inertness pin became a blast-radius
pin (`{GS: 5, JPM: 5}` and nowhere else), BQ24's no-backfill pin became
*fact ⟺ native stamp*, BQ23's byte-identity pin now distinguishes the two
generations.

---

## 1. The exact failure, at cell level

Income statement, table 0. What the parser saw before the repair:

```text
r0  ['', '', '', 'Years Ended December 31,', '', '', …]          ← title
r1  ['2025', '', '', '', '', '', '2024', '', '', '', '', '',
     '2023', '', …]                                              ← years at c0/c6/c12
r2  ['(Dollars in millions…)' ×15 from c3]                        ← caption
r5  ['Net sales' ×3, '37,442' @ c3, …, '34,717' @ c9, …,
     '33,009' @ c15]                                              ← figures at c3/c9/c15
```

`header_row` settles on r1 — correctly, three distinct namings — but the
years sit at **c0/c6/c12** while every figure sits at **c3/c9/c15**, so
`column_header(3)` is blank and `row_figures` returns **zero headed
figures** for every data row of the statement. The stored readings,
taken under a still older parse, anchor `Net sales` 37,442 with header
`'Years Ended December 31,'` — a title, not a period — and rows holding
**one** undated figure each, which is why both growth factors fail with
*"the row prints no earlier period this platform can date."*

**Why the years are displaced — the filer's own markup, verified twice:**

```html
<td colspan="3" rowspan="2"></td>                 ← the stub, spanning DOWN
<td colspan="15">Years Ended December 31,</td>
<!-- next row starts directly with the years: -->
<td colspan="3">2025</td><td colspan="3"/><td colspan="3">2024</td>…
```

The year row is written **15 columns wide against an 18-column grid**,
because its first three columns are occupied by the stub above. The
browser proof: rendered, `2025` sits at x=953 — exactly over `$ 24,515` —
because the layout engine honours the rowspan the parser dropped.

## 2. The defect class

**Rowspan is not carried down.** The smallest structural defect, and it is
none of the candidate classes alone: the multi-row header, the spanning
header and the column-count mismatch are all *symptoms* of the one dropped
assertion. A second, subordinate defect travels with it: a spanned
*number's* extent was erased entirely (the number is rightly never
repeated into its span, but the extent is the only record of which columns
it heads). Honeywell needs the first; the second closes the general case
the first exposes. **No Honeywell special case exists anywhere** — the
fixture in the tests is named for the filing it reproduces, and the code
never sees a company.

## 3. The corpus sweep for siblings

Every held filing, all three statements, parsed under both behaviours
(rowspan disabled and extents stripped versus the repair), compared on
every concept-bearing row:

| | |
|---|---|
| concept-rows whose headed-figure count changed | **8** |
| companies affected | **HON only** — income (`total_revenue` 0→3, `net_income` 0→3), balance sheet (`total_current_assets` 0→2, `total_current_liabilities` 0→2, `total_equity` 0→2 twice), cash flow (`operating_cash_flow` 0→3, `capital_expenditures` 0→3) |
| stored anchors whose address-verification changed | **0, corpus-wide** |

**HON was the visible failure and the only occurrence** — the same
rowspan'd stub heads all three of its statements — and no apparently
successful reading anywhere was being interpreted correctly by
coincidence: every stored anchor's label still sits at its stored address
under the repaired grid.

## 4. The header invariant

> A numeric cell belongs to a period column exactly where the header row
> names that column — **by the cell the filer printed there, or by the
> extent the filer's own colspan asserted covers it**. A cell of an
> earlier row occupies the columns and rows its rowspan asserted, words
> repeating into what they cover and a number never gaining a second
> address. **A blank the filer did not span stays blank**, and a figure
> beneath it stays a number whose period is unproven.

Derived from markup structure alone — no company, no expected value, no
desired concept, no quality result. The ambiguity rule is pinned in both
directions: an explicit unspanned blank between years is never headed
(the anti-forward-fill control — BQ9's falsified repair cannot
reappear), and explicit pad cells shift nothing.

## 5. The implementation seam

Two files, one boundary:

- **`app/providers/document_text.py`** — `_cells` gains the rowspan
  ledger (`carried`): a cell spanning down occupies its columns in the
  rows beneath, laid down exactly where the earlier row put them, this
  row's own cells filling around them; words repeat downward on the same
  rule colspan repeats them across, numbers and currency never do; capped
  at `_DEEPEST` like `_WIDEST`. It also records the extents of spans
  whose text was not repeated; `_gridded` remaps them through the
  whole-column prune; `_widened` offsets a continuation's.
- **`app/domain/tabular_evidence.py`** — `TableRow.spans` carries the
  extents; `SourceTable.column_header` reads them where the header cell
  itself is blank. **Nothing downstream changed**: no concept extraction,
  no consensus rule, no quality logic — the grid is made truthful before
  financial concepts consume it, which is the whole of §5's demand.

## 6. The controls

| control | result |
|---|---|
| the Honeywell shape (rowspan'd stub + displaced years), structure verbatim | year lands after the stub's columns, figure headed `2025` |
| ordinary single-header table | unchanged, `spans == ()` |
| rowspan'd **label** | names every row it covers, covered rows' cells fill around it |
| rowspan'd **number** | occupies but never repeats — one address |
| spanned year over value + `%` columns | extent heads both |
| currency absorption inside a span | collapses onto the figure, extent correctly not recorded |
| **genuine ambiguous header** (explicit unspanned blank) | **stays unheaded** |
| **misaligned/extra-cell** (explicit pads, no spans) | no shift, each figure under its own year |
| empty spanned cell | covers nothing |
| absurd rowspan depth | capped |

Plus the live specimen: HON's real filing parses to years at c3/c9/c15
heading `Net sales` 37,442/34,717/33,009 and `Net income`
4,772/5,740/5,672 — three dated figures each, all three statements.

## 7. HON downstream, from existing evidence

**Unchanged, and correctly so:**

| | before | after |
|---|---|---|
| concepts | `total_revenue` located (title-as-header, 1 figure), `net_income` same | **identical** |
| factors | profitability answered *strong*; both growth factors unanswerable | **identical** |
| band | UNKNOWN, 1 of 3 | **UNKNOWN, 1 of 3** |

The stored readings recorded what the old parse showed them, and BQ17
forbids reinterpreting stored bytes. The repair changes what a *future*
reading is shown, nothing else.

## 8. Corpus-wide regression sweep

**Zero analytical movers.** Bands: HIGH 3 · MEDIUM 4 · LOW 3 · UNKNOWN 14,
identical before and after — every consensus derives from stored
observations the parse does not touch. The only live surfaces that change
are measurement surfaces re-reading the document (`statement-shape`, the
audit, future readings), and the sweep bounds that change to HON alone.

## 9. Provenance — measured, not assumed

**The repair changes no interpretation of stored evidence, and stored
evidence cannot acquire the repaired facts.** Two measurements:

- **HON's five income readings now audit as `stale_provenance`,
  supersedes=True** — *"the filer heads 37,442 with '2025' and the
  reading recorded 'Years Ended December 31,'"*. The figures are the
  filer's; the provenance around them is not. Under the old parse the
  same audit ruled them UNDECIDABLE, because a parse that headed nothing
  could refute nothing — BQ15's asymmetry working exactly as designed,
  in both directions.
- **No other company's stored anchors move** under the repaired audit
  (the §3 sweep's zero).

**And the append order matters — BQ13's lesson, still loaded.** If five
fresh readings were appended *without* superseding the stale five, the
consensus would settle (same label, same cell, same figure — the anchors
agree) but `_settled` takes the modal answer's row from the **first**
observation that gave it: a stale single-figure row, and growth stays
broken. The stale readings must lose authority first, through the audit
that already exists and now has the evidence to act.

**No fingerprint is involved.** Parse behaviour is deliberately outside
the producing contract (`concept_vocabulary_fingerprint` documents it: an
anchor is checkable against the immutable document), so `TOTAL_REVENUE`
stays `ea9df9c5adbc7f44`, the new concept stays `3e077c247f109a37`,
schema stays 3, and no `vocabulary_contracts` entry is needed. Nothing
fabricated, nothing backfilled.

## 10. The paid gate

**The parser is proven correct offline** — the live filing parses
truthfully, every control passes, and no stored evidence moved. **But
HON's meaningful validation genuinely requires fresh observations**: the
repaired producing boundary has never produced a stored reading, and the
stored ones are now provably stale. Per §10, no spend was made.

**Recommended minimum paid scope, for the next ruling:**

1. run the statement audit for HON's income statement and write its
   supersessions — the mechanism BQ15 built, now with evidence to act on
   (this is free);
2. **5 fresh HON income-statement readings** through the ordinary
   `observe` path — the readings will see headed columns, anchor dated
   three-cell rows, and stamp native provenance;
3. expected, to be measured rather than promised: profitability retained,
   revenue growth and earnings growth become answerable, and HON bands on
   whatever the verdicts say. Nothing was tuned to make it band.

## 11. Gates

**2,892 pass** (2,882 before, +10) · ruff check and format clean · mypy
clean, 595 files · `git status --porcelain data/` empty after the phase-0
commit · bands unchanged.

## 12. Recommended next slice

**HON re-observation under the repaired parse** — the audit write plus
five funded readings, as §10 scopes it. It is the first slice in this arc
where the paid spend follows a parser proof rather than a vocabulary or
semantics question, and it closes the last UNKNOWN whose first decisive
blocker BQ18 classified as a platform defect rather than a filer's
choice.

## Scope compliance

No bank profitability logic · `REVENUE_NET_OF_INTEREST_EXPENSE` still
consumed by nothing · BCS/NWG untouched · COF/FITB/DB/MUFG/RF untouched ·
KO not re-read · revenue vocabulary unchanged · BQ20/BQ23/BQ27 authority
rules unchanged · no quality threshold moved · no model call · no
Honeywell special case in any code path.
