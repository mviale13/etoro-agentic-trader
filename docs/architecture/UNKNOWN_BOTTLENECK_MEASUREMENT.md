# Thirteen UNKNOWNs, and not one of them is short of evidence

**Status: research, BQ18. Read-only over held evidence. No model call,
no acquisition, no production write, no rule or threshold change.
Stopped for ruling.**

The question was whether the UNKNOWN population is one acquisition
problem or five unrelated conditions. It is neither.

> **Zero of the thirteen are primarily acquisition problems.** Every one
> is blocked first by something this platform decides, not by something
> a filer failed to print — vocabulary, a question contract, a parser,
> or a consensus tie.
>
> **Goldman Sachs and JPMorgan are banks and both band.** They print
> `Total net revenues` and `Total net revenue`; Barclays and NatWest
> print `Total income`; American Express prints `Total revenues net of
> interest expense`. The first two are in `CONCEPT_LABELS` and the
> others are not. **Neither GS nor JPM prints a gross profit either** —
> their profitability rides on net margin. The belief that banks are
> structurally unassessable under the generic model is false, and it was
> hiding a lexical gap.
>
> **Four refused top lines reconcile exactly to the filer's own
> components** — BQ11's arithmetic standard, met four times without a
> single judgement call.

---

## 1. Baseline — and it does not match the brief

**Production today is `HIGH 3 · MEDIUM 4 · LOW 1 · UNKNOWN 16`, not
`4 · 4 · 3 · 13`.**

The difference is not drift and nothing is wrong: **the BQ16 production
import was never performed.** It was forbidden in that brief (*"Do not
promote into production during BQ16"*), the operator was proven against
copies only, and the write remains a named, unexecuted next action.
`4 · 4 · 3 · 13` is the *simulated post-promotion* aggregate.

Reproduced exactly, by applying the three artifact sets through
`statement-import` on a copy:

| | production today | after the pending import |
|---|---|---|
| HIGH | 3 — DIS, GS, TRV | **4** — + ALL |
| MEDIUM | 4 — AAPL, CB, JPM, PG | 4 |
| LOW | 1 — MET | **3** — + TSLA, WMT |
| UNKNOWN | **16** | **13** |

The three extra UNKNOWNs in production are ALL, TSLA and WMT, whose
remedy is already measured and waiting. **Everything below is the
brief's 13**, so the numbers are comparable; where production differs it
is only by those three.

## 2. The taxonomy, as the failure paths produced it

Every UNKNOWN traced from held observations through consensus,
`FinancialUnderstanding` and the three quality factors, and classified
on its **first decisive** blocker. Four classes emerged; none of the
brief's candidate labels survived unchanged.

### V — the filer prints a consolidated top line and the vocabulary refuses it (5)

`UNP · AXP · C · BCS · NWG`

| Company | Printed, refused | Reconciles to the filer's own components |
|---|---|---|
| UNP | `Total operating revenues` 24,510 | 23,220 + 1,290 = **24,510 exact** |
| AXP | `Total revenues net of interest expense` 72,229 | 54,865 + 25,598 − 8,234 = **72,229 exact** |
| C | `Total revenues, net of interest expense` 85,225 | 25,433 + 59,792 = **85,225 exact** |
| BCS | `Total income` 29,140 | 14,501 + 7,498 + 7,042 + 10 + 89 = **29,140 exact** |
| NWG | `Total income` 16,641 | components printed; not re-derived here |

**UNP is the cleanest case in the corpus and is not a bank at all** — a
railroad whose top line is refused on phrasing alone. It already answers
earnings growth, and its stored readings carry **dated three-cell rows**
for operating income and net income, so establishing `total_revenue`
would give it operating margin, net margin *and* revenue growth: **3 of
3 answered.**

### S — the filer prints no consolidated revenue line at all (6)

`COF · DB · FITB · MTB · MUFG · RF`

Every one prints `Total interest income` and `Total non-interest income`
as separate subtotals and never combines them; MUFG prints four bare
rows labelled `Total`. There is no top line to accept, so this is
**not** a vocabulary gap: a combined figure would be this platform's
arithmetic rather than the filer's, which invariant 1 forbids. The
generic model's revenue and gross-margin questions are the wrong
instrument for these six, and the right one — a bank financial model —
is blocked behind the accepted Prudential boundary.

### P — the parser cannot head the columns (1)

`HON`

Profitability answers **strong**; both growth factors fail on *"the row
prints no earlier period this platform can date."* Today's parse finds
`Net sales` and `Net income` at the right rows and returns **zero**
headed figures, because `header_row` settles on a row labelling only
column 0. BQ15 ruled these readings UNDECIDABLE and kept their
authority, which is why HON has a profitability answer at all.

### T — two contracts deadlocked in one consensus (1)

`KO`

Ten active readings: five stale answering *no figure located* for
`total_revenue`, five promoted answering `Net Operating Revenues`
47,941. Five against five is no majority, so the claim is unsettled and
every margin loses its denominator. `gross_profit` agrees **10 of 10**
and `net_income` is a second vocabulary case (`Consolidated Net Income`,
refused).

### A second axis: three have no authoritative income reading

`C · MTB · RF` — BQ15's audit withdrew all five income readings from
each. They need re-observation *before* anything else can be judged, and
re-observation alone leaves MTB and RF exactly where they are (class S).

## 3. Acquisition or reasoning

| | Companies | n |
|---|---|---|
| **Reasoning is the first decisive blocker** | all thirteen | **13** |
| Acquisition is the first decisive blocker | — | **0** |
| *Additionally* need re-observation before anything can change | C, MTB, RF | 3 |

**No UNKNOWN in this corpus lacks evidence.** In every case the filing
is held, located and parsed; what stops the answer is a decision this
platform makes about that evidence. For the six in class S the *filer*
prints no such figure — but that too is a reasoning outcome, because the
platform is asking a question its own boundary document says does not
apply to them.

**Would currently held evidence suffice under different downstream
reasoning?** For classes V and T, **yes** — with one caveat that is the
whole of BQ17: a stored observation that recorded an absence keeps
recording it. Widening the vocabulary cannot retroactively rescue a
stored absence, by design. So held evidence is *sufficient in the
document* and *insufficient in the store*.

## 4–5. Leverage

| Company | Current evidence | First decisive blocker | Acq. or reasoning | Fresh observation? | Smallest likely remedy |
|---|---|---|---|---|---|
| **UNP** | 5 income, quorate, earnings answered, dated rows | vocabulary refuses `Total operating revenues` | reasoning | **necessary, not sufficient** | 1 label + re-observe |
| **AXP** | 10 (income+BS), quorate, earnings answered | vocabulary refuses `Total revenues net of interest expense` | reasoning | necessary, not sufficient | 1 label + re-observe |
| **NWG** | 5 income, quorate, earnings answered | vocabulary refuses `Total income` | reasoning | necessary, not sufficient | 1 label + re-observe |
| **BCS** | 5 income, quorate, 0 answered | vocabulary refuses `Total income` **and** net income | reasoning | necessary, not sufficient | 2 labels + re-observe |
| **C** | 5 income **all superseded** | superseded; then vocabulary; then a live extraction defect (net income reads EPS `$ 7.11` under header `1,832.0`) | reasoning ×3 | necessary, not sufficient | parser + labels + re-observe |
| **KO** | 10 income, 5 stale vs 5 fresh | consensus tie between two contracts | reasoning | **likely sufficient** — a sixth fresh reading is 6 of 11, a majority | 1 reading, or supersede the stale five |
| **HON** | 5 income, quorate, profitability answered | parser heads no column on that table shape | reasoning | **irrelevant** — BQ8 measured the reading refused whole | header detection |
| **COF, DB, FITB, MTB, MUFG, RF** | quorate (MTB, RF superseded) | filer prints no consolidated revenue line; generic model is the wrong instrument | reasoning | **irrelevant** | a bank financial model (blocked by the Prudential boundary) |

**Aggregated by blocker:**

| Blocker | Companies | Credit to fix | Credit to realise |
|---|---|---|---|
| **total-revenue vocabulary** | **5** | none | yes — re-observation |
| question contract (no top line printed) | 6 | none | n/a — needs a ruling first |
| parser header detection | 1 | none | yes, to validate |
| consensus tie | 1 | none | 1 reading |

So: **not 8 of 13 as one acquisition problem, and not five unrelated
conditions.** It is **two structural blockers covering 11 of 13** —
vocabulary (5) and question contract (6) — plus two singletons.

## 6. The controls, and what they expose

Not re-audited; used to answer two questions.

**What is the minimum escape path?** All eight banded companies answer
**all three** factors. Every one holds `total_revenue` *and* `net_income`
with dated rows. None needs gross profit:

| | top line | net income | gross profit |
|---|---|---|---|
| GS (HIGH) | `Total net revenues` | `Net earnings` | **none printed** |
| JPM (MEDIUM) | `Total net revenue` | `Net income` | **none printed** |
| CB, TRV, MET | `Total revenues` | `Net income` | — |

**Profitability needs only one of its three margins, and net margin
needs only the top line over the bottom line.** That is the whole escape
path.

**Is an UNKNOWN holding equivalent evidence and failing structurally?**
**Yes — four of them, and this is the finding.**

| Escapes | Blocked | Difference |
|---|---|---|
| GS `Total net revenues` | BCS `Total income` | phrasing |
| JPM `Total net revenue` | NWG `Total income` | phrasing |
| CB/TRV `Total revenues` | AXP `Total revenues net of interest expense` | phrasing |
| — | UNP `Total operating revenues` | phrasing |

Same statement shape, same evidence quality, same arithmetic
checkability — **different lexical luck.** The banks that band are not
better documented; their filers happened to choose a form already in the
list. That is a reasoning defect wearing an acquisition deficit's
clothes, and it is exactly what §6 was asked to look for.

## 7. Recommended next slice — one

**Widen `TOTAL_REVENUE` under BQ11's arithmetic standard, then re-observe
the specimens it unblocks.**

- **The defect**: `CONCEPT_LABELS` covers `Total net revenue(s)` and
  `Total revenues` but not `Total operating revenues`, `Total income`,
  or `Total revenues net of interest expense` — four forms that name the
  same consolidated figure and that the filer's own components
  reconcile to exactly.
- **Addresses directly: 5** — UNP, AXP, NWG, BCS, C. Of these, **UNP,
  AXP and NWG are expected to band on one label each**, because each
  already answers earnings growth and holds dated rows; BCS needs a
  second label; C needs its extraction defect resolved first.
- **Credit**: the widening and its falsification are **free**. Realising
  a band requires re-observation — see §8.
- **Before → after**: UNKNOWN 13 → **10** on the conservative reading
  (UNP, AXP, NWG), 13 → 8 if BCS and C follow. UNP is expected to answer
  **3 of 3**.
- **Deliberately unresolved**: the six with no printed top line (the
  bank financial model stays blocked behind the Prudential boundary),
  HON's parser, and KO's tie. It also does not touch the pending BQ16
  production import, which is a separate authorised write.

**Run it exactly as BQ11 was run**: offline falsification across all 24
first — every candidate form checked against every filing for a false
positive, and accepted only where the filer's own arithmetic
reconciles — and paid readings only if the offline stage earns them.

## 8. API credit — is funding now imperative?

# YES

Not because analysis has run out — §7's offline stage is real work that
must happen first — but because **the next slice cannot be *validated*
offline, and the reason is a guarantee this platform deliberately
built.**

BQ17 made producing-contract provenance immutable: a stored observation
records the vocabulary it was read under and is never reinterpreted. So
a widened `CONCEPT_LABELS` **cannot** rescue UNP's stored *"no figure
located"* — that absence is a true statement about a narrower contract
and will remain one forever. The only way a label change becomes a band
is a fresh reading under the new contract. **Every one of the five in
class V is in this position**, and so is KO's tie, which needs a sixth
reading or a supersession ruling.

**What cannot be performed without credit**: proving that a vocabulary
entry actually moves a company from UNKNOWN to a banded assessment. The
label's *correctness* is provable offline — the arithmetic already
reconciles four times. Its *effect* is not.

**Minimum useful acquisition scope: UNP, 5 readings** (one income-
statement quorum). It is the cleanest specimen in the corpus: not a
bank, so no question-contract confound; one unambiguous printed total
reconciling exactly; earnings growth already answered; dated rows
already held. If UNP does not band on those five readings, the
hypothesis is wrong and nothing further should be funded.

**What remains possible offline, and should be done first regardless**:
the full 24-company falsification sweep for the candidate forms; the
counterfactual measuring which companies each form would unblock; HON's
header-detection repair and its corpus measurement; and the KO
supersession ruling. None of these needs a credit.

## 9. Purity

No production write · no promotion · no re-observation · no model or API
call · no quality rule, threshold, vocabulary or UI change · every
figure above read from held evidence, the already-acquired filings and
the platform's own deterministic parser · the promotion simulation ran
on a temporary copy and `git status --porcelain data/` is empty.
