# Does MOVRvest know enough to decide, even though it does not know everything?

**Status: research, DV1. Measurement of the live product after #178. No
model call, no re-observation, no production write (`git status
--porcelain data/` empty after every capture; the Executive Writer and
the intelligence synthesis were forced off for the runs). Stopped for
ruling.**

> **The product's own pages answer the governing question, and the answer
> is uncomfortable in a specific, repairable way.** For three equities the
> decision cites almost none of the evidence the same page displays — and
> for two of them the sentence that holds the case back (*"Quality data is
> unavailable"*) is printed beside a grounded quality band derived from
> the company's own audited filing. Four other equities collapse to one
> identical sentence and one identical conviction number — **64, with the
> rationale "there is nothing to base a decision on"** — whatever their
> evidence. And the two digital assets have the richest honest evidence on
> the platform and **no decision sentence at all**, while a second live
> surface still scores Bitcoin 46 from non-crypto evidence.
>
> The architecture has not made *analytical completeness == permission to
> decide*. It has made something subtler: **the permission to decide reads
> one narrow evidence set (the provider-fed signals), while the evidence
> the platform actually trusts — grounded bands, statements, committees —
> is displayed beside the decision and consumed by none of it.**

Panel: AAPL, DIS, UNP, JPM, HON, KO via `/executive/{s}/dossier`; BTC,
ETH via `/crypto/{s}/dossier`. Production evidence only, one server run,
writer off.

---

## 1. The raw product answers

### AAPL — PREPARE · conviction 60 (Moderate) · agreement 1.0

- **action**: *"Wait before opening AAPL. The case is credible but not yet actionable."*
- **because**: "Dividend-paying business." · "Deepest fall over the past year was 13.8%."
- **despite**: none — *"No adverse finding was recorded…"*
- **review if**: *"Quality data is unavailable for AAPL. Measuring it is what would let this case progress."*
- **and on the same page**: `scores.quality = 62` — *"1 favourable of 3 answered → 33% → MEDIUM → 62 … from 10-K 0000320193-25-000079"*
- catalysts: earnings in 73 days. invalidation_conditions: **empty**.

### DIS — PREPARE · conviction 74 (High) · agreement 1.0

- **action**: *"Continue holding DIS. Nothing supports adding yet."*
- **because**: positive earnings · dividend · *"Cash flow is excellent — OCF $17.0B, FCF $4.9B."*
- **despite**: *"Growth is declining — earnings growth is −48.3%."* (also the sole invalidation condition)
- **review if**: *"Quality data is unavailable for DIS."* — beside `scores.quality = 80` (grounded HIGH, from the 10-K).

### UNP · JPM · HON · KO — INVESTIGATE · conviction 64 (Moderate) · agreement None

All four, byte-for-byte the same shape:

- **rationale**: *"No security-level analysis is available for {S}, so there is nothing to base a decision on."*
- **action**: *"Research {S} before the thesis can progress."*
- **because**: **empty**. **despite**: empty. **evidence_weighed**: **empty**. `evidence_as_of`: None.
- UNP's same page prints `scores.quality = 62` — the grounded MEDIUM this arc just earned (#169) — JPM's and HON's print the honest 1-of-3 refusal, KO's the 0-of-3.

### BTC · ETH — the crypto dossier

**No decision, no posture, no action, no conviction — the fields do not
exist on the surface.** What it does hold is the best-grounded evidence on
the platform: BTC's maximum supply *"21.00 million, agreed by 2 sources"*,
circulating *"20.07 million, agreed by 3"*, Supply Governance **answered**
(*consensus-bound mechanical rule*), Fee Capture's posture, quality
**UNKNOWN** with the honest arithmetic (*"1 of 9 questions can be scored
at all, and a band requires 2 — a statement about this platform's
evidence, not about the asset"*).

**And a second live surface disagrees**: `/executive/BTC/dossier` still
answers — *INVESTIGATE, conviction 46*, worded from *"a cryptocurrency
has no business quality or valuation to assess."* One asset, two product
answers, one of them scored from evidence the crypto layers were built to
replace.

---

## 2–3. Evidence behind each answer, and decision sufficiency

Classification of the important dimensions per asset (established &
relevant / established & immaterial / unresolved non-blocking / unresolved
potentially blocking / not applicable), collapsed into the §6 matrix:

| Asset | Current decision | Business Quality (grounded) | Other major evidence | Important unknown | Does it block the decision? | Sufficiency |
|---|---|---|---|---|---|---|
| **AAPL** | PREPARE 60, wait | **MEDIUM 62**, quorate, on the page | full market strip (P/E 32.9×, momentum, vol, correlation), committees 1.0 | *"quality unavailable"* — **false as stated**; the true unknowns (cash flow, valuation authority) are not the cited one | the *sentence* blocks progression; the evidence does not | **SUFFICIENT WITH MATERIAL UNCERTAINTY** — the posture is defensible; the cited unknown is not the real one |
| **DIS** | PREPARE 74, hold | **HIGH 80**, quorate, on the page | earnings −48.3% surfaced in *despite* and as the invalidation condition; cash flow established | same false *"quality unavailable"* | no | **SUFFICIENT** — the strongest page of the eight: reasons, adverse, and a condition all present |
| **UNP** | INVESTIGATE 64 | **MEDIUM 62**, quorate, earned this arc | 3 of 3 factors answered from the audited filing; **no market/provider strip acquired** | *"no security-level analysis"* — true of the provider half only | **the product treats it as total** — it claims "nothing to base a decision on" while its own page prints a band | **INSUFFICIENT AS STATED** — the decision may be right; the stated basis ("nothing") is false |
| **JPM** | INVESTIGATE 64 | UNKNOWN — 1 of 3, honestly | net-of-interest top line under its truthful concept, earnings −2.4%, committees' statements evidence | quality genuinely thin; no market strip | partially — investigate is right | **SUFFICIENT** for INVESTIGATE — but the conviction number is unfounded |
| **HON** | INVESTIGATE 64 | UNKNOWN — 1 of 3, stale evidence (BQ28) | profitability *strong* from stored readings | growth unanswerable until re-read | yes, genuinely | **SUFFICIENT** for INVESTIGATE — the honest case |
| **KO** | INVESTIGATE 64 | UNKNOWN — 0 of 3 counted (tie) | ten stored readings, deadlocked | the tie | yes, genuinely | **SUFFICIENT** for INVESTIGATE |
| **BTC** | *(none on the crypto surface)* / INVESTIGATE 46 on the legacy one | UNKNOWN by ruling (S5) | supply settled to the ledger, mechanical rule confirmed 89/89, two committees answered, ETF flows | none of the unknowns block a *structural* statement | n/a — **no decision exists to block** | **INSUFFICIENT for the CIO proposition** — not for honesty |
| **ETH** | same | UNKNOWN | fee-burn value capture evidenced, supply settled 3-source | supply governance evidence_insufficient | n/a | **INSUFFICIENT for the CIO proposition** |

**The architecture question §6 asks is answered by the UNP row.** The
platform holds decision-relevant, quorate, audited-filing evidence and
says *"nothing to base a decision on"* — because *permission to decide*
is keyed to one specific acquisition (the per-security provider analysis)
rather than to the sufficiency of what is held.

## 4. False blocking — measured

- **UNP is the flagship specimen.** Grounded MEDIUM 62, three of three
  factors answered from its own 10-K, printed on the very page whose
  rationale reads *"there is nothing to base a decision on."* A rational
  committee could absolutely form the posture *"quality-adequate railroad,
  no market context yet — acquire the strip before entry"* from what is
  cited on that page. The product instead denies the evidence exists.
- **AAPL and DIS are progression-blocked by a false sentence.** Both are
  held at PREPARE partly *because*ated *"Quality data is unavailable"*,
  while the grounded band is established and printed. The block may still
  be the right call (cash generation and valuation authority are real
  gaps) — but the case is being held back by the one unknown that is not
  actually unknown.
- **JPM and HON are *not* false-blocked** — the controls behave. JPM's
  quality is honestly 1 of 3 and its top line is refused for a reason the
  page can state; HON's evidence is provably stale. INVESTIGATE is the
  defensible posture for both. What is indefensible is the *same
  conviction number* for all four (see §5).

## 5. False confidence — measured

- **Conviction 64 attached to "nothing."** Four companies with wildly
  different evidence — a freshly-banded railroad, a semantically-refused
  bank, a stale industrial, a deadlocked staple — all emit **the same
  number** beside empty `because`, empty `evidence_weighed` and a
  rationale that says no basis exists. A number presented next to
  *"nothing to base a decision on"* is confidence nobody computed. (This
  is also the fourth sighting of the *identical-under-every-symbol*
  defect shape the dossier phase documented three times.)
- **`/executive/BTC/dossier` still scores Bitcoin 46** from business-
  quality-and-valuation reasoning the crypto rulings explicitly retired,
  while the crypto dossier beside it correctly refuses to score at all.
  Two answers, one asset, both live.
- **DIS 74 "High Conviction" with earnings −48.3%** was inspected for
  this class and is **not** a specimen: the adverse fact is surfaced in
  *despite*, named as the invalidation condition, and the action is
  conservative (hold, don't add). That is the system working.

## 7. The Artificial CIO proposition, judged

| | AAPL | DIS | UNP | JPM | HON | KO | BTC | ETH |
|---|---|---|---|---|---|---|---|---|
| 1. Know what to do? | yes | yes | nominally | nominally | nominally | nominally | **no** | **no** |
| 2. Understand why? | partly — reasons thin | **yes** | **no — "nothing"** | no | no | no | n/a | n/a |
| 3. Reasons grounded? | yes but shallow | yes | **empty** | empty | empty | empty | evidence yes; no reasons exist | same |
| 4. Unknowns distinguished? | **no — cites a false unknown** | no — same | **no** | partly | partly | partly | **yes — best on the platform** | yes |
| 5. What would change it? | yes (but the condition is false) | yes | generic | generic | generic | generic | n/a | n/a |
| 6. Would it help an investor act? | partly | **yes** | **no** | barely | barely | barely | no (knowledge without verdict) | no |

The crypto layers are the best at question 4 and fail questions 1 and 6
by construction; the equity decision layer answers question 1 everywhere
and fails 2–4 exactly where the provider-fed evidence set runs out.

## 8. Failures recorded, not repaired

F1 — decision gates read *"quality unavailable"* where a grounded band is printed (AAPL, DIS) ·
F2 — *"no security-level analysis → nothing to base a decision on"* while filing-grade evidence is on the page (UNP; structurally JPM/HON/KO) ·
F3 — conviction 64 emitted with zero cited evidence, identical across four assets ·
F4 — crypto dossier carries no decision sentence, not even a worded refusal to decide ·
F5 — `/executive/{crypto}/dossier` still live with the retired scoring ·
F6 — `invalidation_conditions` empty for AAPL and all four INVESTIGATEs ·
F7 — review_if conditions generic (*"measuring it is what would let this case progress"*) rather than named evidence ·
F8 — HON/KO/JPM stale-or-tied states, known and already ruled on elsewhere.

## 9. The taxonomy by product consequence, and the one slice

| Product consequence | Specimens |
|---|---|
| **Cannot decide (or under-decides) despite sufficient cited-able evidence** | UNP; AAPL/DIS progression |
| Decides/scores despite insufficient evidence | conviction-64 ×4; legacy BTC 46 |
| Defensible decision, poor explanation | JPM, HON, KO |
| Important uncertainty not surfaced | AAPL (real gaps hidden behind a false one) |
| Recommendation lacks actionable conditions | all four INVESTIGATEs, AAPL |
| Acquisition genuinely blocks | HON (ruled, BQ28), KO (tie), crypto quality (ruled) |

**Highest-leverage failure class: the first row plus the second are one
defect with two faces — the decision layer's evidence set is not the
platform's evidence set.** The gate and the conviction arithmetic consume
the provider-fed signals; the grounded bands, the statement facts and the
committee judgments are composed onto the page and consumed by nothing
that decides. Where the provider set is present the decision is
defensible but explains itself with the wrong unknown; where it is absent
the product invents a number and denies evidence it is simultaneously
displaying.

### The one recommended next slice

> **One evidence truth per decision: the decision layer consumes the
> grounded quality band where one governs, and the sentence "Quality data
> is unavailable" / "nothing to base a decision on" becomes unproducible
> on any page that prints an established band.**
>
> Concretely: the quality gate reads `workspace.quality` (the grounded
> band the pipeline already computes and already passes to the evidence
> builder) wherever it is quorate, falling back to the provider signal
> only where no grounded band exists; the absent-quality wording is
> derived from the same object the scores section reads, so the page
> cannot contradict itself; and a conviction number is emitted only where
> at least one `because` exists — otherwise the posture stands without a
> number, exactly as the crypto quality layer already refuses a band.

It improves the proposition across **at least five of the eight** (AAPL,
DIS, UNP truthful reasons and unknowns; JPM/HON/KO lose the unfounded
number), touches decision *inputs* under the provenance regime that
already governs them (`DECISION_RULE_PROVENANCE` — the affected rules are
re-pinned, which is the designed path), and directly executes the
already-measured `DECISION_CONVERGENCE` finding that has been awaiting a
ruling since the grounded route was built. F4/F5 (a crypto decision
sentence, retiring the legacy surface) are the natural second slice and
are deliberately not bundled.

## 10. Spend

**This slice requires no API or model spending.** Every input the slice
consumes is already computed on every dossier view. (DV1 itself spent
nothing: no model call, no observation, no write.)

## Scope compliance

HON not superseded or re-observed · nothing built or repaired · no prose
improved · production evidence only · writer and synthesis off ·
`data/` byte-identical throughout.
