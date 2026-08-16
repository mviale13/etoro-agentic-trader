# The evidence recovers; the corpus cannot receive it

**Status: experiment, BQ13. Fifteen model readings spent, the exact
authorised budget, all on ALL, TSLA and WMT. Production corpus
byte-identical. No code change, no vocabulary change, no rule change.
Stopped for ruling.**

BQ8 proved that today's pipeline captures the historical cells the old
readings lost. BQ13 spends the authorised credits to carry three
near-bound companies all the way to a band, and to find out whether the
result can reach production.

**Both halves answered, and they disagree.**

> **The evidence half succeeded completely.** Fifteen readings, zero
> disagreement, every value equal to the deterministic parse to the
> digit. **ALL → HIGH (80), TSLA → LOW (40), WMT → LOW (40)** — three
> UNKNOWNs resolved, under rules that did not move.
>
> **The promotion half failed, and the reason is structural rather than
> operational.** Appending the five fresh readings to the five stale
> ones in the ordinary way leaves the consensus **exactly as it was**.
> Not partly repaired — **unchanged**, for all three companies.
>
> **A dated and an undated reading of the same cell are indistinguishable
> to the consensus**, so the stale reading wins by being first.

There is no clean promotion path. This report stops at that boundary
rather than copying files past it.

---

## 1. Actual model usage

**Fifteen readings**, all `gpt-5` (the reader's default, unchanged), all
income statement, all against the already-resolved 10-K.

| Company | Readings | Filing | Outcome |
|---|---|---|---|
| ALL | 5 | `0000899051-26-000031` | quorate |
| TSLA | 5 | `0001628280-26-003952` | quorate |
| WMT | 5 | `0000104169-26-000055` | quorate |

**No other company was observed.** HON, MTB, RF, KO, C, AXP, FITB and
UNP were not read, and nothing outside the income statement was read
for the three that were.

**Every observation went to an isolated evidence root** (`/tmp/bq13`),
declared through `MOVRVEST_EVIDENCE_ROOT` *and* through an explicit
store path — belt and braces, because #118's lesson is that a call
which declares only a subject resolves its own evidence. The harness
asserts the store's directory is not `data/statements` before the first
reading.

**Fifteen was not a floor chosen for tidiness.** The brief permits
stopping early where existing compatible readings already participate.
§8 measures that they do not — a stale reading does not merely fail to
help, it *displaces* a fresh one — so the quorum had to be filled from
zero, three times.

## 2. Baseline — the production state before anything was spent

Recorded first, from the production store and the read-only quality
door. All three sit at **one answered factor of three**, which is below
`MINIMUM_ANSWERED = 2`, so no band is claimed.

| | ALL | TSLA | WMT |
|---|---|---|---|
| stored income readings | 5 | 5 | 5 |
| stored balance-sheet readings | 5 | — | 5 |
| source filing | 10-K `0000899051-26-000031`, FY2025 | 10-K `0001628280-26-003952`, FY2025 | 10-K `0000104169-26-000055`, FY2026 |
| profitability | **answered — strong** (net 15.2%) | **answered — weak** (gross 18.0%, op 4.6%, net 4.1%) | **answered — weak** (op 4.2%) |
| revenue growth | **not answerable** | **not answerable** | **not answerable** |
| earnings growth | **not answerable** | **not answerable** | **not answerable** |
| answered / favourable | 1 / 1 | 1 / 0 | 1 / 0 |
| score · band | — · **UNKNOWN** | — · **UNKNOWN** | — · **UNKNOWN** |

**Why each is UNKNOWN, exactly.** ALL and TSLA fail both growth factors
for one reason: *the row prints no earlier period this platform can date
from the filer's own column headers*. WMT fails revenue growth for that
same reason and earnings growth for a **different** one — `net_income`
is not established at all, because the filer prints `Consolidated net
income` and `CONCEPT_LABELS` does not accept it. **The two blockers are
not the same blocker**, and only the first is addressed here.

Established measures beneath those verdicts: ALL holds net margin
(15.2%) and liabilities-to-equity (2.91); TSLA holds gross (18.0%),
operating (4.6%) and net (4.1%) margin; WMT holds operating margin
(4.2%) and current ratio (0.79). Gross profit and operating income are
absent for ALL (an insurer prints neither); gross profit is absent for
WMT (its statement prints no such subtotal).

**Predicted recovery, pinned before spending.** Re-derived offline today
by running `historical_row` against the stored anchors and the source
documents — no model, no credit — and identical to BQ7 §4 and BQ8 §2–3:

| Company · concept | Predicted dated cells |
|---|---|
| ALL · total revenue | 2025 **67,685** · 2024 **64,106** · 2023 **57,094** |
| ALL · net income | 2025 **10,266** · 2024 **4,599** · 2023 **( 213 )** |
| TSLA · total revenue | 2025 **94,827** · 2024 **97,690** · 2023 **96,773** |
| TSLA · gross profit | 2025 **17,094** · 2024 **17,450** · 2023 **17,660** |
| TSLA · operating income | 2025 **4,355** · 2024 **7,076** · 2023 **8,891** |
| TSLA · net income | 2025 **3,855** · 2024 **7,153** · 2023 **14,974** |
| WMT · total revenue | 2026 **713,163** · 2025 **680,985** · 2024 **648,125** |
| WMT · operating income | 2026 **29,825** · 2025 **29,348** · 2024 **27,012** |

WMT's revenue row is the one BQ7 predicted and BQ8 never tested — TSLA
and ALL were BQ8's specimens, WMT was not read.

## 3. First-reading validation — the gate before the other twelve

One reading per company, checked against the deterministic parse before
a second was launched. **Five guards, any of which aborts that company
immediately:**

| Guard | What it refuses |
|---|---|
| row cells equal the parser's | a model-supplied historical figure |
| every period header is a bare four-digit year | a period inferred from column order |
| the parser's label at the anchor's index equals the reading's | an ambiguous or moved row |
| readings 2–5 byte-identical to reading 1 | semantic recognition drifting |
| the anchor cell equals production's | a current-period regression |

**All three passed every guard, and every value matched §2's prediction
to the digit.** No guard fired at any point, for any company, across all
fifteen readings.

**The anchors also moved to dated headers, as BQ8 found for TSLA and
ALL and as nothing had yet shown for WMT:**

| Company | Stored anchor header | Fresh anchor header |
|---|---|---|
| ALL | `Years Ended December 31,` | **`2025`** |
| TSLA | `Year Ended December 31,` | **`2025`** |
| WMT | `Fiscal Years Ended January 31,` | **`2026`** |

That change is the whole mechanism: `preceding()` reads the *anchor's
own* header first and returns nothing when it names no year, so an
undated anchor refuses a comparison before the row is even consulted.

**No component was promoted as a total**, checked against the filer's
own arithmetic:

- ALL: `Total revenues` 67,685 = 60,503 + 946 + 2,955 + 3,449 − 168 ✔;
  `Net income (loss)` 10,266 = 13,156 − 2,890 ✔ (the consolidated line,
  *above* the noncontrolling-interest attribution).
- TSLA: `Total revenues` 94,827 = 69,526 + 12,771 + 12,530 ✔ — and the
  reading did **not** take `Total automotive revenues` 69,526, the
  tempting subtotal two rows up. `Gross profit` 17,094 = 94,827 −
  77,733 ✔; `Income from operations` 4,355 = 17,094 − 12,739 ✔;
  `Net income` 3,855 = 5,278 − 1,423 ✔.
- WMT: `Total revenues` 713,163 = 706,413 + 6,750 ✔; `Operating income`
  29,825 = 713,163 − 535,395 − 147,943 ✔.

**And WMT's `net_income` stayed absent, which is the control working.**
The filer prints `Consolidated net income` 22,270 and the reading
refused it — the same shape as KO's parked case. `CONCEPT_LABELS` was
not touched, and the vocabulary blocker is confirmed as vocabulary
rather than as anything this slice changed.

## 4. Quorum progression

Identical in shape for all three, and identical to BQ12's KO: **the
evidence is complete at reading one; only the authority to use it
arrives at reading five.**

| n | consensus | ALL | TSLA | WMT |
|---|---|---|---|---|
| 1–4 | insufficient quorum | no band | no band | no band |
| 5 | **quorate** | **HIGH 80** | **LOW 40** | **LOW 40** |

The growth figures are byte-stable from n=1: ALL +5.5829% / +123.2224%,
TSLA −2.9307% / −46.1065%, WMT +4.7252% / (unanswerable). **Nothing
about the evidence changed at reading five**, and no band was shown
before the contract allowed one.

Agreement at quorum: **5 of 5 on every concept, for every company**,
settled and unsettled alike.

## 5. Semantic recognition versus deterministic expansion

Kept strictly apart, and the model is credited with nothing the parser
supplied.

| Company | LLM semantic recognition | Deterministic expansion |
|---|---|---|
| ALL | located the revenue and net-income rows; declined gross profit and operating income | **supplied all three periods and their headers** |
| TSLA | located all four rows, and passed over `Total automotive revenues` | **supplied all three periods** |
| WMT | located revenue and operating income; **declined** `Consolidated net income` | **supplied all three periods** |

**The model contributed exactly one thing per reading: which row.**
Every historical value and every period label came from `row_figures`
reading the filing's own table — which is why §2 could predict all of
them offline, before a credit was spent, and why the first guard could
be an equality check rather than a judgement.

**Reader stability, and not corroboration.** Five readings of one
filing are five readings of one filing. BQ4's language invariant holds
automatically over everything the three now produce: across 61
investor-visible sentences, `readings of one filing` appears 13 times
and **`independent`, `corroborat…`, `sources` and `observations` appear
zero times each.** No second document was read for any of the three, and
none is claimed.

## 6. Business Quality, before → after

| | ALL | TSLA | WMT |
|---|---|---|---|
| profitability, before → after | strong → **strong** | weak → **weak** | weak → **weak** |
| revenue growth | unanswerable → **moderate** (+5.58%) | unanswerable → **declining** (−2.93%) | unanswerable → **weak** (+4.73%) |
| earnings growth | unanswerable → **strong** (+123.22%) | unanswerable → **declining** (−46.11%) | unanswerable → **still unanswerable** |
| answered | 1 → **3** | 1 → **3** | 1 → **2** |
| favourable | 1 → **2** | 0 → **0** | 0 → **0** |
| score · band | — · UNKNOWN → **80 · HIGH** | — · UNKNOWN → **40 · LOW** | — · UNKNOWN → **40 · LOW** |

**The evidence that caused each transition**, in one line each:

- **ALL → HIGH.** The dated 2024 revenue (64,106) and net income (4,599)
  make both growth factors answerable. Revenue +5.58% bands *moderate*
  and earns nothing; earnings +123.22% bands *strong* and earns one.
  Two favourable of three answered is exactly `2/3` — **the HIGH
  threshold met on its boundary, not past it.**
- **TSLA → LOW.** The dated 2024 revenue (97,690) and net income (7,153)
  make both answerable and both **decline**. Zero favourable of three.
  Profitability was already *weak* and did not move.
- **WMT → LOW.** The dated 2025 revenue (680,985) makes revenue growth
  answerable at +4.73%, which bands *weak*. That is the second answered
  factor, which is the whole of what changed. Earnings growth is still
  blocked by `net_income`, so WMT reaches **2 of 3, never 3 of 3.**

**A non-UNKNOWN band is not the success here, and two of these three are
unflattering.** TSLA moves from *no assessment* to *the lowest band this
platform issues*, on the strength of its own filing reporting revenue,
gross profit, operating income and net income all lower than the prior
year. That direction is evidence the selection was not answer-driven:
the same mechanism that promoted ALL to HIGH demoted TSLA to LOW, and
neither outcome was reachable before because neither factor was
answerable.

**The rules did not move.** `MINIMUM_ANSWERED`, the 2/3 and 1/3 band
thresholds, `BAND_SCORES`, `FAVOURABLE_VERDICTS`, the growth analyst's
metric ladder and `CONCEPT_LABELS` are all untouched — `git status` is
empty and no file outside `docs/` is in this change. **Every transition
is added evidence under a fixed ruler.**

## 7. Newly authorised bands

**Three, and none of them is in production.**

| Company | Band | Score | Authorised by |
|---|---|---|---|
| ALL | **HIGH** | 80 | 2 favourable of 3 answered, quorate at 5 readings of one filing |
| TSLA | **LOW** | 40 | 0 favourable of 3 answered, quorate at 5 readings of one filing |
| WMT | **LOW** | 40 | 0 favourable of 2 answered, quorate at 5 readings of one filing |

Each band was checked with the production balance sheet composed
alongside the fresh income consensus, and is unchanged — the three
quality factors read the income statement only, and no balance-sheet
figure enters them.

## 8. Production handling, immutability, and the boundary

**Nothing was written to `data/`.** The three production statement files
are byte-identical:

| File | MD5, before and after |
|---|---|
| `TSLA.0001628280-26-003952.json` | `94d150735f0ef51aefc4b8c798a26516` |
| `ALL.0000899051-26-000031.json` | `b3ecb42f76515f2bb0894bec8db941ee` |
| `WMT.0000104169-26-000055.json` | `47524d69113251e5c783333e42fb72f5` |

`git status --porcelain` is empty. No stored observation was mutated,
reordered or deleted, and none could be: the store is append-only and
this experiment never held a handle to the production directory.

### The promotion path was looked for, and it does not exist

The ordinary acquisition action is `observe-statements`, which appends
to the existing file. **Measured with the real fresh readings, appending
changes nothing:**

| Company | production as-is | + 5 fresh appended | clean slate (5 fresh) |
|---|---|---|---|
| ALL | UNKNOWN (1 of 3) | **UNKNOWN (1 of 3)** | HIGH 80 (2 of 3) |
| TSLA | UNKNOWN (1 of 3) | **UNKNOWN (1 of 3)** | LOW 40 (0 of 3) |
| WMT | UNKNOWN (1 of 3) | **UNKNOWN (1 of 3)** | LOW 40 (0 of 2) |

Ten readings, five of them carrying every dated cell, and the growth
sentence is still *"the row prints no earlier period this platform can
date from the filer's own column headers."*

**The cause is one function and one omission.** `_fact_consensus`
compares readings through `_answer`, whose comparable form is

```text
"{label}" = {printed} at {cell}
```

— **the column header is not in it.** A stale reading and a fresh
reading of the same cell therefore produce the *identical* comparable
answer, are counted as agreeing, and `_settled` returns the **first**
observation that matches the modal. The store appends, so the first is
the oldest. **The stale reading does not merely fail to help; it
displaces the fresh one**, and adding more fresh readings cannot change
that, because they agree with the stale one by construction.

This is worth stating in its own right, separately from the band it
blocks: **two readings that place the same figure under different
periods are currently counted as agreeing.** Under Invariant 3 a
citation carries the relationship it was read from, and a period is part
of that relationship. Recorded, not repaired — repairing it is a change
to consensus semantics, which this brief forbids.

**The platform's own supersession mechanism is `STATEMENT_SCHEMA_VERSION`**,
documented at `financial_statement_store.py` in exactly these terms: a
version bump means the corpus of statement observations is re-read, and
`_restore` returns nothing for a file at another version, so `append`
writes a fresh file rather than pooling across the boundary. Schema 2's
precedent fits this case closely — the *locator* changed, so the text a
reading was shown changed, and the corpus was re-read rather than
reconciled. Here the **header detection** changed (`301cfdf`, merged the
same day the stale readings were taken), so the *parse* a reading is
shown changed.

**That is the promotion path, and it is a code change.** The brief
forbids one and instructs me to stop and report why. So: three validated
bands exist in isolation, and reaching production requires a ruling on
whether a header-detection change earns a schema bump — which is the
CTO's call, not this slice's.

**Manual copying was available and refused.** The isolated files are
schema-3 and would load if moved. That would discard five immutable
observations to make room for five better ones, outside any mechanism
the repository declares, and is exactly the act the brief names.

## 9. Falsification — no condition fired

| Condition | Result |
|---|---|
| current value differs from the source | **no** — every anchor byte-identical to production and to the parse |
| historical values differ from deterministic parsing | **no** — equality checked per reading, all 15 |
| row identity ambiguous | **no** — the parser's label at the anchor index equals the reading's, every time |
| periods inferred rather than explicitly carried | **no** — every header is a bare four-digit year the filer printed |
| semantic recognition changes across readings | **no** — readings 2–5 byte-identical to reading 1, all three companies |
| a component promoted as a total | **no** — checked against the filer's own arithmetic, §3 |
| existing current-period consensus regresses | **no** — six concepts × three companies, all `SAME` |
| the band appears through a changed rule | **no** — no code changed; `git status` empty; ruff and mypy clean |
| repeated readings shown as corroboration | **no** — zero occurrences of `independent`/`corroborat…`/`sources`/`observations` |

Suite: **2,721 pass**, with the seven crypto network failures and one
error that fail identically on `main` at `10f4904` — verified against
that commit's own CI run, and untouched by this change, which adds one
document.

## 10. Remaining UNKNOWN population

Production today, unchanged by this slice: **HIGH 3 · MEDIUM 4 · LOW 1 ·
UNKNOWN 16**, of 24 companies with statements.

If BQ13's three were promoted: **HIGH 4 · MEDIUM 4 · LOW 3 · UNKNOWN
13.**

The thirteen that would remain, by blocker:

| Blocker | Companies | Route |
|---|---|---|
| concept vocabulary (`NET_INCOME` and siblings) | KO, AXP, FITB, UNP, MTB, C, WMT's third factor | funded, after a vocabulary slice |
| question-contract mismatch (generic questions asked of banks) | COF, NWG, MUFG, BCS, DB, RF | parked; more readings would not help |
| header shape refuses the whole reading | HON | offline, unmeasured |
| extraction failure | C | funded |

**KO is in the same position as these three and for a related reason.**
BQ12's five readings also live in an isolated store, and its promotion
faces a *different* failure mode: KO's stale readings answer *no figure*
where the fresh ones answer with an anchor, so the two are genuinely
different answers and the outcome turns on which has the majority — five
against five is a tie, and a tie is unsettled. **That is an inference
from the consensus code, not a measurement**, and it should be measured
rather than assumed by whatever slice takes promotion on.

## 11. Recommended next slice — exactly one

**Rule on statement-store supersession, and if granted, implement it as
a schema bump.**

It is the only thing standing between four validated bands — ALL, TSLA,
WMT here and KO from BQ12 — and the investor. Nineteen readings have
already been paid for and are currently reachable by nobody.

- **What becomes better for the investor**: three companies stop
  reading *"1 of 3 factors answered — no band is claimed"* and start
  reading a band with its arithmetic beneath it, including two that band
  **LOW**. A dossier that says nothing about Tesla's quality is not
  neutral about it.
- **The mechanism**: `STATEMENT_SCHEMA_VERSION` 3 → 4, on the ground
  that `301cfdf` changed the parse a reading is shown — the schema-2
  argument, applied to header detection instead of the locator. The
  corpus then re-reads on the next funded `observe-statements`, through
  the ordinary action, with no file moved by hand.
- **What it costs**: the whole statement corpus re-reads. That is 24
  companies × 5 readings × the statements each holds, and the honest
  version of this recommendation is that the cost should be counted
  before it is authorised, not discovered afterwards.
- **What it must not become**: a repair to `_answer`. Adding the column
  header to the comparable form would also unblock this, and would
  change what agreement *means* for every stored consensus on the
  platform. That is a consensus-semantics change and deserves its own
  slice, its own measurement and its own ruling — it is recorded in §8
  precisely so it is not done quietly as a side effect of wanting a band.

**Not recommended yet**: widening `NET_INCOME` (parked, and it cannot
help until promotion works); HON's header defect; Citigroup; the
six-company question contract. Each is a separate attribution, and each
is downstream of a store that can receive a better reading.

## Scope compliance

`CONCEPT_LABELS` and `CONCEPT_WORDS` untouched · extraction code
untouched · deterministic parser untouched · consensus and quorum
semantics untouched · Business Quality questions, thresholds and
completeness untouched · financial-model selection untouched · no UI, no
crypto, no PR #145 · `NET_INCOME` not widened · HON, MTB, RF, KO, C,
AXP, FITB, UNP and every other company **not observed** · no production
observation created, mutated or deleted · **no code changed at all** —
this change is one document.
