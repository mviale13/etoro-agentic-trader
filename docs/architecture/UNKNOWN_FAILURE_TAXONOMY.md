# Thirteen UNKNOWNs, six causes, and one quantity that six of them print

**Status: research, BQ19. Read-only over held evidence plus free
deterministic re-reads of filings the resolver already names. No model
call, no new observation, no production write, no rule, threshold,
vocabulary or parser change. Stopped for ruling.**

The question was whether several of the remaining thirteen share one
failure boundary. They do — and the shared boundary is not where the
brief expected it.

> **Six of the thirteen print a consolidated top line this platform
> already reads, already names, and no measure consumes.** AXP, BCS, C,
> GS, JPM and NWG each print a revenue net of interest expense;
> `statement-shape` locates it in all six under today's vocabulary, and
> `REVENUE_NET_OF_INTEREST_EXPENSE` appears in no recipe by BQ24's
> explicit design. **Three of them — AXP, GS and JPM — hold it as
> established consensus right now**, with dated net income beside it, so
> the evidence for a full three-factor assessment is already in the
> store.
>
> **And giving it a consumer re-creates the defect BQ22 removed.**
> Measured in memory over the same held consensus: GS → **HIGH 80,
> profitability `excellent`**, JPM → **MEDIUM 62, `excellent`**, AXP →
> **MEDIUM 62, `strong`**. Two of the three land on the corpus's top
> verdict word on a denominator that excludes a bank's largest cost,
> beside Procter & Gamble's `strong`. **This is a semantic ruling, not a
> repair.**
>
> **Paid re-observation of the three companies that are ready for it
> yields zero bands.** C, MTB and RF hold no authoritative income
> consensus — the HON defect exactly, and confirmed to be the same
> defect — but their filers print no consolidated total at all, so
> fifteen fresh readings move them from `0 of 3` to `1 of 3` and leave
> all three UNKNOWN.
>
> **A latent propagation hole: total withdrawal re-opens the provider
> proxy.** `_quality_value` protects a grounded UNKNOWN outright, but C
> and MTB produce no grounded object at all, and there a provider
> recommendation scores them. Not live — neither holds a provider row —
> and armed by any `movrvest acquire` that adds one.

---

## 1. The population — all thirteen, and the two controls that moved

Production today, derived through the platform's own path
(`FinancialStatementService.established` → `financial_engine.measure` →
`business_quality_service.quality_of`):

```
HIGH 3 — ALL, DIS, TRV
MEDIUM 5 — AAPL, CB, HON, PG, UNP
LOW 3 — MET, TSLA, WMT
UNKNOWN 13 — AXP, BCS, C, COF, DB, FITB, GS, JPM, KO, MTB, MUFG, NWG, RF
```

**The brief's control set contains one stale expectation, and it is not
drift.** GS is named as an established HIGH control; **GS is UNKNOWN**,
and has been since BQ23 (#172) refused its top line as a total struck
after financing cost — the brief's own §F condition, already applied.
JPM went MEDIUM → UNKNOWN in the same ruling. Both are correctly
UNKNOWN and neither should be restored to a control.

| control | expected | observed | verdict |
|---|---|---|---|
| HON | MEDIUM 62, 3/3 | **MEDIUM 62, 3/3** | holds |
| AAPL | MEDIUM 62 | **MEDIUM 62**, 3/3 | holds |
| UNP | MEDIUM 62 | **MEDIUM 62**, 3/3 | holds |
| DIS | HIGH | **HIGH 80**, 3/3 | holds |
| GS | HIGH | **UNKNOWN, 1/3** | **stale expectation** — BQ23 demoted it deliberately |
| KO | UNKNOWN | **UNKNOWN, 0/3** | holds; diagnosis re-verified in §5 |

TRV and ALL are the two undisputed HIGH controls.

## 2. What every one of the three factors actually rides on

Two concepts, and nothing else. `RECIPES` gives `NET_MARGIN` =
`NET_INCOME / TOTAL_REVENUE`, `GROSS_MARGIN` = `GROSS_PROFIT /
TOTAL_REVENUE`, `OPERATING_MARGIN` = `OPERATING_INCOME /
TOTAL_REVENUE`, `REVENUE_GROWTH` = `TOTAL_REVENUE` over time and
`EARNINGS_GROWTH` = `NET_INCOME` over time. So:

- **`TOTAL_REVENUE` alone gates two of the three factors** —
  profitability (every one of its three margins needs it as the
  denominator) and revenue growth;
- **`NET_INCOME` gates earnings growth**, and is a second route into
  profitability;
- `GROSS_PROFIT` and `OPERATING_INCOME` are numerators only and can
  never answer anything on their own. KO holds both and answers nothing.

`REVENUE_NET_OF_INTEREST_EXPENSE`, `NET_INTEREST_INCOME` and
`PREMIUM_REVENUE` appear in **no recipe**. That is not an oversight —
`tests/test_revenue_net_of_interest_concept.py` asserts it, over the
recipe table, six named modules and an AST walk of every `+` in `app/`.

## 3. The concept map — every income-statement concept, every company

`OK` located · `.` absent · `R` figure read and refused · `T` unsettled
across readings · `–` never asked (the concept post-dates the reading)

| | TOTAL_REV | REV_NET_OF_INT | GROSS | OP_INC | NET_INC | NII | PREMIUM |
|---|---|---|---|---|---|---|---|
| **AXP** | . | **OK** | . | . | **OK** | OK | . |
| **BCS** | . | – | . | . | . | OK | . |
| **C** | *no authoritative income consensus* | | | | | | |
| **COF** | . | – | . | . | **OK** | OK | . |
| **DB** | . | – | . | . | . | OK | . |
| **FITB** | . | – | . | . | **OK** | OK | . |
| **GS** | **R** | **OK** | . | . | **OK** | OK | . |
| **JPM** | **R** | **OK** | . | . | **OK** | OK | . |
| **KO** | **T 5/10** | – | **OK** | **OK** | . | . | . |
| **MTB** | *no authoritative income consensus* | | | | | | |
| **MUFG** | . | – | . | . | . | OK | . |
| **NWG** | . | – | . | . | **OK** | OK | . |
| **RF** | *no authoritative income consensus* (balance sheet survives) | | | | | | |

The banded eight for contrast: every one holds `TOTAL_REVENUE` **and**
`NET_INCOME` with a dated row. None needs gross profit. That is the
whole escape path, unchanged since BQ18.

## 4. What today's parser exposes — the deterministic half

`movrvest statement-shape`, all thirteen, one free fetch each, no model
asked, nothing stored. This is the answer to *does the source contain
it* and *does the parser expose it*, separated from *does a stored
reading carry it*.

| | `total_revenue` | `revenue_net_of_interest_expense` | `net_income` |
|---|---|---|---|
| **AXP** | UNREAD — `Revenues` (a heading) | **`Total revenues net of interest expense`** | `Net income` |
| **BCS** | no such line | **`Total income`** | UNREAD — **`Profit after tax`** |
| **C** | UNREAD — `Revenues (1)` | **`Total revenues, net of interest expense (1)`** | `Net income` |
| **COF** | **no such line** | no such line | `Net income` |
| **DB** | **no such line** | no such line | UNREAD — a *component* line; the real bottom line is `Profit (loss)` |
| **FITB** | UNREAD — `Wealth and asset management revenue` (a component) | no such line | `Net Income` |
| **GS** | `Total net revenues` — **refused by BQ23** | **`Total net revenues`** | `Net earnings` |
| **JPM** | `Total net revenue` — **refused by BQ23** | **`Total net revenue`** | `Net income` |
| **KO** | `Net Operating Revenues` | no such line | UNREAD — **`Consolidated Net Income`** |
| **MTB** | UNREAD — `Mortgage banking revenues` (a component) | no such line | `Net income` |
| **MUFG** | no such line | no such line | *"no such line"* — **and the statement is truncated; see §7** |
| **NWG** | no such line | **`Total income`** | `Profit for the year` |
| **RF** | **no such line** | no such line | `Net income` |

**Six print the net-of-interest total and the parser reads all six.**
That is the shared boundary the brief asked for.

## 5. The taxonomy, by first causal boundary

The brief's candidate labels did not survive intact; two were split and
one was added. Each company is classed on the **first** boundary at
which usable evidence is lost, traced from the store forward.

### N — established evidence with no consuming measure (3)

`AXP · GS · JPM`

Quorate, unwithdrawn, dated. Each holds `REVENUE_NET_OF_INTEREST_EXPENSE`
as settled consensus (`5 of 5 agree` on the fresh half of a ten-reading
file) and `NET_INCOME` with a three-period row. **Nothing is missing and
nothing is refused in error.** `TOTAL_REVENUE` is absent for AXP (its
label was never a `TOTAL_REVENUE` form) and *refused* for GS and JPM by
BQ23's structural rule, which is correct — and `withdrawn_assignments=5`
on both shows BQ27's supersession retiring the stale positive that once
voted for it. The evidence exists in its right slot under its right
name, and no factor reads that slot.

This is a **new class**, and it is the direct consequence of BQ22's
Ruling C plus BQ24's naming: the quantity was moved out of a slot that
had consumers into a slot that has none, deliberately, with the
comparability question left open.

### C — stored readings predate a parser repair (3)

`C · MTB · RF`

All five income readings withdrawn, and the stored reasons are the HON
defect verbatim:

```
C    net_interest_income: the filer heads $ 59,792 with '2025'
     and the reading recorded 'Years ended December 31,'
MTB  net_income: the filer heads $ 2,851 with '2025'
     and the reading recorded 'Year Ended December 31,'
RF   net_income: the filer heads $ 2,156 with '2025'
     and the reading recorded 'Year Ended December 31'
```

Confirmed to be the same defect and not merely the same wording: each
withdrawn reading stores a **single-cell row** carrying the merged
header, exactly as HON's did, where today's parse heads the cell with
the year and returns three dated cells. `AuditVerdict.STALE_PROVENANCE`
— numerically correct, evidentially incomplete.

**These three are `READY_FOR_REOBSERVATION`, and §6 shows it buys no
band.**

### A — the filer prints no consolidated top line (4)

`COF · FITB · MTB · RF`

*(MTB and RF appear in both C and A: their readings are stale **and**
their filers print no total. Withdrawal is the first boundary; absence
is the one behind it.)*

`statement-shape` returns *no such line* or a fee **component** for the
top line, and BQ21 read all four structurally: each prints
`Total interest income`, `Total interest expense`, a net interest
subtotal and a non-interest subtotal, and never their sum. A combined
figure would be this platform's arithmetic, which Invariant 1 forbids.

One qualification that must travel with this class: **COF's own
management report publishes the figure** — `Net interest income` 42,878
+ `Non-interest income` 10,556 = `Total net revenue` **53,434**, and the
filer states that construction as its definition. `TOTAL_REVENUE` is
scoped to the statement, which is right; whether a management-report
figure may ever answer a statement concept is a separate boundary
question and is not raised here.

### V — the bottom-line label is in no vocabulary (3)

`BCS` (`Profit after tax`) · `DB` (`Profit (loss)`) · `KO`
(`Consolidated Net Income`)

Three distinct forms, none accepted; verified by `matches_concept`
against every concept, all three `NO MATCH`. `NWG`'s `Profit for the
year` **is** accepted, which is what makes this a vocabulary gap rather
than a claim about IFRS filers.

**Widening `NET_INCOME` bands none of the three.** BCS gains earnings
growth only (its top line is a net-of-interest total with no consumer)
→ 1 of 3. DB the same → 1 of 3. KO gains earnings growth and still
cannot answer profitability or revenue growth, because both need the
`TOTAL_REVENUE` its tie withholds → 1 of 3. Measured, not assumed.

### F — the concept is contested between readings (1)

`KO` — see §6 for the full audit.

### B — the located section is truncated (1)

`MUFG`

`total_revenue` and `net_income` both absent, and the two absences are
not the same fact. The located income statement is **one table of 46
rows ending at `Total`** (other non-interest expenses); pre-tax income,
tax and the bottom line are outside it. `income_statement_text` is
3,162 characters and contains **zero** occurrences of *net income*. Its
four subtotals are bare `Total` under their own headings, unreachable
by a concept check that reads the row label alone. `located_among=2`.

**No amount of reading fixes a locator.** MUFG is the one company in
the corpus where re-observation is not merely unhelpful but incapable.

### E, G, H — the brief's remaining classes

- **E — grounding refused a claim**: **1**, and it is correct. GS and
  JPM's `total_revenue` refusal is `NET_OF_FINANCING_COST`, stating the
  cell, the marker row above it and the column. It is BQ23 working, not
  failing, and both companies appear under N because the refusal is
  right and the consequence is the missing consumer.
- **G — applicability or quorum blocks an assessment**: **0**. Every
  UNKNOWN that holds a consensus is **quorate** (`state=quorate`,
  `observation_count ≥ 5`). Not one is blocked by the quorum, and
  `MINIMUM_ANSWERED = 2` is reached by nobody rather than blocking
  anybody at 2.
- **H — propagation**: **2 latent**, and DV2's guarantee holds for the
  other eleven. See §8.

### Counts

| class | first causal boundary | n | companies |
|---|---|---|---|
| **N** | established, no consuming measure | **3** | AXP, GS, JPM |
| **C** | stored readings predate a parser repair | **3** | C, MTB, RF |
| **A** | filer prints no consolidated top line | **4** | COF, FITB, *MTB*, *RF* |
| **V** | bottom-line label in no vocabulary | **3** | BCS, DB, KO |
| **F** | concept contested between readings | **1** | KO |
| **B** | located section truncated | **1** | MUFG |
| **E** | grounding refused, correctly | 1 | *GS, JPM — counted under N* |
| **G** | applicability / quorum | **0** | — |
| **H** | propagation | **2 latent** | C, MTB |

Thirteen distinct companies; MTB, RF and KO each carry two boundaries,
named in the order they are met.

## 6. KO — the contested-concept diagnosis, re-verified

The brief asked whether BQ17's diagnosis still holds. **It does, and it
is two independent problems rather than one.**

**Which concepts are contested.** Exactly one: `TOTAL_REVENUE`. Ten
authoritative readings, `agree=5/10`:

```
absent_because: Where the statement prints this figure is unsettled
across 10 readings: 5× no figure located; 5× "Net Operating Revenues"
= $ 47,941 at table 0, row 1, column 3.
```

`NET_INCOME` is **not** contested — `10 of 10` readings agree it is
absent, and they are right: KO prints `Consolidated Net Income`, which
no vocabulary accepts. That is class V, not a tie.

**Why the tie is contested, and which contract refuses to break it.**
BQ20's `rule_absences` returns `AbsenceStanding.ACTIVE` for all five
stale absences, with its own reason:

> *every label located for total_revenue was already acceptable under
> the vocabulary this absence was read under, so the difference is
> between readings rather than between contracts*

KO's readings carry no `produced_under` stamp, so the rule bounds them
by `vocabulary_contracts.PUBLISHED`: `ba55a427097938f3` and
`3cdbddd6a1fcf0e6`. The second — BQ11's contract — **accepts `net
operating revenues`**. So the bound cannot exclude a vocabulary that
would have read the label, and the disagreement is genuine reader
disagreement.

**Is the refusal still correct? Yes.** This is exactly the distinction
BQ20 was built to draw, and it separates KO from UNP for a reason
neither company's outcome could reveal: UNP's located label
`Total operating revenues` is accepted by **no** contract in its bound,
so its five stale absences are withdrawn and it bands MEDIUM 62. KO's is
accepted by one. BQ19 (#167) recorded *"UNP and KO are ONE condition"*;
they measurably are not, and BQ20 is why.

**Would resolving KO need a semantic policy decision? Yes — and it is
the only route left.**

- The absence cannot be superseded on evidence. `statement_audit` does
  not audit absences at all, by an explicit ruling in its own docstring:
  *a stored absence is a claim about the reading, not about the
  document, and the document cannot refute it.*
- A sixth fresh reading would carry the vote 6-to-5 — but `observe`
  counts only authoritative readings and stops on the count, and KO
  holds ten. **`movrvest observe-statements KO` is a no-op.** Reaching a
  fresh quorum means superseding first, and nothing licenses that.
- What remains is a rule about **ties**: whether a positive located
  reading outweighs an equal number of absences. That is precisely the
  *"a stale absence votes"* problem BQ19 named, and adopting it would
  weaken every absence in the corpus, not only KO's.

**No refusal was weakened and KO stays UNKNOWN, 0 of 3.** Recorded
separately: if `TOTAL_REVENUE` alone settled, KO reaches **2 of 3** —
gross margin and operating margin both become computable against its
already-established `Gross Profit` 29,544 and `Operating Income` 13,762,
and revenue growth follows. Its net income gap does not block a band.

## 7. Deterministic readiness — and what it is worth

`READY_FOR_REOBSERVATION`, on the strict test the brief set (today's
parse exposes everything needed; the stored readings do not):

| | authoritative | withdrawn | what a fresh reading establishes | factors after | band after |
|---|---|---|---|---|---|
| **C** | **0** | 5 | `Net income` dated; `Total revenues, net of interest expense` **as the net-of-interest concept, which has no consumer** | **1 of 3** | **UNKNOWN** |
| **MTB** | **0** | 5 | `Net income` 2,851 dated (earnings growth ≈ +10.2%) | **1 of 3** | **UNKNOWN** |
| **RF** | **0** | 5 | `Net income` 2,156 dated (earnings growth ≈ +13.9%) | **1 of 3** | **UNKNOWN** |

**Validation predictions, not established facts. Nothing is stored.**

- **Replacements required**: 5 authoritative readings each — all three
  quorums are already fully withdrawn, so there is nothing to supersede
  first. Unlike HON, the intermediate state already exists.
- **Minimum model calls by quorum**: **5 per company, 15 for all
  three.**
- **Expected yield: 0 bands.** All three move from *no consensus at all*
  (C, MTB) or *0 of 3* (RF) to *1 of 3*, which is honester and is not an
  assessment. This is BQ18's measurement re-confirmed with the concept
  map behind it.

The three that would band are the three that need **no** reading at all:
AXP, GS and JPM already hold the evidence. Which is §8.

## 8. The counterfactual — measured in memory, over the same held consensus

`RECIPES` substituted inside one process so that the four margin and
growth recipes read `REVENUE_NET_OF_INTEREST_EXPENSE`; the corpus
re-derived from the identical stored consensus; the table restored and
asserted byte-identical afterwards. **No production value was altered
and nothing was written.**

| | before | after |
|---|---|---|
| **GS** | UNKNOWN, 1/3 | **HIGH 80**, 3/3 — profitability **`excellent`**, revenue growth `moderate`, earnings `strong` |
| **JPM** | UNKNOWN, 1/3 | **MEDIUM 62**, 3/3 — profitability **`excellent`**, revenue growth `weak`, earnings `declining` |
| **AXP** | UNKNOWN, 1/3 | **MEDIUM 62**, 3/3 — profitability `strong`, revenue growth `moderate`, earnings `moderate` |
| **BCS** | UNKNOWN, 0/3 | **unchanged** — the concept was never asked of its readings, and its bottom line is unreadable |
| **C** | no consensus | **unchanged** |
| **NWG** | UNKNOWN, 1/3 | **unchanged** — the concept was never asked of its readings |

Three bands, **zero model calls**, from evidence already in the store.
And it reproduces BQ21 §3's simulated GS HIGH and JPM MEDIUM exactly,
which is the harness validating itself.

**Why it is nevertheless not a repair.** GS 29.5% and JPM 31.3% are
margins struck on a base that has already deducted interest expense — a
bank's largest single cost — and they enter the same threshold table
that gives Procter & Gamble `strong` at 18.6% on gross sales. BQ21 §6
measured the general form: adding the constructed base makes **six of
seven banks `excellent` while zero of four insurers are**. BQ22's
Ruling C removed that defect from production on purpose. Restoring it
under a new concept name would be Invariant 10 in its semantic form —
*an established number is authority to report the number, not authority
to invent what the number means* — and it would resolve, silently and
in favour of one side, the comparability question BQ21 explicitly left
to a ruling.

So the highest-leverage candidate in the corpus is a **question for the
owner**, and the honest form of it is:

> May a profitability verdict computed on a revenue net of interest
> expense enter the same band arithmetic as one computed on gross
> revenue — and if not, what is its own ruler?

Three answers, each with its cost already measured:

| answer | live effect |
|---|---|
| **yes, same ruler** | UNKNOWN 13 → **10** free (AXP, GS, JPM at 3/3); → **7** with 15 readings (BCS + a `NET_INCOME` form, C, NWG). Reinstates the comparability defect BQ21 measured and BQ22 removed |
| **no — its own factor and its own thresholds** | nothing ships until a threshold is grounded. Seven banks is not a corpus; S5.3's *magnitude is not quality* applies again |
| **no — and say so** | the six keep UNKNOWN and gain a **worded** reason naming the quantity they print and what this platform cannot yet compare it to. Free, deterministic, no band |

The third is not a null option. Today an investor reading GS is told
*"1 of 3 factors answered"* and is never told that the platform read a
consolidated top line, named it correctly and has no ruler for it.

## 9. Propagation — proven, with two holes

Every company's grounded object was pushed through the builder's own
`_quality_value`, `_quality_basis` and `_grounded_derivation`, twice:
once with no provider recommendation and once with a synthetic one
constructed to score **80**.

**Eleven of thirteen: clean.** Every grounded UNKNOWN returns
`_quality_value = None` under both probes, stamps **no** rule, and words
its basis from the domain object — *"N of 3 factors answered — fewer
than 2, so no band is claimed. That is a limit of the established
evidence, not a finding about the company"*, followed by the filing's
own citation. The string *"Quality data is unavailable"* appears for
none of them, and the provider proxy loses even when it would score 80.
DV2's guarantee holds.

**Two holes, both at the same seam.**

1. **C and MTB produce no grounded object at all**, because every
   reading of their only statement is withdrawn. `quality_of` returns
   `None`, so `_quality_value` falls through to `_quality_score(company)`
   — and the synthetic provider recommendation **scores them 80**. The
   docstring's promise is specifically that *a grounded assessment
   governs outright … including when it bands `UNKNOWN`*; total
   withdrawal is not an UNKNOWN band, it is the absence of a band, and
   the builder cannot tell it from *never read*. `FinancialStatementService.withdrawn()`
   exists precisely to draw that distinction and **reaches this
   function nowhere.**

   **Not live**: neither C nor MTB holds a provider row
   (`data/cache/fundamentals` has rows for AAPL, DIS, PG and TSLA only,
   of the 24). Any `movrvest acquire` that adds one arms it. RF is
   protected by accident — its balance sheet survived, so `measure`
   succeeds and produces an UNKNOWN band that governs.

2. **`statement-shape` states a filer's silence about a section it
   stopped reading.** For MUFG it prints `net_income  the statement
   prints no such line` where the located table ends 46 rows in, before
   pre-tax income. The *investor-facing* consensus wording is correct —
   it says the **reading** located no cell — so this is confined to a
   developer surface. It is BQ21's recorded-not-fixed `evidences_absence`
   hole: the guard requires *some* concept located, which catches a
   statement read **not at all** and not one read **partially**.

## 10. Repair candidates, ranked by leverage

| # | candidate | UNKNOWNs addressed | deterministic? | diagnosis confidence | generality | calls after repair | risk to evidence standards |
|---|---|---|---|---|---|---|---|
| **1** | **Rule on the net-of-interest quantity's investment meaning** | **6** (3 free, 3 with readings) | the *effect* is; the *decision* is not | **high** — measured twice, by BQ21 and again here | high — it settles a class, not a company | **0** for AXP/GS/JPM · 15 for BCS/C/NWG | **high if answered "same ruler"** — reinstates a measured comparability defect |
| **2** | Close the total-withdrawal propagation hole | 0 bands; removes a latent wrong score for **2** | **yes, fully** | **high** — reproduced with a synthetic provider row | high — any future audited-away company | **0** | **none** — it strengthens a boundary |
| **3** | Widen `NET_INCOME` for `Profit after tax` / `Profit (loss)` / `Consolidated Net Income` | 0 bands; +1 factor for **3** | falsification is; realisation needs readings | high — three `NO MATCH` verifications | medium — IFRS and one US form | 15 (BCS, DB, KO) | low, under BQ19's arithmetic standard |
| **4** | Re-observe C, MTB, RF | **0 bands** | readiness is proven; the yield is nil | high | none — three companies | **15** | none |
| **5** | Tie-breaking rule for KO | 1, if it banded | no — a policy | n/a | **dangerous** — it weakens every absence | 0 | **high** — the brief forbids it |
| **6** | A bank financial model / locator work for MUFG | 1–7 | no | BQ21 refused it on evidence | blocked by the Prudential boundary | n/a | n/a |

Candidate 5 is listed to be refused: the brief's instruction not to
weaken KO's refusal is the right call, and §6 shows the refusal is
correct on its own terms.

## 11. Recommended next slice

# SEMANTIC RULING REQUIRED

**Not** deterministic repair, and **not** paid re-observation.

The single highest-leverage question in the corpus is already answered
in the negative by measurement and has never been answered by a ruling:
six of thirteen UNKNOWNs print a consolidated top line this platform
reads and names, three hold it as established evidence with dated net
income beside it, and connecting it to the existing band arithmetic
would restore the exact defect BQ22 was built to remove. **No code
change is the right first move.** The owner decides which ruler that
quantity gets, or that it gets none and is said so.

**Bundle one free deterministic repair with it**: candidate 2, the
total-withdrawal propagation hole. It ships no band, it removes a way
for a provider proxy to score a company whose every reading was audited
away, and it is the one item on the list with zero risk to evidence
standards. It is also the shape of defect the constitution says ships
regardless — *a decision currently getting a wrong answer.*

## 12. Model spend — is any justified next?

# NO

- **AXP, GS and JPM need zero calls.** Their evidence is established,
  quorate and dated. What they need is a ruling.
- **C, MTB and RF are ready and worth nothing.** 15 calls, 0 bands,
  measured — every one of the three moves to `1 of 3` because its filer
  prints no consolidated total. Funding them would buy honest evidence
  and no assessment, and the brief's own preference — *general
  deterministic repair → validation* over *paid re-observation →
  discover deterministic defect* — points away from it.
- **BCS, DB and KO need a free falsification first.** A `NET_INCOME`
  widening is provable offline against all 24 filings, and it bands
  none of the three even if correct.
- **MUFG is unreachable by reading.**

If the ruling in §11 comes back *"yes, same ruler"*, the justified spend
is then **15 readings — BCS, C and NWG, five each** — and BCS needs the
`NET_INCOME` widening in the same slice or it stays at 1 of 3. **None of
it is executed here.**

## 13. Purity

No production write · no promotion · no supersession · no
re-observation · no model or API call · no rule, threshold, vocabulary,
recipe, parser or UI change · `git status --porcelain` empty ·
`data/statements` fingerprint **`a148e451aa5ee82a3732dcfa4569f284`**,
byte-identical to what BQ18 left · the `RECIPES` substitution in §8 ran
in one process and the table was restored and asserted equal to
baseline · every figure above is a filer's printed row, this platform's
own deterministic parse of a filing the resolver already names, or the
platform's own arithmetic over checked cells · the thirteen
`statement-shape` runs each cost one free SEC EDGAR fetch, ask no model
and store nothing.
