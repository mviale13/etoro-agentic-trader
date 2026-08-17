# The quantity gets its name, and two of three filers cannot be read for it

**Status: built offline, validated paid, and stopped short of the
escalation criterion. BQ24. The offline gate passed in full. The paid gate
produced 1 clean observation of 3, and the failure is structural rather
than stochastic, so no further readings were bought. `data/statements`
byte-identical. Stopped for ruling.**

> **`REVENUE_NET_OF_INTEREST_EXPENSE` is named, contracted, stamped and
> proved offline against all three specimens and every control** — the
> eleven gross top lines, and M&T's parent-company `Total income`, which
> now fails on the *evidence* rather than on the boundary BQ19 had to
> lean on.
>
> **American Express reads cleanly on the first attempt.** One reading,
> `gpt-5`: `Total revenues net of interest expense` 72,229 at t0 r17 c3,
> its own `Net interest income` 17,364 at t0 r16 c3 immediately above it,
> `total_revenue` absent, native fingerprint `3e077c247f109a37` stamped,
> importer rules it compatible with no manifest.
>
> **Goldman and JPMorgan cannot be read for it at all, and the reason is
> the harness rather than the concept.** Their label is in *both*
> vocabularies, one cell may answer only one concept, and the reading
> cited row 12 for both — so the extractor rejected the **whole
> observation**, losing net income and net interest income with it.
>
> **The escalation criterion is not met. No consensus acquisition is
> recommended.** More readings cannot help: the collision is deterministic
> in cause, and a lucky reading would only make a five-reading quorum fail
> intermittently instead of always.

---

## 1. The concept

**`StatementConcept.REVENUE_NET_OF_INTEREST_EXPENSE`**, value
`revenue_net_of_interest_expense`. The brief's preferred name, adopted
unchanged — repository convention is a SCREAMING_SNAKE noun phrase and it
fits without compromise.

> A filer-reported **consolidated** top-line revenue or income measure
> that **includes net interest income** — therefore already deducting
> interest expense — together with non-interest revenue or income.

The name refuses the abbreviation deliberately. `NET_REVENUE` would
collide with the other `net`: `Net sales`, `NET SALES` and `Net Operating
Revenues` are net of **returns, discounts and excise taxes**, a revenue
adjustment rather than an expense, and **three of the eleven gross top
lines this platform establishes carry the word**. A test pins that
`net_revenue` does not appear in the value and `interest_expense` does.

**The invariant, and the three things it is not.** It is not any row
containing *net*; not any financial company's top line; not any total
below an interest-related row. The positive evidence is the
`NET_INTEREST_INCOME` relationship BQ22 measured and BQ23 built, and
`financing_cost_refusal` now expresses both readings of it:

```text
GOVERNED = {
    TOTAL_REVENUE:                    (NET_INTEREST_INCOME, ABSENT_ABOVE),
    REVENUE_NET_OF_INTEREST_EXPENSE:  (NET_INTEREST_INCOME, PRESENT_ABOVE),
}
```

**One predicate read with opposite polarity.** The same subtotal that
disproves a gross top line is what establishes a net-of-financing one, so
a statement cannot support both readings of one row and cannot support
neither. A candidate with no marker above it is refused
`FINANCING_COST_NOT_EVIDENCED`; a gross total with one is refused
`NET_OF_FINANCING_COST`, exactly as BQ23 left it.

---

## 2. The corpus falsification table

Every table of every located income statement, scanned for a candidate
label and tested against the structural qualification. Free SEC re-reads,
no model.

| | printed label | altitude | `NET_INTEREST_INCOME` located | non-interest component | reconciliation | qualifies |
|---|---|---|---|---|---|---|
| **GS** | `Total net revenues` 58,283 (t0 r12) | consolidated, statement face | **r11** 13,559 | `Total non-interest revenues` 44,724 | 44,724 + 13,559 = **58,283 EXACT** | **YES** |
| **JPM** | `Total net revenue` 182,447 (t0 r15) | consolidated, statement face | **r14** 95,443 | `Noninterest revenue` 87,004 | 87,004 + 95,443 = **182,447 EXACT** | **YES** |
| **AXP** | `Total revenues net of interest expense` 72,229 (t0 r17) | consolidated, statement face | **r16** 17,364 | `Total non-interest revenues` 54,865 | 54,865 + 17,364 = **72,229 EXACT** | **YES** |
| **BCS** | `Total income` 29,140 (t0 r12) | consolidated, statement face | **r4** 14,501 | none this platform reads | unavailable | **YES** (structure only) |
| **NWG** | `Total income` 16,641 (t0 r11) | consolidated, statement face | **r5** 12,829 | none this platform reads | unavailable | **YES** (structure only) |
| **COF** | — no candidate label in any located table | — | r13 42,878 | `Total non-interest income` 10,556 | — | **no candidate** |
| **FITB** | — no candidate label in any located table | — | r11 5,982 | `Total noninterest income` 3,035 | — | **no candidate** |
| **MTB** | `Total income` 2,916 — **cash-flow section, t73**, caption *Condensed Statement of Income* | **parent company alone** | **none above it in that table** | `Dividends from consolidated subsidiaries` | — | **NO** |

**The falsification attempt that mattered, and it succeeded twice over.**
BQ19 refused `total income` as a `TOTAL_REVENUE` form because of M&T, and
said in the same breath that *"only the concept-to-statement partition
keeps the two apart today, and that is a boundary rather than a property
of the label."* Measured in M&T's own filing, the parent-company table
prints **no net interest income above the line at all**, so the candidate
fails the structural gate wherever it sits. The boundary is no longer
load-bearing.

**Identical wording was not treated as sufficient**, and the measurement
proves it: three filers print three different labels for one quantity, and
one label names two different quantities across two filers. Neither
direction is recoverable from words.

**One methodological finding worth keeping.** The first sweep reported NWG
as *not qualifying*, wrongly. Its net interest row carries an extra
leading cell, so matching the marker to the candidate **by position**
compared two different years. Matching by **column header** fixed it. A
figure's period is the header above it, never its index — the same lesson
DB's `Notes` column taught BQ21.

---

## 3. Positive and negative controls

| control | result |
|---|---|
| GS, JPM, AXP specimens, from held evidence | **qualify**, all three, with exact reconciliation |
| **every accepted form with no marker** | **refused**, all five — a label alone never establishes the concept |
| the eleven gross top lines | **excluded twice**: not one label is an accepted form, *and* not one statement establishes a marker |
| `Total net sales`, `Net sales`, `NET SALES` | **not reachable** — the concept is not addressable by wording |
| M&T parent-company `Total income` | **refused** — `FINANCING_COST_NOT_EVIDENCED` |
| a marker established in **another table** offered for the parent figure | **still refused** — one table is one scale |
| a **component** offered as the total (`Total non-interest revenues` at r8, marker at r11) | **refused** — the marker does not precede it |
| BQ23 still refuses GS and JPM as `TOTAL_REVENUE` | **yes**, `NET_OF_FINANCING_COST`, unchanged |
| AXP's settled `TOTAL_REVENUE` absence | **unchanged**, `refused=None`, 5 of 5 |
| the two concepts are not aliases | distinct members, distinct vocabularies, distinct fingerprints; two forms shared, and a shared form is not an alias because the structural requirement is **opposite** |

---

## 4. The extraction mechanism, and where it broke

**Lexical candidate at extraction; structural qualification on read.** The
reading is asked for the concept by a question naming the relationship,
and may cite only a row whose label is an accepted form. The
*qualification* is then derived on every read from the cells the
observation already stores — the candidate's and the marker's — so it
stays checkable forever and no interpretation is baked into a stored byte.
That is the same seam BQ23 uses, read the other way.

**The disambiguation is carried entirely by the new concept's question**,
which no earlier reading was ever asked:

> *"…where that total **includes net interest income** — that is, a top
> line struck after interest expense has already been deducted… **This
> concept, and not total revenue, answers such a total.** Not a gross
> revenue line struck before any financing cost; not a component…; not a
> subtotal struck after a provision for credit losses; and not a total of
> a parent company alone…"*

`CONCEPT_QUESTIONS[TOTAL_REVENUE]` is **byte-identical**. That was not a
preference: the fingerprint covers labels only, and what a reading is
*asked* is tracked by the schema version — so editing the old question
would have demanded a schema bump, and BQ14 measured that a bump wipes 24
companies and every live band.

### Where it broke, and it is the harness

`FinancialStatementExtractor` enforces **one cell, one concept**: a second
concept citing an already-cited cell raises, and the **whole observation**
is rejected. GS's `Total net revenues` and JPM's `Total net revenue` are
in *both* vocabularies, so the reading cited one row for two concepts and
lost everything:

```text
GS  : NO OBSERVATION — The figure for 'revenue_net_of_interest_expense'
      cites a cell already read as another concept…
JPM : NO OBSERVATION — (identical)
AXP : clean
```

**AXP is the control that isolates the cause.** Its label is in the new
vocabulary and *not* in `TOTAL_REVENUE`'s, so no collision is possible —
and it read correctly on the first attempt. **The concept extracts where
its vocabulary is disjoint and cannot be extracted where it overlaps.**

Per §5 of the brief, this is the point at which to report rather than
weaken the concept, and the concept was not weakened.

---

## 5. Relationship with BQ23 and `TOTAL_REVENUE`

Three states of one physical row, all live simultaneously and none an
alias of another:

| | GS row 12 |
|---|---|
| **historically extracted** as | `total_revenue`, under a contract that accepted the label — still stored, still saying so |
| **analytically refused** for | `total_revenue`, by BQ23's structural rule, derived on read |
| **prospectively extractable** as | `revenue_net_of_interest_expense`, under the new producing contract |

BQ23 remains authoritative and untouched: a fact establishing the new
concept is still refused as `TOTAL_REVENUE` when the predicate fires, and
the corpus proves it — GS and JPM still carry
`NET_OF_FINANCING_COST` refusals with their figures and reasons intact.

---

## 6. Provenance

| | |
|---|---|
| **new producing fingerprint** | **`3e077c247f109a37`** |
| `total_revenue` | **`ea9df9c5adbc7f44`**, unchanged, all 14 forms |
| `net_interest_income` | `8c3e67f9872329b5`, unchanged |
| every other concept | unchanged (`gross_profit` `36b11e47cf234c1f`, `net_income` `c5983f89b332a0c7`, …) |
| store schema | **3, unbumped** |
| `vocabulary_contracts.PUBLISHED` | **not extended** — the new concept has no lineage, `registry_is_current` returns `False`, and its absences therefore keep voting, which is the safe direction |
| stamped natively | **yes** — `producing_contract` iterates `concepts_of`, so the fresh AXP reading carries `revenue_net_of_interest_expense → 3e077c247f109a37` with **no manifest**, and the importer rules it `compatible=1` |

**No backfill, and none possible.** Not one stored observation carries the
concept — asserted per company, per statement, over both the consensus
facts and the raw readings, including `produced_under`. `_addressed` reads
concepts from the observations rather than from the live vocabulary,
*"because a stored reading may predate a concept the vocabulary gained
since"*: the architecture was built for this.

**No schema bump, proved rather than argued.** A consensus over five
readings that know the concept and five that do not settles every shared
claim identically — same anchor, same row, same refusal, same modal
answer — with the reading count rising from 5 to 10, which is what pooling
means. The new concept appears only because half the readings were asked.

---

## 7. Consumed by nothing

Named and acquirable, and analytically inert. Guarded four ways:

- absent from every entry in `RECIPES`;
- absent by source scan from `business_quality`, `financial_question`,
  `financial_understanding`, `financial_questions`,
  `business_quality_service` and `profitability_analyst`;
- an **AST walk over every module in `app/`** asserts no addition anywhere
  sums a net-interest term — the synthetic gross revenue a bank
  profitability factor would need is computed nowhere;
- production bands are **exactly what BQ23 left them: HIGH 3 · MEDIUM 4 ·
  LOW 3 · UNKNOWN 14**.

`FinancialModel.BANK` is not activated, no threshold is added, and GS and
JPM do not band again.

---

## 8. The offline gate — passed

| # | requirement | result |
|---|---|---|
| 1 | GS specimen qualifies | **yes**, exact |
| 2 | JPM specimen qualifies | **yes**, exact |
| 3 | AXP specimen qualifies | **yes**, exact |
| 4 | industrial `Net sales` controls do not qualify | **11 of 11 excluded**, twice each |
| 5 | M&T parent-company `Total income` does not qualify | **refused on the evidence** |
| 6 | BQ23 still refuses the three as `TOTAL_REVENUE` | **yes** |
| 7 | no production observation rewritten | **`data/statements` md5 `5b5b1d1d…` before and after** |
| 8 | all tests and gates pass | **2,845 pass**, ruff and mypy clean |

All three specimens are representable under one concept, so the gate did
not stop the slice.

---

## 9. The paid validation — 1 of 3, and the failure is structural

**Three calls, `gpt-5`, one reading each, income statement only.**
Isolated three ways before the first call: `MOVRVEST_EVIDENCE_ROOT` at a
temp directory set *before any app import*, the store passed explicitly,
and the resolved path asserted not to be production and to be inside the
isolated root.

### AXP — clean, every check met

```text
revenue_net_of_interest_expense  'Total revenues net of interest expense' = 72,229
                                 at table 0, row 17, column 3
net_interest_income              'Net interest income' = 17,364
                                 at table 0, row 16, column 3
total_revenue                    absent
net_income                       'Net income' = $ 10,833
produced_under[revenue_net_of_interest_expense] = 3e077c247f109a37
produced_under[total_revenue]                   = ea9df9c5adbc7f44
```

| check | result |
|---|---|
| intended consolidated row located | **yes**, r17, the statement face |
| new concept established | **yes** |
| exact printed figure | **72,229** |
| structural relationship | **holds** — marker r16 precedes r17, same table, same column |
| native fingerprint stamped | **`3e077c247f109a37`** |
| `TOTAL_REVENUE` remains refused | **yes** — absent, and its label is not an accepted form |
| generic profitability restored | **no** — no band, no margin |
| importer | **`compatible=1`, no manifest** |

### GS and JPM — rejected whole

Both readings cited one row for two concepts. The extractor's
one-cell-one-concept rule rejected the entire observation, so **nothing
was stored, including the net income and net interest income the same
reading had found.**

**This is not a retry candidate.** The cause is deterministic — the label
is in two vocabularies and the platform offers no way for a reading to say
*this row is the second concept, not the first* — and the model's choice
is the only stochastic part. A reading that happened to file it under one
concept would make a five-reading quorum fail *intermittently* rather than
always, which is worse than failing cleanly. So no further calls were
bought.

**Escalation criterion, read exactly:** *"Only if all three one-shot
observations succeed cleanly may you recommend whether a 5-reading
consensus acquisition is warranted."* One succeeded. **No consensus
acquisition is recommended.**

---

## 10. API and model usage

| | |
|---|---|
| calls | **3** — GS, JPM, AXP, one each, `gpt-5`, income statement only |
| produced an observation | **1** (AXP); 2 rejected before anything was written |
| other companies observed | **none** |
| free SEC re-reads | GS, JPM, AXP, BCS, NWG, COF, FITB, MTB — deterministic, no model |
| preserved at | `data/experiments/statement-observations/bq24/statements/`, md5 `59b041df104076e8830ae275a8261cdf` |
| production write | **none.** `data/statements` md5 `5b5b1d1d57787769c4ddee8af7a21ad5` before and after |

The specimen is preserved for review and **not appended**, per §10.

---

## 11. Impact on quality bands

**None, as expected**, and asserted rather than assumed: the corpus tally
is pinned at **HIGH 3 · MEDIUM 4 · LOW 3 · UNKNOWN 14**, unchanged from
BQ23.

## 12. Gates

| | |
|---|---|
| `pytest` | **2,845 pass** (2,827 before, +18) |
| `ruff check` / `ruff format` | clean, 1,003 files |
| `mypy app` | clean, 594 files |
| `git status --porcelain data/statements` | **empty** |

Two existing tests were corrected rather than weakened. The
producing-contract stamp test asserted a *snapshot* of the income-statement
vocabulary and now derives it from `concepts_of`, which is what it was
always trying to guarantee. And BQ23's no-company scan matched substrings,
so it found **`GS` inside the identifier `STANDINGS`**; it now matches on
word boundaries — the same false-positive shape that once let a ticker
corroborate itself on the letters *etf*.

---

## 13. Recommendation

**Do not proceed to consensus acquisition.** The concept is sound and its
offline proof is complete, but two of the three filers cannot be read for
it at all, and a quorum over an intermittently-rejecting extraction would
buy noise.

**One slice first: resolve the vocabulary overlap between
`TOTAL_REVENUE` and `REVENUE_NET_OF_INTEREST_EXPENSE`.** Two candidate
routes, both offline to decide:

- **Narrow `TOTAL_REVENUE`'s vocabulary** by the two shared forms
  (`total net revenue`, `total net revenues`). BQ22 declined deleting the
  *four* `net` forms because bare `Net revenues` may be an industrial's
  gross top line — an argument that does not reach these two, which no
  company in this corpus prints as a gross total. It is a real contract
  change: `TOTAL_REVENUE`'s fingerprint moves and
  `vocabulary_contracts.PUBLISHED` must be extended in the same commit, or
  absence supersession silently stops working.
- **Let the structure resolve the collision in the extractor.** The
  platform already knows which of the two concepts a cell belongs to; the
  distinctness check currently resolves a contested cell by enum order,
  which is arbitrary. Making it resolve by *which concept's structural
  requirement the cell satisfies* changes no vocabulary and no
  fingerprint, and would let one reading answer both concepts correctly.

The second is more principled and touches no contract; the first is
smaller and better precedented. Both need a ruling, and neither needs a
paid call to decide.

**Then, and only then, the three-filer consensus.** With the collision
gone, the natural scope is one reading each for GS and JPM to confirm the
fix, before any quorum is funded.

## Recorded, not solved

- **A rejected reading loses every concept it found**, not only the
  contested one. GS's net income and net interest income were located
  correctly and thrown away with the collision. Whether a partial
  observation should be storable is a separate question, and a real one.
- **`CONCEPT_WORDS` has no entry for the new concept.** That table exists
  to weaken an absence into *"this platform cannot tell"*, and nothing
  reasons from this concept's absence yet. Add it when something does.
- **BCS and NWG qualify structurally with no reconcilable component.**
  Neither prints a non-interest subtotal this platform reads, so their
  totals would be established on the marker relationship alone — weaker
  evidence than the three specimens, and worth a separate ruling before
  either is acquired.
- **The new concept has no published lineage**, so BQ20's absence
  supersession will never rule on it. Correct today, and the first time
  its vocabulary widens, `vocabulary_contracts` must gain its era in the
  same commit.

## Scope compliance

No vocabulary of any existing concept edited · no schema bump · no
production observation appended or rewritten · `FinancialModel.BANK` not
activated · no bank profitability factor · no net-margin denominator
changed · **`NII + noninterest income` computed nowhere in `app/`** ·
COF/FITB not repaired · DB/MUFG not fixed · HON untouched · KO not
re-read · BQ23's refusal unchanged · 3 model calls, the authorised scope,
one company each.
