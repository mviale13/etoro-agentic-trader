# The schema is not the contract

**Status: research, BQ14. No code changed, no schema bumped, nothing
re-observed, no credit spent. Production byte-identical. Stopped for
ruling.**

BQ13 measured a wall and named a cause. The wall is real and is
reproduced here. **The cause is wrong, and the correction changes the
answer.**

> BQ13 argued that the header fix postdated the corpus, so the corpus
> was written under an older parse contract, so `STATEMENT_SCHEMA_VERSION`
> is the boundary that should supersede it.
>
> **The header fix and the schema bump are the same commit** —
> `301cfdf`, 2026-08-09 09:07 — and **the corpus was committed inside
> it.** So schema 3 does not separate the two parses. It contains both.
>
> Measured per observation against today's parse: **325 of 400 stored
> anchors are VALID, 65 are STALE, 10 are INVALID.** Seventeen of
> twenty-four companies are wholly valid, and **every one of the 26
> balance-sheet anchors is valid.** The defect is confined to seven
> companies' income statements.
>
> A 3 → 4 bump destroys **175 observations and all 24 companies'
> evidence** — losing **eight live bands** — to repair sixty-five
> anchors on seven companies, of which three currently gain a band.

**Ruling: C — targeted supersession. A global bump is 5× too coarse and
mislabels a defect repair as a contract change.**

---

## 1. What `STATEMENT_SCHEMA_VERSION` actually means

**Three uses in the whole application**, and the shape matters more than
the count:

| Site | Behaviour |
|---|---|
| `financial_statement_store.py:72` | `STATEMENT_SCHEMA_VERSION = 3` |
| `:202` `_encode` | stamps the version **on the file**, once, beside `symbol` and `source` |
| `:246` `_restore` | `if stored.get("schema_version") != VERSION: return ()` |

**The version rides on the file, never on the observation.** So the unit
of supersession is *one filing's entire entry — every statement, every
reading* — and there is no expressible statement about a single
observation's provenance.

**And `append` reads before it writes.** `append` calls `_restore` and
writes `(*existing, observation)`; on a version mismatch `_restore`
returns `()`, so appending to a superseded file silently **discards
every prior observation** and writes a one-observation file at the new
version. That is the supersession mechanism: not a migration, an
erasure-on-next-write.

The statement store has **no** `PREVIOUS_SCHEMA_VERSION` and no
`RELABELED_SCHEMA_VERSION`. Its sibling, `company_knowledge_store.py`,
has both (currently `None`) plus a documented three-way taxonomy of what
a bump can mean — *what a reading was shown*, *what it was asked*, *how
an answer is interpreted*. The statement store has the constant and none
of the vocabulary.

### The declared contract, version by version

From the store's own comments:

- **1** — the stream begins: the income statement located where the filer
  typeset its title, anchors checked by `figure_at`, rows read by the
  platform.
- **2** — statements located as the **run** they form
  (`statement_locator`) rather than by the widest title match. *"schema-1
  balance-sheet readings and schema-2 ones were shown different text."*
  A **shown** change.
- **3** — *"the income statement is asked two more concepts,
  `net_interest_income` and `premium_revenue`, and the balance sheet
  accepts the parent's equity stated with the filer's own name. **Both
  change what a reading is asked**."* An **asked** change.

So, precisely:

> **A statement observation at schema 3 asserts:** for this filing's
> located statement of this kind, *these* concepts were asked; for each,
> a reading named a row of a table this platform parsed, `figure_at`
> checked the named cell against the parse, and the rest of the row was
> read deterministically by `row_figures` — **under the section locator,
> the concept set and the accepted-label set of the code that produced
> it.**

**The last clause is asserted by nothing.** The version names the
*intended* contract; it does not record the *code that ran*.

### Is explicit reporting-period identity a change to that contract?

**No.** `ReportedFigure.column_header` has carried the period since
schema 1, and `figure_at` has always refused a cell whose column has no
header. A reading that stored `Year Ended December 31,` was asserting the
same thing a reading storing `2025` asserts — *this cell's column is
headed thus* — and asserting it **less accurately**, because the parse
handed it the wrong row as the header.

That is a **defect repair**, not a contract change. The observations do
not claim something different; they claim the same thing wrongly. Nothing
in schema 3's declared contract has to move for today's readings to be
compatible with it.

**Which is exactly why `301cfdf` did not document it.** That commit
carried the schema-3 bump *and* the header fix, and the version comment
records only the concepts. The header repair is invisible in the version
history — and that invisibility is the whole defect.

## 2. Agreement semantics — audited, and not independently wrong

`_answer(fact)` reduces a reading to `"{label}" = {printed} at {cell}`.
The six cases the brief names, **measured** against the real function:

| # | Case | Comparable forms | Counted as agreeing? | Correct? |
|---|---|---|---|---|
| 1 | same value, same period | identical | **yes** | ✔ |
| 2 | same value, different explicit periods | differ — 94,827 at col 3 vs 97,690 at col 4 | **no** | ✔ separated by the **cell** |
| 3 | same value, same cell, one dated header and one undated | **identical** | **yes** | ✘ **the defect** |
| 4 | same value, same label, different cell | differ | **no** | ✔ |
| 5 | same value, same concept, different filing | unreachable — `statement_consensus_of` raises on a mixed-document set | — | ✔ |
| 6 | same value across duplicate readings of one filing | 5 fresh TSLA readings → **1** distinct form | **yes** | ✔ by design |

Case 3 is the only misfire, and it is reachable **only across contracts**:

> **Within one contract the column header is a function of the cell.**
> Measured over every stored anchor of ALL, TSLA and WMT in both the
> production store and BQ13's: **0 of 16 cells carry more than one header
> within a single store.** The header comes from the parser, not the
> model, so two readings of one cell under one parse can never disagree
> about its period.

Therefore adding the header to the comparable form would contribute
**zero** discriminating information inside a contract, and only matters
when two contracts are mixed.

### Verdict: A

**`_answer` is correct under the old observation contract, and the real
problem is mixing old and new contracts.** It is not independently wrong.

**And repairing it would not deliver a single band.** With the header in
the comparable form, ALL/TSLA/WMT become 5 stale answers against 5 fresh
ones — a tie, no majority, **unsettled** — which is exactly what KO
already measures (§3). That is a genuine improvement in honesty: silent
displacement becomes visible deadlock. It is not a repair to the wall.

## 3. The wall, reproduced and measured

Production observations plus the surviving isolated artifacts
(`/tmp/bq11` = BQ11/BQ12's KO, `/tmp/bq13` = BQ13's three). Nothing
written, no model called.

### ALL, TSLA, WMT — silent displacement

| Company | stale only | fresh only | **stale + fresh** |
|---|---|---|---|
| ALL | settles `Years Ended December 31,`, 1 cell | settles **`2025`, 3 cells** | **`Years Ended December 31,`, 1 cell** |
| TSLA | settles `Year Ended December 31,`, 1 cell | settles **`2025`, 3 cells** | **`Year Ended December 31,`, 1 cell** |
| WMT | settles `Fiscal Years Ended January 31,`, 1 cell | settles **`2026`, 3 cells** | **`Fiscal Years Ended January 31,`, 1 cell** |

In the mixed set all ten readings collapse into **one** agreement group
— `by_majority` is `True`, ten of ten — and `_settled` returns the first
observation carrying that form, which append-only ordering guarantees is
the oldest. **The fresh readings are not outvoted; they are absorbed.**

### KO — measured, not inferred

BQ13 inferred a tie. It is one:

| Set | Agreement groups | `by_majority` | Settles |
|---|---|---|---|
| stale only (5) | 5× *no figure located* | True | **unsettled** — the modal answer is an absence |
| fresh only (5) | 5× `"Net Operating Revenues" = $ 47,941` | True | **`2025`, 3 cells** |
| **stale + fresh (10)** | 5× *no figure* · 5× `"Net Operating Revenues"` | **False** | **unsettled** |

**Two different failure modes, and the distinction is load-bearing.**
ALL/TSLA/WMT fail *silently* — a majority forms around the wrong reading.
KO fails *honestly* — no majority forms at all, and the platform says the
claim is unsettled. Schema filtering would change both: it removes the
stale side entirely, leaving the fresh five to settle alone.

## 4. What a 3 → 4 bump would do today

Simulated on a **copy** of the corpus with the version rewritten;
production untouched and `git status --porcelain data/` empty.

**Every one of the 24 companies drops to *no evidence at all*.** Not
degraded — absent, because `_restore` discards the whole file.

| Currently banded | Band | After a bump, before re-reading |
|---|---|---|
| DIS, GS, TRV | HIGH | **UNKNOWN (no evidence)** |
| AAPL, CB, JPM, PG | MEDIUM | **UNKNOWN (no evidence)** |
| MET | LOW | **UNKNOWN (no evidence)** |

**Eight live bands lost immediately**, and 175 observations invalidated,
of which **325 of 400 anchor-facts are provably identical to what a
re-read would produce**.

Minimum to regain quorum: **5 readings per statement per company**, and
the store's unit is the *file*, so both statements must be refilled for
the eleven companies that hold two. **175 readings**, from the same 24
filings already resolved.

Can today's parser read them safely? Separated as the brief requires:

| Class | Companies | Readings | Note |
|---|---|---|---|
| **safe / current pipeline** | AAPL, ALL, CB, DIS, GS, JPM, MET, PG, TRV, TSLA | 85 | proven by BQ8 and BQ13; re-reads succeed |
| **vocabulary-blocked** | AXP, FITB, UNP, WMT, MTB | 40 | re-read succeeds, one factor still unanswerable |
| **vocabulary-repaired** | KO | 5 | BQ11 + BQ12 proved the re-read works |
| **structural refusal** | HON | 5 | **the reading is rejected whole** (BQ8 §4); re-read yields nothing |
| **extraction failure** | C | 5 | unresolved since BQ6 |
| **question-contract mismatch** | BCS, COF, DB, MUFG, NWG, RF | 35 | re-read succeeds and the band stays UNKNOWN |
| | **24** | **175** | |

**A bump cannot be treated as if all 24 regenerate.** HON is known to
refuse and C is known to fail — 10 readings that would be spent to
produce nothing — and 75 more belong to companies whose blocker is not
evidence at all.

## 5. Cost by strategy

Quorum 5, per statement. 35 statement-quorums across 24 companies.

| | **A — full rebuild** | **B — lazy rebuild** | **C — targeted** | **D — no bump** |
|---|---|---|---|---|
| companies affected | 24 | 24 eventually | **8** | 0 |
| readings immediately | **175** | 0, then on demand | **40** (8 income statements) | 0 |
| readings eventually | 175 | 175 | 40 | 0 |
| already paid in isolation | 20 | 20 | **20** (KO, ALL, TSLA, WMT) | 20 |
| **bands lost meanwhile** | **8** | **8** — the file is dead on bump, not on demand | **0** | 0 |
| observations destroyed | 175 | 175 | **40** | 0 |
| valid anchors destroyed | **325** | 325 | **0** | 0 |
| semantic cleanliness | mislabels a defect as a contract change | same, plus a corpus in two versions indefinitely | states exactly what is wrong with exactly those records | leaves incompatible evidence pooled |
| complexity | one constant | one constant | **new: a per-observation contract record** | — |
| risk of mixing | none — nothing survives | none | must be *measured* rather than asserted | **the live defect** |

**B is not cheaper than A in the way it looks.** The bump kills every
file at once; laziness only defers the *re-reading*, not the loss. The
eight bands go the moment the constant changes.

**C's residual honesty**: of its 40 readings, 20 are already paid (in
isolated stores), and of the remaining 20, **10 belong to HON and C and
are expected to fail**. So C's realistic new yield is MTB and RF —
neither of which gains a band, because both are question-contract cases.
**C buys correctness, not bands.** The bands come from the 20 already
spent.

## 6. Are schema-3 readings obsolete? — the falsification

Every stored anchor, in every reading, asked of today's parser: does this
exact cell still print this figure under this header, and does the row
still carry these cells?

**400 anchor-facts. VALID 325 · STALE 65 · INVALID 10.**

| Class | Count | Meaning |
|---|---|---|
| **VALID UNDER CURRENT CONTRACT** | **325 (81%)** | today's parse yields the identical anchor and the identical row |
| **STALE BUT NUMERICALLY CORRECT** | **65 (16%)** | the figure is the document's own; the header is the spanned title and the row holds one cell of three |
| **KNOWN INVALID** | **10 (3%)** | HON — the stored row index no longer names the row the reading read |
| **UNDETERMINED** | **0** | every statement and table was located |

By company:

| Class | Companies |
|---|---|
| **wholly valid** | AAPL, AXP, BCS, CB, COF, DB, DIS, FITB, GS, JPM, KO, MET, MUFG, NWG, PG, TRV, UNP — **17** |
| **mixed** | ALL, RF, WMT — **3** (income statement stale, balance sheet valid) |
| **wholly stale** | C, MTB, TSLA — **3** |
| **wholly invalid** | HON — **1** |

**And the partition is perfectly clean by statement:**

| Statement | VALID | STALE | INVALID |
|---|---|---|---|
| balance sheet | **26** | 0 | 0 |
| income statement | 39 | 13 | 2 |

Not one balance sheet is affected — they print bare years and never
carried a spanned title for the pre-fix `header_row` to mistake.

### The second axis: vocabulary

A stored *absence* is contract-dependent where the located statement
prints a figure-bearing row that today's `CONCEPT_LABELS` admits and the
producing set did not. Measured across all 24 companies, then checked for
figures — **which mattered**:

| Company | Row today's labels match | Carries figures? | Verdict |
|---|---|---|---|
| **KO** | `Net Operating Revenues` | **yes** — 47,941 / 47,061 / 45,754 under 2025/2024/2023 | **contract-dependent** — the label was added by BQ11 (`6c96ea0`) |
| AXP | `Revenues` | **no** — a bare section heading | absence is correct |
| C | `Revenues (1)` | **no** — a bare section heading | absence is correct |
| C | `Net income` | figures are `$ 7.11` under a header of `1,832.0` | **the known extraction failure**, not vocabulary |

**A label match alone is a false positive**, and two of the four were.
`6c96ea0` added exactly one label, so **KO is the only genuine vocabulary
case in the corpus.**

### Conclusion

**Schema 3 contains both fully valid and stale observations, and a global
bump is too coarse by a factor of five.** The contract did not change
uniformly — it did not change at all. What changed is the fidelity of the
parse on one table shape, and the accepted-label set for one label.

## 7. The supersession invariant

Smallest rule satisfying the brief:

> **An observation loses authority only where the immutable source,
> re-examined under the current contract, yields evidence that
> observation could not have produced — never because of the answer it
> supports.**

Two limbs, because two things can differ, and both are decided against
the document rather than against a preference:

1. **Parse supersession.** The stored anchor's own cell, re-parsed today,
   prints a different period header, or the row carries a different set
   of cells. *(Reaches ALL, C, MTB, RF, TSLA, WMT; HON fails the prior
   row-identity check and is superseded as invalid.)*
2. **Vocabulary supersession.** A stored absence, where the located
   statement prints a **figure-bearing** row whose label the current
   accepted-label set admits and the producing set did not. *(Reaches KO
   alone.)*

**It is answer-blind by construction** — neither limb can read a band, a
score, a verdict or a growth figure; both terminate in a comparison of
printed cells. The test that it is not result-driven is that it fires
identically for all four outcomes:

| Company | Superseded by | New band |
|---|---|---|
| ALL | limb 1 | **HIGH 80** — an improvement |
| TSLA | limb 1 | **LOW 40** — a demotion |
| WMT | limb 1 | **LOW 40** — a demotion |
| KO | limb 2 | **MEDIUM 62** — an improvement |

Two up, two down, one rule, no company named in it.

**Append-only survives.** Supersession removes *authority*, not the
record: the observation stays in the file, in order, and the consensus
excludes it with the reason worded. A superseded reading is still
readable, still dated, still attributable — which is what keeps
`EvidenceMovement` and the defect ledger honest about what this platform
once believed.

## 8. Funding ruling

# C — TARGETED SUPERSESSION

**Not A.** The observation contract did not change. Period identity was
in the contract from schema 1; the parse failed to honour it on one table
shape. Bumping would assert a contract change that did not happen,
destroy 325 provably-valid anchors to repair 65, and take eight live
bands to UNKNOWN for as long as the rebuild takes.

**Not B.** `_answer` is correct within a contract — proven, not asserted:
the header is a function of the cell, 0 of 16 cells vary. Repairing it
converts silent displacement into honest deadlock and delivers no band.
Worth doing eventually for the honesty; it is not this repair.

**Not E.** BQ13's wall is real and reproduced here for all three
companies, and KO's is now measured rather than inferred. Only BQ13's
*cause* was wrong, and §1 corrects it.

**Not D**, because the defect is live: incompatible evidence is pooled
today, and the platform currently reports a settled 10-of-10 agreement
between readings that disagree about what period a figure names.

### If the ruling stands, the exact terms

- **Old contract**: schema 3 as declared, produced by pre-`301cfdf` parse
  code — `header_row` takes a spanned title containing a digit as the
  header, so the data columns inherit the banner and the row yields one
  cell.
- **New contract**: schema 3 as declared, produced by post-`301cfdf`
  parse code, plus `CONCEPT_LABELS` as of `6c96ea0`.
- **Why they cannot coexist**: not because they assert different things,
  but because they assert the same thing at different fidelities, and
  `_answer` cannot see the difference — so the weaker reading wins by
  being older.
- **Immediate companies**: **8** — ALL, C, HON, KO, MTB, RF, TSLA, WMT,
  income statement only. 40 readings, of which **20 are already paid**
  (KO in `/tmp/bq11`, ALL/TSLA/WMT in `/tmp/bq13`) and **10 are expected
  to fail** (HON refuses, C's extraction is broken).
- **Total eventual cost**: 40 readings, against 175 for a bump.
- **Is lazy rebuilding semantically safe?** Under C, yes — and it is the
  only strategy where it is. Superseding a *specific* record leaves the
  other 325 authoritative, so a company not yet re-read keeps its correct
  band rather than losing it. Under A or B laziness is unsafe, because
  the evidence is gone the moment the constant moves.

## 9. Recorded and not solved

- **The version does not record the code that produced the record.** That
  is the root cause, and it will recur: any future defect repair to the
  parse will again leave two fidelities sharing one version. A contract
  fingerprint on the observation is the general fix; this slice proposes
  it only as far as supersession needs.
- **`_answer`'s blindness to the period is a real, separate weakness.**
  It costs nothing today once contracts stop mixing, and it should not be
  repaired *as* this fix, because doing so would hide the provenance
  problem behind a comparison change.
- **Whether isolated observations may be promoted at all** is untouched
  here. BQ12's and BQ13's twenty readings were produced under the current
  contract and are contract-valid; whether an observation acquired outside
  `data/` may enter it is a provenance question this report does not
  answer.
- **The isolated artifacts are ephemeral.** `/tmp/bq11` and `/tmp/bq13`
  survive today; `/tmp/bq12` is already gone. Twenty paid readings depend
  on a directory `/tmp` may clear.

## 10. The smallest implementation slice, if the ruling is C

Constrained by one existing rule: **a page view never fetches**, so the
classification in §6 cannot run at read time. The contract must be
*recorded*, then compared.

1. **A `superseded_because: str | None` field on the stored
   observation**, defaulted on decode exactly as `located_among` was —
   *"an entry written before the field existed records nothing, which
   reads as 'not superseded' rather than as a claim."* **No version bump**,
   because adding a defaulted field changes neither what a reading is
   shown nor what it is asked. The store's own precedent, applied again.
2. **One offline audit command** — free, no model, no fetch beyond the
   filings already resolved — that runs §6's two limbs and writes the
   marker. This is the only place a document is re-parsed, and it is
   operator-invoked, never behind a surface.
3. **`statement_consensus_of` excludes superseded observations** and
   words the exclusion in the consensus's own voice, so a reader sees
   *five readings of one filing, four earlier ones superseded* rather
   than a silently smaller count.

Nothing else moves: `_answer`, `_settled`, quorum, Business Quality,
thresholds, vocabulary and the schema constant all stay as they are.

## Scope compliance

`STATEMENT_SCHEMA_VERSION` unchanged · `_answer` and `_settled` unchanged
· consensus and quorum unchanged · nothing re-observed · **no credit
spent** · no isolated observation copied into production · Business
Quality, vocabulary, HON, Citigroup and financial-company question
semantics untouched · no UI, no crypto, no PR #145 · production `data/`
byte-identical, `git status --porcelain data/` empty · the schema-bump
effect was measured on a temporary copy and never on the corpus · this
change is one document.
