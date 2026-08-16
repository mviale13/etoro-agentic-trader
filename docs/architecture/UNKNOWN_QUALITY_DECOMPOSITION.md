# The sixteen UNKNOWNs, decomposed

**Status: research report, BQ5. No implementation. Offline over the
tracked 24-company statement corpus; no model call, no credit spent.
Stopped for ruling.**

Eight companies band. Sixteen do not. This asks what exact authority is
missing for each, and refuses to answer "missing data".

**The completeness rule first, because it reframes everything.**
Grounded Business Quality requires `MINIMUM_ANSWERED = 2` of its three
questions — **not** 3. So nine of the sixteen are **one factor** from a
band, and the question is never "how do we answer everything".

**The universal finding:**

> **`revenue_growth` is unanswered for 16 of 16.** Not one UNKNOWN
> company answers it. It is the only question with no exceptions, and
> `total_revenue` — the concept it needs — is also the denominator of
> the net margin that would answer profitability for twelve of them.

---

## 1. The sixteen, measured

`ANS` = answered. Blocked cells name the concept and what
`statement-shape` says about it in the document itself.

| Symbol | ans | profitability | revenue_growth | earnings_growth |
|---|---|---|---|---|
| ALL | 1 | **ANS** strong | no-earlier-period `Total revenues` | no-earlier-period `Net income (loss)` |
| AXP | 1 | gross_profit **not printed** | total_revenue **UNREAD** | **ANS** moderate |
| BCS | 0 | gross_profit **not printed** | total_revenue **not printed** | net_income **UNREAD** |
| C | 0 | gross_profit **not printed** | total_revenue **UNREAD** | net_income **PRINTED** ⚠ |
| COF | 1 | gross_profit **not printed** | total_revenue **not printed** | **ANS** declining |
| DB | 0 | gross_profit **not printed** | total_revenue **not printed** | net_income **UNREAD** |
| FITB | 1 | gross_profit **not printed** | total_revenue **UNREAD** | **ANS** moderate |
| HON | 1 | **ANS** strong | no-earlier-period `Net sales` | no-earlier-period `Net income` |
| KO | 0 | total_revenue **UNREAD** | total_revenue **UNREAD** | net_income **UNREAD** |
| MTB | 0 | gross_profit **not printed** | total_revenue **UNREAD** | no-earlier-period `Net income` |
| MUFG | 0 | gross_profit **not printed** | total_revenue **not printed** | net_income **not printed** |
| NWG | 1 | gross_profit **not printed** | total_revenue **not printed** | **ANS** strong |
| RF | 0 | gross_profit **not printed** | total_revenue **not printed** | no-earlier-period `Net income` |
| TSLA | 1 | **ANS** weak | no-earlier-period `Total revenues` | no-earlier-period `Net income` |
| UNP | 1 | gross_profit **not printed** | total_revenue **UNREAD** | **ANS** moderate |
| WMT | 1 | **ANS** weak | no-earlier-period `Total revenues` | net_income **UNREAD** |

### The six states, kept apart as the brief requires

| State | Meaning here | Where |
|---|---|---|
| **evidence present but unread** | the filer prints a line; this platform's `CONCEPT_LABELS` does not accept the label | 9 factor-instances (AXP, C, FITB, KO×3, MTB, UNP · BCS, DB, WMT) |
| **evidence read but not established** | the concept is printed under an accepted label and five readings still failed to locate it | **1 — C's `Net income`** ⚠ |
| **evidence present, comparative undatable** | the concept *is* established for the current period; the earlier column cannot be dated from the filer's own headers | 9 factor-instances (ALL×2, HON×2, TSLA×2, WMT, MTB, RF) |
| **evidence absent (supported)** | `statement-shape` supports *the filer prints no such line* — statement read, no near label unread | gross_profit ×11, total_revenue ×6, net_income ×1 |
| **factor not applicable** | — | **none**: the generic contract asks all three of every company |
| **applicability unknown** | — | **none in this layer**; `FinancialModel.BANK` would decline leverage and cash generation, neither of which Business Quality consults (BQ2) |

**No factor is inapplicable and no applicability is unresolved.** That
matters: the sixteen are not a modelling problem, which is what BQ2
already proved from the other direction.

## 2. Blocking frontier per company

The smallest set of unresolved factors whose resolution *could* permit
a band under the unchanged rule. **This assumes nothing about how a
resolved factor would score.**

| Symbol | needs | Frontier | Offline-resolvable? |
|---|---|---|---|
| **KO** | 2 | any 2 of 3 — all three are vocabulary (`Net Operating Revenues`, `Consolidated Net Income`) | **yes, all three** |
| **C** | 2 | revenue_growth (vocabulary) **+** earnings_growth (extraction) | vocabulary yes; extraction **no** |
| **MTB** | 2 | revenue_growth (vocabulary) **+** earnings_growth (dating) | **yes, both** |
| **ALL, HON, TSLA** | 1 | either growth question — both are dating | **yes** |
| **WMT** | 1 | revenue_growth (dating) **or** earnings_growth (vocabulary) | **yes, either** |
| **AXP, FITB, UNP** | 1 | revenue_growth (vocabulary) | **yes** |
| **BCS, DB** | 2 | only **one** factor is resolvable (net_income vocabulary); the other two are supported absences | **no — resolving everything available still leaves UNKNOWN** |
| **RF** | 2 | only **one** resolvable (earnings dating) | **no — stays UNKNOWN** |
| **COF, NWG** | 1 | **none** — profitability and revenue_growth are both supported absences | **no — structurally UNKNOWN** |
| **MUFG** | 2 | **none** — all three concepts supported-absent | **no — structurally UNKNOWN** |

**Five companies (COF, NWG, MUFG, BCS, DB) plus RF cannot reach a band
by any offline repair**, because what blocks them is evidence the
filer's income statement genuinely does not carry in a form this
platform accepts. That is a finding about the question set, not about
the reading.

## 3. Root-cause decomposition

Counted by **factor-instance** (a company can appear in several rows)
and by **company**.

| Root cause | Factor-instances | Companies blocked |
|---|---|---|
| **Concept vocabulary mismatch** (present but unread) | **9** | 9 — AXP, BCS, C, DB, FITB, KO, MTB, UNP, WMT |
| **Comparative period undatable** (established, no earlier column) | **9** | 6 — ALL, HON, MTB, RF, TSLA, WMT |
| **Required concept genuinely absent** (supported) | **18** | 12 — AXP, BCS, C, COF, DB, FITB, MTB, MUFG, NWG, RF, UNP + KO(none) |
| **Extraction failure** (printed, accepted label, unlocated 5/5) | **1** | **1 — C** |
| **Acquisition unavailable** | 0 | — every company has a readable statement |
| **Statement consensus insufficient** | 0 | — all 24 are quorate at 5 of 5 |
| **Applicability unresolved / question-contract mismatch** | 0 | — see §1 |
| **Completeness despite valid answers** | **9** | 9 companies answer exactly 1 of the required 2 |

A category the corpus forced, not on the brief's list:

> **Structurally unanswerable under the generic question set — 6
> companies** (COF, NWG, MUFG, BCS, DB, RF). Their income statements
> print no gross profit, and for most no total revenue this platform
> accepts. These are not defects in reading; the question set asks an
> industrial's questions of a bank.

## 4. Shared blockers, ranked by companies blocked

**1 — `total_revenue` not established: 12 companies.** Blocks
`revenue_growth` for all 12 *and* the net margin that would answer
profitability for most of them. **6 are vocabulary** (AXP, C, FITB, KO,
MTB, UNP — the filer prints `Revenues`, `Operating revenues:`, `Net
Operating Revenues`) and **6 are supported absences** (BCS, COF, DB,
MUFG, NWG, RF). Fixing the vocabulary half is deterministic and offline
**but does not by itself establish anything** — a widened
`CONCEPT_LABELS` changes what a *future reading* may accept, and the
stored readings were taken under the old vocabulary. **Maximum
companies made band-eligible by vocabulary alone: 0 without
re-observation.**

**2 — comparative period undatable: 6 companies, 9 factor-instances.**
The concept is already established for the current period; only the
earlier column cannot be dated from the filer's own headers. **This is
the one blocker whose repair might not need re-observation** — the
stored `row` tuples carry every located cell with its `column_header`,
so whether a datable earlier period is already in the store is an
offline question. It is the frontier for ALL, HON, TSLA and half of
WMT/MTB/RF.

**3 — `gross_profit` genuinely absent: 11 companies.** Supported by
`statement-shape`; not a defect. It blocks profitability only because
the *other* two margins also fail. **Not repairable and should not be.**

**4 — extraction failure: 1 company (C).** Real, isolated, and the only
case where the document, the vocabulary and the platform agree and the
reading still failed. **Requires funded re-observation to test.**

**Ranking note as instructed**: blocker 1 has the highest coverage and
is *not* therefore the recommended slice — see §7.

## 5. The seven zero-answer companies, re-audited after BQ4

BCS, C, DB, KO, MTB, MUFG, RF — why zero survives despite readable
statements:

- **KO** — all three blocked by **vocabulary alone**. Coca-Cola's
  statement was read (20 rows, gross profit and operating income
  located); `Net Operating Revenues` and `Consolidated Net Income` are
  not accepted labels. **The most repairable company in the corpus, and
  the one whose zero is least about the company.**
- **C** — revenue vocabulary (`Revenues (1)`) **plus** the corpus's only
  extraction failure (`Net income` printed and accepted, unlocated 5/5).
  Two independent defects in one company.
- **MTB** — revenue vocabulary plus an undatable comparative.
- **BCS, DB** — bottom line printed under IFRS wording (`Profit after
  tax`, unread); gross profit and total revenue supported-absent. One
  resolvable factor, two needed.
- **RF** — gross profit and total revenue supported-absent; earnings
  comparative undatable. One resolvable, two needed.
- **MUFG** — **nothing is resolvable**: all three concepts are supported
  absences, and its statement establishes exactly one line
  (`Net interest income`) with no corroborating figure. The genuinely
  hardest case, and the honest answer is that the generic question set
  cannot read this filing.

**Four of the seven (KO, C, MTB, and partially BCS/DB) are blocked by
this platform's vocabulary or reading — not by the filer.** BQ4 made
that visible in the wording; it did not change it.

## 6. Near-bound companies — one gap from eligibility

| Symbol | Current evidence | Exact blocker | Fact required | If established |
|---|---|---|---|---|
| **AXP** | earnings growth *moderate* | revenue_growth: `Revenues` unread | total revenue, two dated periods | **2 of 2 → band** |
| **FITB** | earnings growth *moderate* | same | same | **band** |
| **UNP** | earnings growth *moderate* | `Operating revenues:` unread | same | **band** |
| **ALL** | profitability *strong* | both growth rows undatable | one dated earlier period | **band** |
| **HON** | profitability *strong* | `Net sales` / `Net income` undatable | same | **band** |
| **TSLA** | profitability *weak* | `Total revenues` / `Net income` undatable | same | **band** |
| **WMT** | profitability *weak* | revenue undatable **or** `Consolidated net income` unread | either | **band** |

**Seven companies are exactly one authority away.** No band is
predicted: the ruler needs the resolved factor's own verdict, which is
not knowable until the fact is established.

## 7. Funding gate

**OFFLINE — corpus and code sufficient**
- Whether a datable earlier period already sits in the stored `row`
  tuples for the 6 undatable-comparative companies. The store holds
  every located cell with its `column_header`; nothing else is needed
  to answer it. **Covers the frontier of ALL, HON, TSLA, WMT, MTB, RF.**
- Auditing which accepted labels each filing prints (done here).
- Confirming the 6 supported absences are supported (done here).

**NEW NON-LLM EVIDENCE — acquisition without model inference**
- Nothing. Every company already has an acquired, quorate statement.
  There is no missing document.

**FUNDED LLM VALIDATION REQUIRED**
- **Any vocabulary repair's actual effect.** Widening `CONCEPT_LABELS`
  changes what a *reading* accepts; the 5 stored readings were taken
  under the old vocabulary and carry `unlocated_because` for concepts
  they never accepted. **The store cannot tell us what a re-reading
  would find** — so the entire 9-company vocabulary population is
  unverifiable offline.
- **C's extraction failure.** Whether a re-reading locates `Net income`
  is precisely a question about the reader.

**The critical path has moved.** BQ2, BQ3 and BQ4 were all answerable
offline. The largest remaining blocker is not.

## 8. Recommendation — exactly one next slice

**The undatable-comparative investigation, offline, first.**

Not because it has the highest coverage — `total_revenue` does — but
because it is **the only remaining blocker whose answer is still free**,
and it covers **6 companies including 4 of the 7 near-bound ones**. The
question is sharp and settleable from the store alone: *for a concept
whose current period is established, does the stored row already carry
an earlier cell this platform could date?* If yes, the repair is
deterministic and needs no re-observation. If no, that population joins
the funded queue and the funding decision becomes unambiguous.

**And then fund the LLM.** After that investigation, every remaining
blocker — the 9-company vocabulary population and C's extraction —
requires re-observation to test at all. That is the honest trigger the
brief asks for: funding stops being *useful* and becomes *necessary* the
moment the offline question above is answered, whichever way it lands.

**Not recommended now**: widening `CONCEPT_LABELS`. It is the highest-
coverage change and it would establish **nothing** without a funded
re-read — spending a vocabulary ruling to buy zero bands, and BQ3
already ruled it must not ride along with wording work.

## Scope compliance

No change to Business Quality, completeness, thresholds, financial-model
selection, statement vocabulary, extraction, schemas, narrative
knowledge, crypto, UI or PR #145. Nothing re-observed, no model called,
no credit spent. Every figure is read from `data/statements` or produced
by executing existing code unchanged, and is reproducible offline.
