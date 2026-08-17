# A figure the filer printed, and the concept it may not answer

**Status: built, BQ23. Enforces the semantic invariant BQ22 established.
No model call, no vocabulary edit, no stored byte changed, no fingerprint
moved. Stopped for review.**

> **Goldman prints `Total net revenues` 58,283 and this platform no longer
> calls it total revenue.** The rule reads no words: it reads that the
> statement typesets `Net interest income` 13,559 one row above, in the
> same column of the same table, so the figure is a total *after*
> financing cost. Eleven live top lines are untouched, and **three of the
> eleven carry the word *net* in their label** — which is the control that
> proves the rule is structural.
>
> **GS `HIGH 80` → `UNKNOWN`. JPM `MEDIUM 62` → `UNKNOWN`.** Measured, not
> preserved. The aggregate is **HIGH 3 · MEDIUM 4 · LOW 3 · UNKNOWN 14**,
> derived by the sweep rather than written down.
>
> **A refusal is a third state and never renders as the filer's silence.**
> `movrvest statements GS` prints *REFUSED — constructed from net interest
> income* beside the figure the filer printed, because *no figure located*
> would be a false claim about a document that prints one.

---

## 1. The implementation seam

Five files, and the boundary each one holds:

| | file | what it owns |
|---|---|---|
| 1 | **`app/domain/financing_cost_refusal.py`** *(new)* | the rule. `GOVERNED`, `RefusalStanding`, `FactRefusal`, `refusal_for`, `precedes_in_one_column`. Imports `financial_statements` and `tabular_evidence` and nothing else — it cannot reach a store, a document or a company |
| 2 | `app/domain/financial_statement_consensus.py` | applies it. `statement_consensus_of` gained a **second pass**, `_refused` / `_refuse_one`; `ConsensusFact` gained `refused` and `absent_because`; the consensus gained `refused_facts` and `refusal_caveat()` |
| 3 | `app/services/financial_engine.py` | `_unestablished` now reads `fact.absent_because` instead of `fact.unlocated_because`, so a measure that lost its denominator says why in the rule's own words |
| 4 | `app/commands/statements.py` | renders the third state — the refusal, the filer's figure, and the reason |
| 5 | `tests/test_financing_cost_refusal.py` *(new)* | 22 tests: the three specimens, six structural controls, the eleven-company corpus control, the BCS/NWG regression, the derived baseline, and byte identity |

**Why a second pass rather than a wider `_fact_consensus`.** Each claim is
settled on its own first — content-blind strict majority over the readings
entitled to answer it — and only then is the settled set asked whether one
concept's presence disproves another's semantic role. A single pass could
not do it: the figure that disproves a top line belongs to a *different
concept*, and it must be settled before it can disprove anything. This is
the first cross-concept derivation in the statement stream, and it is
named as one rather than arriving as a helper.

---

## 2. The formal predicate

```text
refused(concept, figure, established) ⟺
      concept ∈ GOVERNED
    ∧ figure ≠ ∅
    ∧ marker = established[GOVERNED[concept]] ≠ ∅
    ∧ marker.cell.table  = figure.cell.table       (one scale)
    ∧ marker.cell.column = figure.cell.column      (one period)
    ∧ marker.cell.row    < figure.cell.row         (above it)
```

with `GOVERNED = {TOTAL_REVENUE: NET_INTEREST_INCOME}` — one pair,
declared as data rather than branched on, so a second structural refusal
cannot quietly widen this one.

Three properties, each pinned:

- **One table, one column.** Borrowed verbatim from `comparable`: one table
  is one scale, one column is one period. A subtotal in another table is
  not known to feed this total; one in another column is a different
  year's.
- **Positively stated.** Anything the predicate cannot establish leaves the
  figure alone — the same direction `absence_supersession` takes when a
  contract cannot be bounded.
- **`established` is passed in.** The rule receives one statement's settled
  figures and reaches nothing. It has no store, no document, no symbol.

A test strips every docstring with `ast` and asserts the executable code
contains no company name and none of `"net"`, `casefold`, `lower()`,
`startswith` or `in label`. The prose cites the filings that earned the
rule, as it should; the code cannot read a word.

---

## 3. How this differs from absence supersession

The two modules are siblings and are deliberately not merged.

| | `absence_supersession` (BQ20) | `financing_cost_refusal` (BQ23) |
|---|---|---|
| what it acts on | an **absence** | a **positive** |
| the question it asks | *could the reader that recorded this have accepted the label?* | *is this figure the quantity the concept names?* |
| the evidence | the producing vocabulary contract, bounded from the published lineage | the filer's own typesetting of two concepts of one statement |
| the direction | restores a claim that a stale contract deadlocked | removes a claim a structure disproves |
| what it leaves behind | a **count** — `withdrawn_absences` | the **figure** — `FactRefusal`, with the marker that disproved it |
| concept-locality | the concept whose vocabulary moved | the concept the pair governs |

Folding them together would make both unreadable: one is about what a
reader *could see*, the other about what a number *means*. And the
asymmetry in the last row is not cosmetic. A withdrawn absence has nothing
worth carrying — it said *no figure* and that sentence adds nothing. A
refused positive has a figure the filer really printed, and discarding it
would let the consensus make a false claim about the document.

---

## 4. Goldman Sachs, before → after

| | before | after |
|---|---|---|
| the reading | `Total net revenues` 58,283, 5 of 5 | **unchanged, byte for byte** |
| `total_revenue` | located | **refused** — `constructed from net interest income` |
| `net_income` | `Net earnings` 17,176, 5 of 5 | unchanged |
| `net_interest_income` | 13,559, 5 of 5 | unchanged |
| profitability | **answered** — net margin 29.5% *excellent* | not answerable |
| revenue growth | **answered** — +8.9% *moderate* | not answerable |
| earnings growth | answered — +20.3% *strong* | **unchanged** |
| factors answered | 3 | **1** |
| band | **HIGH 80** | **UNKNOWN** |

The reconciliation, checked in the test from the filer's own subtotals:
`Total non-interest revenues` 44,724 + `Net interest income` 13,559 =
**58,283 exactly.**

The live surface:

```text
income statement
  total_revenue
    figure: REFUSED — constructed from net interest income
      the filer prints: "Total net revenues" = 58,283 under "2025"
                        (Consolidated Statements of Earnings, table 0, row 12, column 3)
      because: The statement prints "Net interest income" 13,559 at table 0, row 11,
               column 3, above "Total net revenues" 58,283 at table 0, row 12, column 3
               and in the same column ("2025"). So the figure is a total after financing
               cost, not the gross total_revenue this concept names, and it is a
               different economic quantity. The filer did print it, and this platform
               holds no concept for it yet.
    located: 5 of 5 agree
```

`located: 5 of 5 agree` still stands, because the readings did agree. What
changed is what that agreement is allowed to settle.

## 5. JPMorgan, before → after

| | before | after |
|---|---|---|
| `total_revenue` | `Total net revenue` 182,447, 5 of 5 | **refused**, same standing |
| profitability | **answered** — net margin 31.3% *excellent* | not answerable |
| revenue growth | **answered** — +2.8% *weak* | not answerable |
| earnings growth | answered — −2.4% *declining* | **unchanged** |
| factors answered | 3 | **1** |
| band | **MEDIUM 62** | **UNKNOWN** |

`Noninterest revenue` 87,004 + `Net interest income` 95,443 = **182,447
exactly.**

**JPMorgan's one favourable point was that net margin.** It is the clearest
statement of what the slice does: the band that made JPM *MEDIUM rather
than LOW* rested entirely on a denominator that excludes a bank's largest
cost, compared against Apple's on gross sales.

## 6. American Express — the consistency check

**Unchanged, and that is the point.** AXP holds five readings answering
*no figure located* for `total_revenue`, settled by majority, because its
label was never in the vocabulary. The structural rule finds no located
figure to refuse, so `refused` is `None` and the absence stands exactly as
it did.

| | |
|---|---|
| `total_revenue` | *no figure located*, 5 of 5, `by_majority=True` |
| `refused` | `None` — refused by vocabulary, not by structure |
| `net_interest_income` | **17,364, 5 of 5** — the marker that *would* have refused a located total |
| re-read | **none.** No observation of AXP was taken |

One economic quantity, one outcome, whichever route reaches it:
`Total non-interest revenues` 54,865 + `Net interest income` 17,364 =
**72,229**, the figure the vocabulary declines and the structure would
have declined too.

---

## 7. The negative controls

### The eleven gross top lines, from the live corpus

Every class-A occurrence keeps its concept, and `refused` is `None` for
all eleven:

| | label | | label |
|---|---|---|---|
| AAPL | **`Total net sales`** | PG | **`NET SALES`** |
| ALL | `Total revenues` | TRV | `Total revenues` |
| CB | `Total revenues` | TSLA | `Total revenues` |
| DIS | `Total revenues` | UNP | `Total operating revenues` |
| HON | **`Net sales`** | WMT | `Total revenues` |
| MET | `Total revenues` | | |

**Three of the eleven carry the word `net`** — Apple, Honeywell and
Procter & Gamble — and none is refused. Their `net` is net of returns and
allowances, a revenue adjustment rather than an expense line, and the
structure says so: not one of them establishes a net interest income
subtotal at all. A rule that read the label would refuse all three.

### The structural controls

| control | result |
|---|---|
| marker **below** the total (row 17 vs row 4) | **not refused** — order is the rule |
| marker in **another table** | **not refused** — one table is one scale |
| marker in **another column** | **not refused** — one column is one period |
| **no marker at all** | **not refused** — the state eleven live totals are in |
| the marker's own concept | **never refused** — a statement cannot argue itself out of its own marker |
| `net_income`, which sits below the marker on every bank statement | **not refused** — only the governed pair is |
| **a marker present but structurally apart**, constructed because the corpus has no such case: `Total revenues` at row 4, `Net interest income` at row 18 | **not refused** |
| the same two concepts **reversed**: marker at row 4, `Total revenues` at row 18 | **refused** — and the label contains no `net`, which is the other half of the same proof |

The last pair is the one that matters. The same two concepts, the same
labels, the same figures — only the order differs, and only the order
decides. That is what makes the rule structural rather than *if the
company is financial* wearing a disguise.

### Union Pacific, named because it is the nearest miss

`Total operating revenues` 24,510, earned by BQ19 on the filer's own
arithmetic, **still located and still unrefused**. UNP prints interest
expense *below* its top line — the ordinary industrial shape — and
establishes no net interest income at all.

---

## 8. Barclays and NatWest — the regression control

Neither has a located top line: `total income` is not in the vocabulary,
and BQ19 refused it for a parent-company collision at M&T. So the
simulation asks what the rule would do **if that label were ever
accepted**, using each company's own established marker:

| | its established `Net interest income` | the row it prints `Total income` on | simulated outcome |
|---|---|---|---|
| **BCS** | 14,501 at **t0 r4 c2** | **r12** | **refused** — `constructed from net interest income` |
| **NWG** | 12,829 at **t0 r5 c4** | **r11** | **refused** — same standing |

The marker is read from the store; only the total's position is supplied,
at the row BQ22 measured, because there is no located figure to read it
from — which is exactly why it is a simulation. **Nothing was promoted, no
vocabulary was widened, and neither company was re-read.**

So `total income` now has two independent reasons to be refused, one
lexical and one semantic, and the semantic one would survive if the
lexical one were ever overturned.

---

## 9. The production baseline, recomputed

| | HIGH | MEDIUM | LOW | UNKNOWN |
|---|---|---|---|---|
| before | 4 | 5 | 3 | 12 |
| **after** | **3** | **4** | 3 | **14** |

Derived by the sweep over the production store, not hard-coded anywhere.

**The exact vote change, per mover:**

| | factors before | factors after | why |
|---|---|---|---|
| **GS** | profitability *excellent* (1 pt) · revenue growth *moderate* (0) · earnings growth *strong* (1 pt) → **2 of 3 favourable → HIGH 80** | earnings growth *strong* alone → **1 answered** | both revenue-dependent factors lost their denominator; `MINIMUM_ANSWERED` is 2, so no band is claimed |
| **JPM** | profitability *excellent* (1 pt) · revenue growth *weak* (0) · earnings growth *declining* (0) → **1 of 3 → MEDIUM 62** | earnings growth *declining* alone → **1 answered** | the same, and the lost factor was its only favourable one |

**No other company moved**, and that is pinned rather than asserted: a
test runs the assessment twice — once as production does, once over a
consensus with each refusal reversed by hand — and requires the set of
companies whose band differs to equal exactly the set carrying a refusal.

Neither UNKNOWN is a finding about a bank. Both are this platform saying
it holds no comparable top line, which is what was true all along.

---

## 10. Nothing was written, and no contract moved

| | |
|---|---|
| `git status --porcelain data/` | **empty** |
| stored statement observations | **byte-identical** — the working tree matches `HEAD` exactly |
| `TOTAL_REVENUE` fingerprint | **`ea9df9c5adbc7f44`**, unchanged, 14 forms |
| `vocabulary_contracts.PUBLISHED[-1]` | `ea9df9c5adbc7f44` — the lineage still covers the live vocabulary |
| `registry_is_current(TOTAL_REVENUE)` | **True** — absence supersession keeps working |
| `produced_under` on every GS reading | **`()`**, and `produced_contract_for(TOTAL_REVENUE)` is `None` |

**Both accepted forms are still accepted as vocabulary.** `total net
revenue` and `total net revenues` remain in `CONCEPT_LABELS`, and a test
asserts they do — because the rule refuses a **figure**, never a label.
Deleting them lexically would wrongly refuse an industrial that prints
`Net revenues` meaning net of returns, which is class A. That is why no
fingerprint moved and why BQ20's registry needed no extension.

A test re-reads GS's five observations after the derivation and asserts
they are equal to what was read before it, that each still reports
locating `Total net revenues`, and that provenance is untouched. **This is
a semantic authority rule downstream of extraction, not a producing-contract
change.**

---

## 11. Gates

| | |
|---|---|
| `pytest` | **2,827 pass** (2,805 before, +22) |
| `ruff check` | clean |
| `ruff format` | clean, 1,001 files |
| `mypy app` | clean, 594 files |
| `git status --porcelain data/` | empty |

**Two existing tests were re-specimened, not weakened.**
`tests/test_score_derivation.py` used JPMorgan as a live 62 with three
distinct verdicts, and PG-vs-JPM as the pair that only verdicts separate.
Neither claim was about a bank. Union Pacific carries the first shape
(`excellent`, `weak`, `moderate`) and **Apple vs Chubb** carries the second
exactly — identical sense mix, different verdicts — which is a better
specimen anyway: two companies of different kinds at the same score. Both
docstrings record why the specimen changed.

---

## Recorded, not solved

- **The concept the refused figure belongs to is still unnamed**, and the
  refusal says so in its own words: *"this platform holds no concept for it
  yet."* Naming it turns two UNKNOWNs from a loss into a relocation, and it
  needs a funded re-observation to establish, which is why it is not here.
- **A quality factor's `because` quotes its first gap, not the refusal.**
  GS's profitability consults gross margin, operating margin and net
  margin; the first two fail on concepts this filer prints no line for, so
  `because` names gross profit and the refusal appears in `gaps` alongside
  it. That ordering predates this slice. Revenue growth consults one
  measure and does quote the refusal, and `movrvest financials` shows it on
  both margins in full.
- **The predicate requires one table.** Were a filer ever to split its
  income statement so the net interest subtotal and the top line landed in
  different tables, the rule would not fire. No filing in the corpus does
  that — GS, JPM, AXP, BCS and NWG all print both in table 0 — and the
  conservative direction was chosen deliberately, because a cross-table
  claim about what feeds what is not established by position alone.
- **`refusal_caveat()` is on the consensus and no surface calls it yet.**
  Built because a surface that could only see located-or-absent would
  report a refusal as the filer's silence; `movrvest statements` renders
  the per-fact refusal instead, which is finer. The caveat is the
  statement-level sentence a dossier section would want.

## Scope compliance

`FinancialModel.BANK` not activated · no net-revenue concept introduced ·
no bank profitability factor · **`NII + noninterest income` computed
nowhere in `app/`** · COF/FITB not repaired · DB/MUFG not fixed · HON
untouched · KO not re-read · no vocabulary widened or narrowed · no
production observation changed · no model or API call · no company named in
the rule.
