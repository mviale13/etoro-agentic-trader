# One label of three, and a band that works but cannot land

**Status: built and measured, BQ19. Production promotion executed; one
vocabulary form accepted and two rejected on evidence; five paid
readings spent on UNP alone. Stopped for review.**

Two gates, both crossed, and the second produced a result the brief's
kill criterion is worth reading carefully against.

> **The lexical remedy works completely.** On its five fresh readings
> alone, Union Pacific answers **3 of 3** factors and bands **MEDIUM
> 62** — exactly BQ18's prediction.
>
> **It does not land in production, and not because of the remedy.**
> Appended beside the five stale readings that recorded *"no figure
> located"*, the consensus is **5 against 5** — `by_majority=False`,
> unsettled, UNKNOWN. That is KO's tie, arriving at a second company.
>
> **Two of the three candidate forms were rejected**, one by an existing
> ruling this slice found no evidence to overturn, and one by a
> collision the sweep discovered.

---

## 1. Phase 0 — the production promotion

The three idempotent commands, unmodified, no observation chosen by
hand:

| Run | Appended | Refused |
|---|---|---|
| bq13 | 15 (ALL, TSLA, WMT ×5) | — |
| bq11 | 5 (KO) | — |
| bq8 | 2 (ALL, TSLA) | **1 — KO, by the rule itself** |

bq8's KO reading was refused with its own words: *"the manifest records
no figure for total_revenue under a vocabulary that differs from
today's."* **22 appended · 0 compatibility-unproven · 0 unrelated
companies moved.**

| | before | after |
|---|---|---|
| HIGH | 3 | **4** — + ALL |
| MEDIUM | 4 | 4 |
| LOW | 1 | **3** — + TSLA, WMT |
| UNKNOWN | 16 | **13** |

Exactly the expected state.

## 2. Phase A.1 — the arithmetic

Every candidate reconciles to the filer's own printed components. The
arithmetic is reported in full because for one of them **the
reconciliation is itself the refusal**:

| Company | Label | Reconciliation |
|---|---|---|
| **UNP** | `Total operating revenues` | 23,220 + 1,290 = **24,510 exact** — an addition of two revenue components |
| AXP | `Total revenues net of interest expense` | 54,865 + 25,598 **− 8,234** = **72,229 exact** |
| C | `Total revenues, net of interest expense (1)` | 25,433 + 59,792 = **85,225 exact** (59,792 is itself interest income *less* interest expense) |
| BCS | `Total income` | 14,501 + 7,498 + 7,042 + 10 + 89 = **29,140 exact** |
| NWG | `Total income` | 25,698 − 12,869 + 3,247 − 733 + 1,112 + 186 = **16,641 exact** |

**AXP and C are one form, not two.** A footnote marker and a comma are
typography, so both normalise to `totalrevenuesnetofinterestexpense`.
Three distinct forms went to the sweep, not five.

## 3. Phase A.2 — the falsification sweep

All 24 companies, all three statements, every occurrence of every
proposed form.

**Collision with an existing concept**: none of the three forms is owned
by any other concept today.

| Form | Occurrences | Where |
|---|---|---|
| `total operating revenues` | **1** | UNP income statement, 24,510 |
| `total revenues net of interest expense` | 2 | AXP 72,229; C 85,225 — both income statements, both the intended line |
| `total income` | **3** | BCS 29,140; NWG 16,641; **MTB — cash-flow region, table 73, 2,916** |

**Near misses**, all excluded by the equality rule rather than by luck:
AXP's `Total revenues net of interest expense after provisions for
credit losses` 66,973, and MTB's `Total income taxes` — different
strings, therefore different labels. This is the containment rule BQ11
relied on, working.

### The refutation the sweep found

MTB's third occurrence is in a table captioned **`Condensed Statement of
Income`** — the parent-company-only statement a US bank holding company
files. Its rows:

```text
Dividends from consolidated subsidiaries   $ 2,776
Interest income                                116
Income from BLG                                 20
Other                                            4
Total income                                 2,916
```

That is **the parent alone, dominated by dividends from its own
subsidiaries**, against consolidated interest income of 10,486. The
exact phrase already denotes a non-consolidated aggregate *inside this
corpus*, in a table titled a statement of income — and only the
concept-to-statement partition keeps the two apart today, which is a
boundary rather than a property of the label.

**`total income` rejected.** BCS and NWG are not addressed by this
slice.

### The refutation the test suite found

Widening for `total revenues net of interest expense` failed
`test_a_revenue_net_of_an_expense_is_not_the_top_line`, an **existing
BQ11 ruling** naming AXP and Citigroup exactly:

> *"AXP and Citigroup print revenue after deducting interest. A
> different economic quantity from consolidated total revenue, and
> refused for that reason rather than for its wording."*

The ruling is right, and my own arithmetic proof above contains the
evidence for it: `− 8,234` is an expense subtraction, so the line is a
net figure and not a gross top line. **`total revenues net of interest
expense` rejected.** AXP and C are not addressed by this slice.

**Recorded, not resolved**: Goldman Sachs's accepted `Total net
revenues` is built the same way — non-interest revenues plus *net*
interest income — so the vocabulary is arguably inconsistent between GS
and AXP today. That inconsistency is real and it is not a vocabulary
widening's business to settle; it belongs to whichever slice argues
BQ11's ruling.

## 4. Forms accepted and rejected

| Form | Verdict | Ground |
|---|---|---|
| `total operating revenues` | **ACCEPTED** | 1 corpus occurrence; pure addition of revenue components; no collision |
| `total revenues net of interest expense` | **REJECTED** | an existing argued ruling, corroborated by its own arithmetic |
| `total income` | **REJECTED** | denotes a parent-only aggregate elsewhere in this corpus |

One of three. The five candidate companies reduce to **one**, which is
the minimum paid experiment the brief specifies — the falsification
narrowed the slice rather than confirming it.

## 5. Fingerprint

| | |
|---|---|
| old `TOTAL_REVENUE` | `3cdbddd6a1fcf0e6` |
| new `TOTAL_REVENUE` | `ea9df9c5adbc7f44` |
| delta | **+1 form** — `total operating revenues`; 13 → 14 accepted forms |

Every other concept's fingerprint is unchanged (`net_income`
`c5983f89b332a0c7`, `gross_profit` `36b11e47cf234c1f`, …).

## 6. Nothing was rewritten, and no old absence became readable

Measured immediately after the widening and before any acquisition:

- corpus bands **HIGH 4 · MEDIUM 4 · LOW 3 · UNKNOWN 13** — unchanged;
- `git status --porcelain data/` empty;
- existing observations carrying a producing stamp: **0** — every
  pre-BQ17 record still records nothing, and none was backfilled.

UNP's five stale readings still say *"no figure located"* under the
narrower vocabulary, which is true and remains true. **This is BQ17
working exactly as designed**, and it is also why the band does not
land — see §9.

## 7. The paid gate

**Reached.** UNP's form passed the sweep with one corpus occurrence and
no unresolved collision, which is the gate the brief set.

## 8. UNP ×5 — extraction and provenance

Five readings, `gpt-5`, isolated evidence root, one taken and validated
before the other four were launched, with a guard aborting on any
divergence from reading 1.

| | |
|---|---|
| located the intended consolidated total | **5 of 5** — `Total operating revenues` 24,510 at table 0 row 4 |
| divergence across readings | **none** — labels, cells, printed values and full rows byte-identical |
| dated cells | **3 each** — 2025 24,510 · 2024 24,250 · 2023 24,119 |
| also located | `Operating income` 9,846 and `Net income` $7,138, 3 dated cells each |
| internal consistency | 23,220 + 1,290 = **24,510**, the printed total |

**Native provenance stamped, and it is the new contract:**

```text
total_revenue        ea9df9c5adbc7f44   matches live = True
gross_profit         36b11e47cf234c1f   matches live = True
operating_income     668db132db8b57bd   matches live = True
net_income           c5983f89b332a0c7   matches live = True
```

**BQ17's payoff, demonstrated**: the importer rules all five
`compatible` **with no manifest authored** — the first evidence in this
platform's history that promotes on its own testimony.

## 9. UNP before → after

| | readings | answered | band |
|---|---|---|---|
| **stale only** (production today) | 5 | 1 of 3 | **UNKNOWN** |
| **fresh only** | 5 | **3 of 3** | **MEDIUM 62** |
| **mixed** — what production would become | 10 | 1 of 3 | **UNKNOWN** |

Fresh-only, in full: profitability **excellent** (operating margin 40.2%,
net margin 29.1%), revenue growth **weak** (+1.07%), earnings growth
**moderate** (+5.80%) — 1 favourable of 3 → 33% → MEDIUM → 62.

**Mixed is a tie**: five readings answer *no figure located* and five
answer `"Total operating revenues" = 24,510`, so `by_majority` is
`False` and the claim is unsettled. Every margin loses its denominator
and UNP stays at one answered factor.

### The kill criterion, read exactly

> *"If UNP does not band across the five fresh readings for reasons
> attributable to the proposed lexical remedy, stop."*

**It does band across the five fresh readings**, and the reason it does
not band in a mixed store is not attributable to the remedy: it is the
stale-absence tie BQ14 named when it declined vocabulary supersession
and BQ16 measured on KO. The remedy is validated; a second, already-known
blocker sits behind it.

### The BQ18 assumption that was false

BQ18 classified UNP as *"fresh observation necessary but not sufficient
— needs vocabulary first"* and predicted vocabulary + fresh reading =
band. The missing term: **a stale absence does not merely fail to help,
it votes.** BQ18 identified exactly that mechanism for KO and filed it
as its own class (T) rather than recognising it as a property of every
class-V company — whose stale readings record the same kind of absence
for the same reason. UNP and KO are one condition, not two.

## 10. API and model usage

**Five readings, `gpt-5`, UNP only.** No other company observed, and
none of AXP, C, BCS or NWG re-observed. Every reading went to an
isolated evidence root; the five are preserved at
`data/experiments/statement-observations/bq19/statements/`, md5
`19d1fa207ed5ad000dfcf8a736a9f566`, byte-identical to the originals.

**Production was not given them.** Appending would create the 5-against-5
tie above — analytically UNKNOWN either way, but it would bake a
deadlock into the corpus before the supersession question is ruled. They
wait, and they need no manifest to move when it is.

## 11. Gates and production impact

| Gate | Result |
|---|---|
| `pytest` | **2,794 pass** |
| `ruff check` | clean |
| `ruff format --check` | 992 files clean |
| `mypy app` | clean, 591 files |

Four existing tests changed, all in `test_statement_gap_truthfulness.py`
and all because they used `Total operating revenues` as a specimen of a
*refused* label. The downgrade specimen moved to MTB's `Mortgage banking
revenues`; the content pin gained the one earned label; and BQ11's
count assertion became a statement about *how* each form was earned
rather than how many there are — with a new assertion that
`Operating revenues:`, the bare heading UNP prints above its
components, is still refused. **No assertion was weakened and
`test_a_revenue_net_of_an_expense_is_not_the_top_line` was left exactly
as BQ11 wrote it.**

Production data: the promotion of §1 is the only write. Nothing else in
`data/statements` moved.

## Recorded, not solved

- **The tie is now two companies** — KO and UNP — and will be every
  class-V company that follows. It is BQ14's declined vocabulary-
  supersession limb, and it is now the single highest-leverage open
  question in this arc.
- **The GS/AXP inconsistency** in what counts as a top line.
- **BCS, NWG, AXP, C** are not addressed and were not re-observed.
- **HON's parser, KO's tie semantics, the six companies with no printed
  consolidated line, other concepts, playbook logic and quality
  thresholds** — all untouched, as instructed.

## Scope compliance

Vocabulary widened by exactly one form, each candidate ruled
independently · no threshold, quality rule, playbook or UI change · no
company re-observed but UNP · five readings, the authorised minimum ·
BQ16/BQ17 logic unmodified · no existing observation or provenance
rewritten · the KO refusal in §1 produced by the rule, not by hand.
