# Does the equity dossier tell the investor what MOVRvest knows? — measured, and slice 1 built

**Status: research measured 2026-08-12 on the live API and the rendered
pages at F1 (`59a58c2`); slice 1 (§5.1) built 2026-08-13 as EF1 — see
§7. The remaining findings stay measurements, not mandates**
(Constitution §23–24). Every claim below was read from a live response,
a rendered page, a store, or the journal — never inferred from a class
name.

The question ruled on:

> Does the equity dossier visible to the investor faithfully expose the
> intelligence that MOVRvest now possesses and the evidence actually
> used by the Artificial CIO?

The test is not "is everything displayed?" It is: can the investor
understand what MOVRvest thinks, why, what it actually knows, what it
does not know, and what would change the case — without seeing
implementation architecture.

---

## 1. Method and corpus

Five real securities, chosen to exercise different paths — not to
demonstrate success:

| | Knowledge | Understanding | Grounded playbook | Statements | Financial model | Grounded quality | Decision (live) |
|---|---|---|---|---|---|---|---|
| **JPM** | 5/5 quorate | multi-engine | Diversified | IS+BS at quorum, 9 measures | GENERIC (5 Qs, 4 answered) | MEDIUM 62 | INVESTIGATE, `evidenced=False` |
| **DIS** | 5/5 quorate | multi-engine | Diversified | IS+BS at quorum, 9 measures | GENERIC (5 Qs, 3 answered) | HIGH 80 | RECOMMEND 76 |
| **NVDA** | 5/5 quorate | single-engine (manufacturing 100%) | Industrial | none | GENERIC | none | RECOMMEND 73 |
| **VOW3.DE** | 5/5 quorate | **refused** (segments+sizes known, earning-ways not) | RefusedGrounding | none | — | none | RECOMMEND 77 |
| **BNP.PA** (held) | 11 quorate | single-engine (services + spread) | **BANK** | none | **BANK** | none | PREPARE 71 |

Canonical layers were read through their own read-only doors
(`consensus_of`, `understand`, `select_grounded`,
`FinancialStatementService.established`, `measure`, `model_for`,
`answer_questions`, `quality_of`); dossiers via
`GET /executive/{symbol}/dossier` (6–12s each); pages via the rendered
HTML; history via `data/events/`.

---

## 2. What the dossier does well (measured, so nobody re-fixes it)

- **Both understandings reach the page with real provenance.** JPM's
  business understanding renders the engine, the archetype word, five
  segments with shares and earning mechanisms, and the narrowest
  agreement (3/5, unsettled). Its financial understanding renders nine
  measures where **a figure can be walked to a cell** — *"Net income"
  $57,048 over "Total net revenue" 182,447, under "2025" (Consolidated
  statements of income, table 0)* — and every absent measure carries its
  reason in the reading's own words (5 of 5 observations located no
  gross-profit cell).
- **The grounded quality score participates in the decision and says
  so.** JPM's 62 and DIS's 80 are `quality_of` over established
  figures; the basis names the filing, the question count, and the two
  honest exclusions — including the leverage note that explains the
  JPM-Diversified limitation unprompted.
- **VOW3.DE's refusal is rendered**: *"how it earns is not established —
  its segments and their sizes are"* appears on the page. An honest
  refusal reached the investor.
- **The frontend calculates nothing.** The page's only arithmetic is
  display formatting (`toFixed`, ×100 for percent). No banding, no
  thresholds, no recomputation. The #98/#120 rule holds.
- **Catalysts are real** (earnings dates per security), the equity/crypto
  shell split holds, and `synthesis.review_if` *can* carry established
  understanding — BNP.PA's reads *"how 'Investment & Protection
  Services (IPS)' earns settles differently — it stands at 7 of 10"*,
  which is exactly the right kind of sentence.

---

## 3. Findings, ranked by investor consequence

### F1 — The playbook the investor is shown is not the playbook the platform earned. **[misleading, severity 1]**

The dossier's playbook card is built from
`signals.research.playbook`, and `CompanyResearchService` selects via
`ResearchStrategyFactory` — the **industry-only** route over Yahoo
sector/industry. The grounded two-route selector
(`PlaybookSelectionService`, grounded first, labelled fallback) is
consumed only by the CLI. Measured on the corpus:

| | Grounded route (canonical) | Dossier card (investor sees) |
|---|---|---|
| BNP.PA (held) | **Bank** | **"Not classified"**, `classified: false` |
| DIS | Diversified Business | "General Corporate" |
| NVDA | Industrial | "Semiconductor" |
| VOW3.DE | refused, with the reason | "General Corporate" (industry) |
| JPM | Diversified Business | *(no card at all — reference symbol)* |

The worst of it: BNP.PA's card explains itself with *"The grounded
route needs an archetype established from the company's own filing,
**and none was**"* — a static sentence on the UNCLASSIFIED playbook
that is **false for this security**: the grounded route concluded Bank
from 11 quorate observations. The platform tells the investor its own
knowledge does not exist. This is a held position.

### F2 — The decision itself runs on the un-earned classification. **[stranded, severity 2]**

The research findings that reach `evidence_weighed`, the strengths and
risks, and the committee ledger are produced by the **industry**
playbook's analysts over provider data. VOW3.DE's RECOMMEND weighs
"General Corporate" analyst verdicts; BNP.PA is analysed as
unclassified though the platform concluded it is a bank. Grounded
intelligence reaches the decision through exactly one input —
`quality_of` — and through nothing else. So the dossier displays
grounded understanding the decision never consumed (#2), and the
decision consumes an industry classification the grounded layer has
superseded (#1). Two generations of the product are live inside one
decision.

### F3 — "Stable" over a three-state flap, and no *why* anywhere. **[misleading, severity 3 — BUILT 2026-08-13, see §9]**

The journal for VOW3.DE on **2026-08-09 alone** records
PREPARE (76) → INVESTIGATE (70, *"Business quality has not been
measured"*) → RECOMMEND (78) — a provider outage flipping the case
twice in five hours (the known Yahoo-401 shape). The dossier renders
`trend: "Stable — 5 consecutive reviews since 2026-08-09"` and
`conviction_change: null`. The journal holds the rationale of every
transition; the dossier tells the investor the case is stable and
never says what changed or why. The platform's top RECOMMEND carries a
stability claim its own history contradicts.

### F4 — What would invalidate the thesis is the risks list, verbatim. **[duplicated, severity 4]**

VOW3.DE's `invalidation_conditions` are byte-identical to its `risks`
(three provider-fed weakness findings), and `synthesis.review_if` is
empty for the RECOMMEND. "What would change this case?" is answered by
re-reading what is already weak — a fourth occurrence of the
identical-fields defect shape (`context_strengths`, `catalysts`,
`invalidation_conditions` account-level — and now
`invalidation_conditions ≡ risks`). BNP.PA proves the mechanism can do
better: where quorate understanding exists, `review_if` carries a real
established sentence.

### F5 — The financial model and its question set are developer-only. **[stranded, severity 5]**

`FinancialModel` and `answer_questions` — which questions this kind of
company is asked, which were answered from its own statements, which
are not yet answerable, which are refused — reach `movrvest financials`
and stop. JPM's dossier basis says *"over the 3 of 3 questions its
financial model could answer"* without naming the model or listing the
questions; BNP.PA **selects `FinancialModel.BANK`** and no surface the
investor can reach says so, nor that the bank model's questions await
the bank's own statements. The crypto dossier renders exactly this
layer (questions grouped by applicability); the equity dossier renders
none of it.

### F6 — The origin pill does not discriminate exactly where it should. **[misleading, severity 6]**

DIS's quality 80 is grounded (filing-derived, cell-addressed evidence);
NVDA's quality 80 is the provider triplet (large-cap + earnings +
dividend). Both cards read `kind: "assessment"` — *"Assessed against
this platform's bands"*. `FactOrigin` exists to keep the weaker claim
from borrowing the stronger's authority, and on the quality score —
the one score with two generations live — it labels both generations
identically. The distinction survives only in basis prose.

### F7 — An empty risks list reads as a clean bill. **[misleading, severity 7]**

BNP.PA — a held position, 28% volatility, 19.5% drawdown — renders
`risks: []` while VOW3.DE renders three. The absence is an evidence
gap (its provider fundamentals are partly unread, so the analyst
verdicts that produce risk findings never ran), but nothing on the
page separates *no adverse findings* from *the questions that would
find them were not answerable*. Meanwhile its strengths list is
populated from the same provider — the asymmetry compounds the
misreading.

### F8 — A committee abstains while its remit's findings sit on the same page. **[misleading, severity 8]**

DIS's Risk Committee: *"shown no finding in its remit, so it takes no
position"* — beside `evidence_weighed` carrying *"Annualised volatility
is 25.8%"*, *"Deepest fall 21.7%"*, and a safety score of 55 built
from exactly those findings. The same committee **speaks** on IB01.L
over identically-shaped findings. Not diagnosed here (research only);
measured and reproducible. Committee agreement then reads 100% — one
committee spoke, alone.

### F9 — Committee deliberation never touches established facts. **[stranded, severity 9]**

DIS's Investment Committee is *positive*, supporting: *"Forward P/E
below historical market average"*, *"Large-cap company"* — provider
findings. The filing-grade findings its own quality score displays
(net margin 14.2% at 5/5, cell-addressed) never enter the ledger the
committees deliberate over. `ASSESSMENT_CONVERGENCE.md` predicted this
("no committee assessment can warrant while every remit is
provider-fed"); it is now measured on the live surface.

### F10 — "No security-level analysis is available for JPM." **[misleading at the edge, severity 10]**

JPM — the most deeply known company on the platform (both statements
at quorum, nine measures, grounded MEDIUM) — renders that sentence as
its action *because*, `evidenced=False`, while the same page displays
the full grounded analysis and a grounded quality of 62 that
*participated in the score*. The sentence means "no provider evidence
was gathered" (JPM is reference corpus, not on the book) and asserts
"no analysis". Reference symbols are investor-reachable by URL; the
wording conflates provider absence with total absence.

---

## 4. The fidelity matrix

Layer by layer, the chain the ruling asked about:

| Layer | Dossier state | Note |
|---|---|---|
| Company Knowledge (consensus, width) | **present** | source + "consensus of 5 observations" + narrowest agreement rendered |
| Reader stability / observation spread | **correctly absent** | platform self-measurement, not an investor fact |
| Business Understanding (engine, segments, mechanisms) | **present** | with shares, mechanisms, refusal reasons |
| Archetype | **present** (inside understanding) | the word renders; the rule that decided is CLI-only (`movrvest archetype`) — acceptable |
| **Grounded playbook selection** | **stranded + misleading** | F1: industry card shown instead; false sentence for BNP.PA |
| Industry playbook + analyst coverage | present | but unlabelled as the fallback generation (F2) |
| **Financial Model + question set** | **stranded** | F5: developer-only; BANK selection invisible |
| Financial Understanding (measures, cells) | **present** | provenance walks to the cell |
| Grounded Business Quality | **present** | in the score card with honest exclusions |
| Provider signals (value/quality/momentum/risk) | present | but origin pill non-discriminating (F6) |
| Assessments → committee opinions | present | remit runs on provider findings only (F9); one abstention contradiction (F8) |
| DecisionEvidence (weighed, missing, scores) | present | absence semantics leak (F7, F10) |
| CIO decision + rationale | present | |
| **Thesis history / change / why-changed** | **stranded + misleading** | F3: journal knows; dossier says "Stable", `conviction_change: null` |
| Invalidation / next trigger | **duplicated** | F4: ≡ risks; review_if empty except from understanding |
| Duplicated generations on one page | **duplicated** | grounded quality beside industry playbook beside provider signals, unlabelled as generations |

---

## 5. §23 slice candidates

Only where the sentence completes. Ranked to match §3; none started.

1. **After this change, the investor can see the classification MOVRvest
   actually earned for a security** — a held bank reads *Bank* with the
   route that earned it, a refused grounding reads its refusal, and no
   card can assert the platform knows nothing where it knows something.
   (F1; the two-route selector already exists and is labelled.)
2. **After this change, the investor can see why the recommendation
   changed since they last looked** — which state it moved from, and the
   rationale of the transition — instead of a stability claim computed
   over the flap itself. (F3; the journal already records every
   transition with its rationale.)
3. **After this change, the investor can tell a score measured from the
   company's own filing apart from one assessed from provider proxies at
   a glance** — the origin pill discriminates where the two generations
   coexist. (F6; `FactOrigin` and the card `kind` field already exist.)
4. **After this change, the investor can see which questions this kind
   of company is asked, which its own statements answered, and which
   are not yet answerable** — the equity dossier gains what the crypto
   dossier already renders. (F5; `answer_questions` output already
   serialises in the CLI.)
5. **After this change, the investor can know what would actually
   invalidate the thesis rather than re-reading its current
   weaknesses.** (F4; the `review_if` mechanism already produces the
   right sentence where understanding is quorate.)

F2 (decision on the un-earned playbook) is deliberately **not** a slice
candidate here: rerouting the decision's analyst selection changes live
decisions and is a ruling of its own, on top of F1's visibility slice.
**Measured 2026-08-13**
([`DECISION_CONVERGENCE_MEASUREMENT.md`](DECISION_CONVERGENCE_MEASUREMENT.md)):
the side-by-side counterfactual moved no score, committee, conviction
or decision anywhere in the corpus — the convergence gap is labels and
applicability, not decisions — so F2's rerouting half is *not*
justified today, and this document's slice 1 remains the whole of the
investor-facing value.
F7–F10 are wording/consistency defects a slice above would either
absorb or expose for individual repair.

## 6. Traps recorded for whoever builds

- The UNCLASSIFIED playbook's `explanation` is a static string that
  asserts *both* routes failed; any surface that renders it inherits
  the claim regardless of what the grounded route knows. *(Repaired in
  EF1: the sentence now speaks only for the industry route.)*
- `trend.stated` counts consecutive same-state reviews and words it
  "Stable"; a day containing three states reads as day one of
  stability by the evening.
- The DIS Risk-Committee abstention (F8) reproduces on the live API;
  diagnose the remit/ledger dimension attribution before touching
  committee code.
- JPM renders no playbook card at all (reference symbol, no watchlist
  item) — a fourth card state beside grounded/industry/unclassified
  that any playbook slice must handle.
- Dossier latency measured 6–12s per symbol on this machine (brain
  pipeline); an audit that hits five dossiers should expect a minute.

---

## 7. EF1 — Industry + Earned Archetype Visibility (built 2026-08-13)

Slice 1 above, accepted and built. The product model it implements is a
correction to F1's framing: **industry and business archetype are not
competing classifications.** Industry answers *where does this company
operate, as the market files it*; the earned playbook answers *what kind
of economic business has this platform established, and therefore which
analysis applies*. Both are useful; the defect was substitution, not
coexistence.

### What the dossier now carries

`GET /executive/{symbol}/dossier` gains `classification` — null where
the subject is not a company — with three parts, every visible sentence
backend-authored:

- **`industry`** — the provider's own `industry`/`sector` strings from
  the stored fundamentals door (`CachedValueProvider.stored()`), dated
  with the moment they were read. Two absences kept apart: *"None
  reported"* (the profile was read and names no industry — BNP.PA) and
  *"Not acquired"* (no profile held; acquisition is explicit and a page
  view performs none — JPM).
- **`playbook`** — the grounded route's answer, from `select_grounded`
  over the `BusinessUnderstanding` the route already composes through
  the read-only door. Exactly one of three states: **established**
  (name, the rule's own reasoning, and what the conclusion rests on),
  **refused** (the route's refusal verbatim — sub-quorum states the
  count, an undecided archetype carries `undecided_because`), or
  **unavailable** (the store door's absence sentence). No industry
  string can reach this half, and no state serves a default.
- **`distinction`** — one sentence separating the two concepts, worded
  once by the backend.

The definition split its heading: `classification_heading`
("Classification") now heads this section, and the analyst-coverage card
is headed by the new `analysis_heading` ("How this security is
analysed") — so "General Corporate" and "Semiconductor" read as what
they are, the analysis frame the industry route chose, never as a
classification this platform earned. The UNCLASSIFIED playbook's static
explanation was rewritten to speak only for the industry route (the
false half of the old sentence was this document's first trap).

### The live corpus at build time

| | Industry | Investment playbook |
|---|---|---|
| VOW3.DE | Auto Manufacturers (Yahoo, dated) | **refused** — the engine's 33%-coverage sentence, verbatim |
| JPM | Not acquired (reference symbol) | **established — Diversified Business**, resting on 4/5 |
| BNP.PA | None reported (read, provider names none) | unavailable — schema-11 observations restore as absent |
| DIS | Entertainment | unavailable — same |
| NVDA | Semiconductors | unavailable — same |
| CAT | Not acquired | unavailable — same |

BNP.PA/DIS/NVDA/CAT are unavailable **solely because funded
current-schema re-observation has not happened** (`movrvest observe
SYMBOL --to 10` once credits exist); the same production path exposes
them with no code change — proven by canonical fixtures
(`tests/test_dossier_classification.py`): the manufacturer shape reads
*Industrial*, the diversified shape *Diversified Business*, the bank
shape *Bank*. Archived schema-11 knowledge is not resurrected through
any side door.

### Visibility, not routing

The displayed classification reroutes nothing — no `ResearchPlan`,
analyst, `FinancialModel`, score, committee, conviction or CIO
recommendation. Proven behaviourally at the wire: one test serves two
dossiers over an identical brain, flips the grounded conclusion from
absent to authoritative Bank, and asserts every decision field
byte-identical. The decision-convergence measurement
([`DECISION_CONVERGENCE_MEASUREMENT.md`](DECISION_CONVERGENCE_MEASUREMENT.md))
stands: **re-run the convergence comparison when a company with an
established specialised archetype — BANK first, BNP.PA the priority —
reaches financial-statement quorum for the specialised question set.**
Until that evidence gate passes, the two analytical routes coexist by
ruling, not by endorsement; the intended destination remains evidence →
knowledge → understanding → earned archetype → playbook → questions →
assessments → committees → CIO.

### Recorded, not solved

- The store door's absence sentence ("No filing has been read for
  BNP.PA") does not distinguish *never read* from *read under an older
  contract and deliberately restored as absent*. The state is honest;
  the vocabulary is the knowledge layer's to sharpen, not this
  surface's.
- The narrative slot renders a provider's raw 429 as its absence text
  (pre-existing, writer seam, flagged separately).
- F2–F10 remain measured and unbuilt.

---

## 9. F3 — Why the recommendation changed (built 2026-08-13)

Slice 2 of §5, built under a zero-credit constraint: every input is a
record the platform already wrote, so nothing here needs model access.

### The defect, live

VOW3.DE rendered **"Stable — 6 consecutive reviews since 2026-08-09"**
with `conviction_change: null`. Its own journal holds fourteen reviews
and **eight state changes**, three of them on 2026-08-09 itself:

| recorded | state | conviction | quality | valuation |
|---|---|---|---|---|
| 15:32 | PREPARE | 76 | 62 | 80 |
| 17:36 | **INVESTIGATE** | 70 | **—** | **—** |
| 20:45 | RECOMMEND | 78 | 80 | 80 |

The stability claim was dated to the day the case moved twice, and the
cause of the middle move — two scores that stopped being measurable —
was recorded and never shown.

### What was built

- **`DecisionCourse` / `RecordedTransition`** (`app/domain/decision_history.py`):
  every state change composed from two adjacent journal records, most
  recent first, each carrying the rationale the CIO **recorded at the
  time**, verbatim, and the scores that differed.
- **`trend_against` no longer dates a calm that did not hold.** Where
  the record contains changes, the sentence counts them —
  *"RECOMMEND across the last 6 reviews — the case changed 8 times
  before that"*. Where the run **is** the whole record, "Stable — N
  consecutive reviews since DATE" is honest and is kept (JPM).
- **`decision_course` on `GET /executive/{symbol}/dossier`**, composed
  from the history the Brain already perceived for the cycle — no store
  opened, no fetch, no model.
- **A page section** under *What changed*, rendering the backend's
  sentences and computing no delta.

### The rules the wording keeps

- **A score that stopped being measurable is not a score that fell.**
  *"Business quality could no longer be measured (it was 62)"* — never a
  zero, never a deterioration. A provider outage is not a worse
  business, and a test asserts no such line anywhere in the journal ever
  contains "fell" or an arrow.
- **A whole missing score set is one silence, not five findings.** Where
  either record predates the journal keeping scores the transition is
  `unexplained` and `moved` is empty — the first draft enumerated five
  scores "measured again", which turned one absence into a list.
- **A first review is an absence, not a trend.** It renders the reason,
  never "Stable".
- **The rationale is quoted, never re-authored.** Nothing here writes a
  sentence now about a decision taken then.

### Measured, before → after

| | before | after |
|---|---|---|
| VOW3.DE trend | "Stable — 6 consecutive reviews since 2026-08-09" | "RECOMMEND across the last 6 reviews — the case changed 8 times before that" |
| DIS trend | "Stable — 6 consecutive reviews since 2026-08-09" | "…the case changed 7 times before that" |
| JPM trend (never changed) | "Stable — 4 consecutive reviews since 2026-08-09" | **unchanged** |
| course | absent | VOW3.DE 14 reviews / 8 changes; DIS 13/7; JPM 3/0 |
| **decision fields** | | **0 differences** across VOW3.DE, DIS, JPM |

Decision-neutrality is also held by a wire-level test that swaps the
journal beneath an identical brain and asserts every decision field
byte-identical.

### Recorded, not fixed

`JsonEventRepository` defaults to the path literal `data/events`, which
`conftest.py`'s hermetic root cannot redirect — the
[`HERMETIC_EVIDENCE.md`](HERMETIC_EVIDENCE.md) shape. This slice
declared the path in its own tests rather than changing the production
default, which is a separate ruling.
