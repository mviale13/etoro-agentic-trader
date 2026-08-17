# A right answer to a question the fact no longer takes

**Status: built, BQ27. No model call, no acquisition, no production write,
no vocabulary, schema or fingerprint change. The 15 preserved BQ26
observations are not appended. Stopped for ruling.**

> **The regression, pinned before anything changed.** Combining Goldman's
> five production readings with BQ26's five natives: one physical fact —
> `Total net revenues` 58,283 at t0 r12 c3 under "2025", the identity
> checked field by field — assigned to `TOTAL_REVENUE` by the old five and
> to `REVENUE_NET_OF_INTEREST_EXPENSE` by the new five. Mixed:
> `majority=False`, `refused=None`. The 5-vs-5 tie, and BQ23's refusal
> gone. JPMorgan identical at 182,447; AXP clean (`majority=True`, no
> collision) — the control.
>
> **The repair: a positive assignment stops voting for a concept where a
> later native reading — asked about both concepts — assigned the same
> physical fact to a mutually exclusive concept on the statement's own
> evidence.** Derived on read, nothing written, six proof obligations, and
> a single miss keeps the assignment voting.
>
> **The headline measurement: GS's and JPM's `total_revenue` surface is
> byte-identical before and after the simulated append.** Same REFUSED
> standing, same sentence, same net-margin reason. The append stops
> costing anything.

---

## 1. The exact regression (§1)

Measured on copies before the rule existed:

| | old assigns | new assigns | same physical fact? | mixed result |
|---|---|---|---|---|
| **GS** | `Total net revenues` 58,283 @ t0 r12 c3 → `total_revenue` | same cell → `revenue_net_of_interest_expense` | **True** (cell, label, printed, value, header all equal) | `located=False refused=None majority=False` — 5× located vs 5× *no figure* |
| **JPM** | `Total net revenue` 182,447 @ t0 r15 c3 → `total_revenue` | same cell → new concept | **True** | same tie |
| **AXP** | *(no positive ever)* | r17 → new concept | n/a | `majority=True` — no collision, the control |

The loss is not the band (UNKNOWN either way) but the account: BQ23's
*"constructed from net interest income"* dissolved into *"unsettled across
10 readings"*.

## 2. The formal rule (§2)

`app/domain/assignment_supersession.py`. A historical positive assignment
of physical fact F to concept A loses its vote for A only where **all
six** hold:

1. another stored observation establishes **the same physical fact F**
   (`same_reported_fact`, §3 below);
2. that observation assigns F to a **different concept B**;
3. A and B **both** declare semantic qualification rules — membership in
   `GOVERNED`, the same table BQ23 and BQ25 read;
4. those rules are **mutually exclusive for this occurrence** — one marker
   concept, opposite requirements;
5. the deciding evidence is **in the statement itself**, read by the
   superseding observation: its own established marker, judged through the
   same `refusal_for` every consensus runs — A refuted *and* B supported;
6. the superseding observation is **native to both questions** — stamped
   `produced_under` for A *and* B, so declining A was an arbitrated choice
   and never ignorance.

No company, no banking, no label text, no enum order, no recency, no score
— pinned by the AST scan (docstrings stripped, word-boundary company
match) and by an order-independence test on both the fixture and the live
ten.

**§3 is honored structurally**: what today's extractor *would* choose is
never evidence. Five old positives alone stay ACTIVE — pinned — even
though today's code, replayed, would classify the row differently. A
stored observation must exist that made the assignment, was asked both
questions, and read the deciding evidence. A parser improvement supersedes
nothing by itself.

## 3. The physical-fact identity (§4)

Five conjuncts, all read from **checked anchors** — figures this platform
read back out of the document at observation time:

| conjunct | what it fixes |
|---|---|
| `cell` (table, row, column) | the address — one table is one scale, one column is one period, one row is one line |
| `label` | what the filer calls the row, so a drifted parse cannot alias two lines through a shared address |
| `printed` | the content as typeset |
| `value` | the content as a number — required and **never decisive alone** |
| `column_header` | the period, in the filer's own words |

Two unrelated rows printing the same number fail on the cell; the same
cell re-read at a different value fails on the value; the same row in
another year's column fails on the header. Each is a pinned control.

## 4. GS and JPM, before → after (§§5–6)

On the mixed ten (production + preserved), under the rule:

| | before the rule (BQ26's measurement) | after |
|---|---|---|
| `total_revenue` | unsettled 5-vs-5, `refused=None` | **REFUSED — constructed from net interest income**, `withdrawn_assignments=5`, `unlocated_because=None` |
| its figure | lost to the tie | **carried** — 58,283 / 182,447, with the marker that disproves it |
| new concept | located, majority, 5/5 | unchanged — located, majority |
| net income | 10/10 | **10/10 — the withdrawn readings still vote it** |
| net interest income | 10/10 | **10/10** |

**The composition (§6), and why there is one reason rather than two.** The
withdrawal leaves five entitled voters, all recording the arbitration
absence — so the claim settles as absent. The second consensus pass then
notices: an assignment was withdrawn *and* the mutually exclusive
sibling's figure is settled in this same consensus — exactly the evidence
that withdrew it — and carries **BQ23's own refusal of that settled
figure**, built by the same `refusal_for`, wording included. The surviving
voters' arbitration sentence says the same thing and yields to it;
`unlocated_because` is cleared so the refusal is the one reason.

The guard is the withdrawal itself: **a genuine tie is never masked**.
Five old positives against five *unstamped* later readings withdraw
nothing, settle nothing, and render as honestly unsettled — pinned.

Measured end to end on the simulated append: **GS's and JPM's
`total_revenue` line and net-margin sentence are byte-identical before and
after.** The refusal survives the append exactly.

## 5. AXP (§7)

No historical positive → no rulings → `withdrawn_assignments=0`, refusal
`None`, absence settles 10 of 10, wording strictly improves, new concept
gains majority. The rule never touches it — pinned.

## 6. The negative controls (§7)

| control | result |
|---|---|
| five old positives alone (production's state) | **ACTIVE** — no stored superseder, nothing superseded |
| materially different value at the same cell | **ACTIVE** — not the same fact; the conflict stays visible |
| same number, different row | **ACTIVE** — figure equality never triggers |
| same row, different period header | **ACTIVE** |
| same cell assigned to `GROSS_PROFIT` (no qualification rule) | **ACTIVE** — and a concept with no rule returns *no rulings at all* for its own positives |
| superseder stamped only for B, only for A, or unstamped | **ACTIVE ×3** — not native to both questions |
| superseder without the marker fact | **ACTIVE** — the deciding evidence must be in the statement it read |
| marker printed **below** the fact | **ACTIVE** — the structure supports neither reassignment; an assignment moved by lexical or ordering accident withdraws nothing |
| unrelated concept's contract changed (`premium_revenue` stamped `feedfacefeedface`) | **no effect** — still SUPERSEDED on its own six obligations |
| observation order reversed (fixture and live ten) | **identical rulings** |
| genuine 5-vs-5 with unstamped later readings | **stays a tie**, worded *unsettled*, never refused |

## 7. Interaction with BQ20 and BQ23 (§8)

Three authority rules, deliberately unmerged, one proof shape each:

| | acts on | the proof is about | evidence |
|---|---|---|---|
| **BQ20** `absence_supersession` | a historical **absence** | what a reader *could see* | the producing contract's bounded forms |
| **BQ23** `financing_cost_refusal` | a settled **positive** | what a figure *is* | the statement's own typesetting |
| **BQ27** `assignment_supersession` | a historical **assignment** | *which question a fact answers* | a later native reading plus mutually exclusive semantics |

They share infrastructure where sharing is honest — all three are derived
on read, concept-local, byte-preserving, and reported beside the agreement
(`withdrawn_absences` / `withdrawn_assignments` / `refused`) — and share
no logic, because the proof obligations differ. `_fact_consensus` composes
the two vote filters by position; the second `_refused` pass composes the
presentation. BQ27's semantic judgment is *delegated* to BQ23's
`refusal_for` rather than duplicated, so the two can never drift apart.

## 8. The simulated 15-reading append (§9)

Applied through the normal importer to a **copy**; production opened
read-only, md5 compared. None of it hard-coded — the test suite derives
the same outcomes from the live corpus.

| expectation | result |
|---|---|
| 15 appendable | **15 appended** |
| incompatible / unproven | **0 / 0** |
| GS new concept | **majority** (58,283, addressed 5/10) |
| JPM new concept | **majority** (182,447) |
| AXP new concept | **majority** (72,229) |
| GS/JPM historical `TOTAL_REVENUE` assignments | **cease voting** (`withdrawn_assignments=5` each) |
| BQ23 semantic refusal | **available and rendered** — same standing, byte-identical sentence |
| generic profitability | **not restored** — no consumer exists; GS and JPM answer one factor and no band is claimed |
| quality aggregate | **HIGH 3 · MEDIUM 4 · LOW 3 · UNKNOWN 14**, before and after |
| production md5 | unchanged |

## 9. History, provenance, gates (§§10, 13)

- Derived on read; a test re-reads GS's five production observations after
  the derivation and asserts byte equality, the anchor intact, and
  `produced_under` still `()`.
- `TOTAL_REVENUE` = `ea9df9c5adbc7f44` · `REVENUE_NET_OF_INTEREST_EXPENSE`
  = `3e077c247f109a37` · schema 3 · no `vocabulary_contracts` update · no
  backfill — pinned.
- The rule is **inert on production**, checked across the whole corpus:
  no consensus of any company withdraws an assignment today, because
  obligation 1 cannot be met until the natives are appended.
- **2,882 pass** (2,861 before, +21) · ruff check and format clean · mypy
  clean, 595 files · `git status --porcelain data/` empty.
- One surface change: `movrvest statements` prints a one-line note beside
  a refusal where assignments were withdrawn, so a 5-of-5-with-5-withdrawn
  never reads as 5-of-5 outright.

## 10. Recommended production action (§11)

**Append the complete GS/JPM/AXP batch — all fifteen preserved BQ26
observations — through the ordinary importer, as the next ruling.**

BQ26's only reason to hold was that the append spent Goldman's and
JPMorgan's truthful refusal. That cost is now measured at zero: the
refusal survives the append byte-for-byte, the new concept reaches
majority for all three filers, every anchor the old readings hold keeps
voting, no band moves, and nothing is written that isn't already proven
compatible on its own native stamps. The specimens are durable at
`data/experiments/statement-observations/bq26/statements/` (md5
`8bd5604939fb8731d3bd2f9b386d2001`) and need no re-acquisition.

The write itself is not performed here, per the production gate.

## Recorded, not solved

- **`_carried_refusal` reports the sibling's settled figure**, which for
  the live pair is the same printed fact the withdrawn readings anchored.
  If a future sibling pair could settle a *different* figure than the one
  withdrawn, the refusal would name the settled one — correct, and worth
  knowing.
- **The superseder search is O(n²) per governed concept** over one
  statement's observations. At quorum scale (≤ tens) this is nothing;
  a corpus with hundreds of readings per statement would want an index.
- **`withdrawn_assignments` is not rendered on the dossier**, only on
  `movrvest statements` and in the domain. The dossier consumes
  `absent_because`, which carries the right sentence.

## Scope compliance

No model or API call · no new readings · BQ23 and BQ25 semantics unchanged
· no vocabulary change · BANK not activated · no profitability consumer ·
BCS/NWG excluded · COF/FITB/HON/KO/DB/MUFG untouched · the 15 preserved
observations not appended · production bytes, fingerprints and schema
unchanged.
