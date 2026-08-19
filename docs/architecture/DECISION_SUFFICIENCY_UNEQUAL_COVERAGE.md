# Decision sufficiency under unequal coverage

**Status: research. 2026-08-19. No production change, no decision
altered.** One recorded Daily CIO cycle (`0a15d9df7a64` — the spine's
first production-shaped run), a corpus of 18 company securities, a
stage-0 trace of the complete decision contract, and a reversible
ablation measurement over the same held state. Production data
untouched; the isolated store was restored byte-identically after every
mutation and the whole-tree digest asserted it.

## Conclusion

# B. COURSES READY, CAPITAL-ACTION CONTRACT NOT READY

**The course layer already operates honestly under unequal coverage.**
Every one of the 18 securities received an explicit course or an
explicit refusal; the hard floor is invariant across size, fame and
coverage — the same six families demote a US large-cap and a French
bank identically — and the honest action ceiling for limited evidence
already exists in the vocabulary: PREPARE — HOLD for a held security,
WAIT for an unheld one — and INVESTIGATE/RESEARCH are doing exactly
that job today, correctly.

**OPEN/ADD cannot yet be permitted under limited evidence, for four
measured reasons.** Conviction is not comparable across coverage —
removing evidence *raised* it from 77 to 81 in the live corpus; no
action-magnitude contract exists to bound a smaller commitment
(`max_order_usd` is consumed by nothing); a positive disposition's
rationale claims *"satisfies quality, evidence, valuation, risk, and
portfolio gates"* while `missing_evidence` names an unread factor the
rationale does not; and one substitution door (below-quorum filings →
provider proxy) makes the *authority* behind a quality score invisible
at the moment of action. The precise missing contract is named in §7.

---

## 1. Stage 0 — the contract as it exists

The full trace (file:line for every rule) established the spine:
`ExecutivePipeline.execute` → `DecisionEvidenceBuilder.build` →
`ArtificialCIO.decide` (sixteen ordered gates) →
`ExecutiveActionBuilder.build` (state × held → course). The findings
that govern this measurement:

**Where absence is handled rigorously** — the platform's own rule ("a
score of None means the platform did not measure it; it never means
zero, and it is never filled in from something else",
`executive_decision.py:16-23`) holds at every score: all five scores are
None-not-zero; UNKNOWN is deliberately absent from every direction
table so it cannot vote; quality abstains rather than banding a partial
set (quality-authority@1); the grounded denominator counts answered
questions only; a withdrawal blocks the provider route; risk refuses a
partial mean; conviction drops absent terms and is withheld entirely
without a favourable finding.

**Where absence becomes a number anyway** — the audit's positive
findings:

1. **`evidence_score` is structurally incapable of absence** — typed
   `int`; with no security evidence at all it becomes
   `int(cognitive × 0.6)`, a positive number derived from the
   *account's* reasoning confidence (`decision_evidence_builder.py:385-403`).
2. **A third of that cognitive figure is a constant.**
   `RiskAnalyst.CONFIDENCE = 0.80` regardless of whether market risk
   and drawdown risk were measured (`risk_analyst.py:23`).
3. **Vote confidence floors at 50** and measures agreement, not
   coverage — a two-abstention case can out-score a fully-covered
   disagreeing one inside `evidence_score`.
4. **Absence is systematically protective against the veto.**
   `analyst_veto` needs a SELL vote, which needs full signal coverage —
   so missing evidence can never veto, and (measured, §4) removing
   SPCX's price *improved* its disposition from REJECT to INVESTIGATE.
5. **A stated-zero dividend inferred from two sibling fields becomes a
   zero-point quality factor** — a statement about payment read as a
   fact about quality (`value_provider.py:232-243` →
   `quality_signal_service.py:266-269`).
6. **The substitution door**: below-quorum and UNMEASURABLE filing
   knowledge fall through to the provider triad
   (`decision_evidence_builder.py:293-327`) — documented as intentional,
   and the one place an authoritative source failing to conclude hands
   the score to a weaker one. Measured live: removing BNP.PA's grounded
   knowledge left RECOMMEND/add byte-equal at conviction 76, because
   the provider proxy also reads 80 — **the authority swap is invisible
   in every outcome field**.
7. **The account's risk never reaches the CIO's gates** — measured:
   removing the portfolio's entire drawdown reading left both
   capital-asking cases at RECOMMEND/add, identical conviction. The
   security's own volatility/drawdown is gated; the account's condition
   participates only through a constant-bearing confidence.
8. **Dormant controls a reader would assume live**: `hard_reject`
   (constructed False), `max_order_usd` (consumed by nothing — no
   sizing or action-ceiling code exists anywhere), the quality-REJECT
   branch (no band maps below the 35 floor), MONITOR (reachable only
   through a pathological triple).

**The key audit passes with the exceptions above**: no missing factor
becomes an adverse *score* — the failure modes are subtler: synthetic
floors (1–3), protective absence (4), semantic misread (5), silent
authority swap (6), and unnarrated absence at positive dispositions
(§5).

## 2. Stage 1 — the corpus, from one recorded cycle

Cycle `0a15d9df7a64`: COMPLETE, 276.1s, **288 outbound calls (bound
400, transport-counted)**, 24 of 26 priced, two worded refusals (HYPE,
TAO), 14 courses, comparison basis INITIAL_BASELINE. The active book
supplied 11 company securities; 7 additions were evaluated from stored
evidence only (AAPL, MSFT, SE, NFLX, MCD, JNJ, PG — broker items
reconstructed from the identity observation stream for the book and
from stored names for additions, declared here). Offline baselines
reproduced the cycle's dispositions exactly.

| symbol | disposition | course | asks | conviction | quality basis |
|---|---|---|---|---|---|
| **DIS** | RECOMMEND | add | yes | 77 | grounded governs |
| **BNP.PA** | RECOMMEND | add | yes | 76 | provider HIGH (grounded below quorum) |
| ADBE | PREPARE | hold | no | 67 | — |
| UMI.BR | PREPARE | hold | no | 67 | — |
| AAPL · MSFT · MCD · PG | PREPARE | wait | no | 59–70 | — |
| VOW3.DE · AZN · ETOR · META · CYD · NOVO-B.CO · JNJ · SE · NFLX | INVESTIGATE | research | yes* | 60–70 | quality unanswerable |
| **SPCX** | REJECT | reduce | yes | 40 | vetoed |

*RESEARCH asks for work, not capital. The two capital-asking courses
are DIS and BNP.PA (`add`). AAPL and MSFT are the negative control the
corpus required: broadly evidenced, PREPARE/wait, no capital action —
**broad coverage did not buy a stronger verdict.**

Specimen slots: Apple/Microsoft/Adobe present; DIS the covered
large-cap; CYD the sparse one; five non-US issuers; BNP.PA the bank;
SE the identity dispute (UNRESOLVED, its size factor refused); SPCX the
limited-identity holding; INVESTIGATE cases carry the incomplete-quality
slot; **the DOCUMENT_REFUSED slot could not be filled and that is
itself a finding** — Citigroup holds no stored fundamentals, and the
#210 refusal is a knowledge-service outcome that is *not stored
anywhere a decision reads*: the decision layer today cannot distinguish
"filing refused" from "filing never read".

## 3. Stage 2 — the ablation matrix

Six specimens × nine evidence families, every mutation reversed and the
tree digest asserted equal; **zero provider calls** (every transport
patched to raise; the Brain replayed from the cycle's own captured
eToro evidence).

The demotion map for the capital-asking cases:

| family removed | DIS (RECOMMEND/add) | BNP.PA (RECOMMEND/add) |
|---|---|---|
| identity (vendor claim absent → ASSUMED) | unchanged | unchanged |
| identity **conflict** (UNRESOLVED) | **PREPARE/hold** | **INVESTIGATE/research** |
| pricing | **PREPARE/hold, conv 81↑** | **PREPARE/hold, conv 81↑** |
| market cap | **PREPARE/hold** | **INVESTIGATE/research** |
| valuation (P/E) | **PREPARE/hold** | **PREPARE/hold** |
| momentum | **PREPARE/hold, conv 81↑** | **PREPARE/hold, conv 81↑** |
| quality (grounded removed) | unchanged | unchanged — **provider proxy substituted invisibly** |
| quality (provider factors) | **PREPARE/hold** | **INVESTIGATE/research** |
| earnings calendar | **unchanged — RECOMMEND/add stands** | **unchanged — RECOMMEND/add stands** |
| portfolio drawdown (account-level) | unchanged | unchanged |

And the non-capital rows: AAPL's PREPARE moved under nothing; CYD's
INVESTIGATE moved under nothing (its provider-quality removal took
conviction to None — the strengths emptied, and the number was
honestly withheld); SE's INVESTIGATE moved under nothing; **SPCX's
REJECT improved to INVESTIGATE when its price or momentum was removed**
— the veto's inputs gone, the adverse judgment gone with them.

Three measured facts that decide the conclusion:

- **The hard floor is real and invariant** (acceptance Q2): identity
  free of unresolved conflict, a price, a market-cap crossing, a P/E, a
  quality answer and full vote coverage are each individually
  sufficient to demote RECOMMEND — on both the US large-cap and the
  French bank, under identical rules.
- **Conviction is not coverage-comparable** (Q9/Q10 inverted): the
  five-term mean loses its risk/safety term when pricing goes and the
  surviving terms average *higher* — 77 → 81 while the state fell.
  A number that rises as evidence leaves cannot bound an action.
- **RECOMMEND can stand with a named factor unread** (Q3/Q4): the
  earnings calendar removed, both capital-asking cases keep
  RECOMMEND/add; `missing_evidence` names the unread calendar; the
  rationale still reads *"satisfies quality, evidence, valuation, risk,
  and portfolio gates"* and names nothing.

## 4. Stage 3 — the gaps, classified by role in the decision

**A. HARD SAFETY PREREQUISITE** (earned by demotion in the matrix):
an identity free of unresolved cross-provider conflict · a current
quote · an admissible market-cap crossing · a forward P/E · an answered
quality band (either route) · vote coverage (≥2 participating signals,
full relative coverage). These are the floor, and they did not vary
with company size or coverage.

**B. ACTION-LIMITING UNCERTAINTY** (course survives; the claim or
magnitude should narrow): the unread earnings calendar under a
RECOMMEND (the case stands, but the platform is acting into a
scheduling blind spot it names only in a side field) · the one
unanswered third of a 2-of-3 grounded quality band · a dropped research
analyst · **the provider-proxy quality basis where filings did not
conclude** — the course may stand, but the claim "quality 80" carries a
different authority than the same number grounded, and nothing at the
action layer says which. **To become operational, every one of these
needs an action-ceiling or sizing contract that does not exist** —
`max_order_usd` and its whole family are dormant, and no code path
bounds a commitment by anything.

**C. ADDITIONAL ANALYTICAL DEPTH** (absence changes nothing and the
claim is not weakened): the account-level drawdown reading at decision
time (it never reaches the gates — its absence today literally cannot
change a decision; whether it *should* is a separate question this
measurement flags but cannot answer) · market sensitivity · identity
*enrichment* beyond conflict-freedom (ASSUMED vs CORROBORATED moved
nothing).

**D. UNRESOLVED**: whether "one provider's claim, never cross-checked"
(ASSUMED) is an acceptable identity floor for a capital action — it
passes today by design (#134's honest description of every join), and
the ablation cannot say whether it should; whether the stated-zero
dividend inference (§1.5) belongs in a quality factor at all; and the
DOCUMENT_REFUSED indistinguishability (§2), which needs the refusal to
become a stored fact before its decision role can even be measured.

## 5. The fifteen acceptance questions

1. **Yes** — 14 courses + 2 worded refusals in the cycle; 18/18 in the
   corpus; the spine's no-silent-drop pass guarantees it structurally.
2. Identity-conflict-freedom, price, market-cap crossing, P/E, quality
   answer, vote coverage — **invariant across both capital-asking
   cases and every control**.
3. **Yes** — RECOMMEND with the earnings calendar unread, measured on
   both capital-asking cases; plus (traced) a 2-of-3 grounded band and
   dropped analysts.
4. **No** — `missing_evidence` names them; the rationale claims all
   gates satisfied. The one course that names a gap is RESEARCH.
5. **No score becomes adverse from absence** — but three synthetic
   floors put *positive* numbers where absence lived (`evidence_score`,
   the 0.80 constant, the vote floor), which is the same defect from
   the other side.
6. **Yes, one door**: below-quorum/UNMEASURABLE filings → provider
   triad, invisibly (BNP.PA measured). The bank-top-line refusal itself
   is honoured; the door is the quorum fall-through.
7. **No** — not with current conviction semantics (it rises as
   coverage falls) and no magnitude contract.
8. **Yes** — PREPARE (HOLD or WAIT, depending on ownership) and
   INVESTIGATE/RESEARCH are already the honest action ceiling, and the
   matrix shows them doing that job correctly on every gap.
9/10. **No and no** — AAPL/MSFT (broad) sit at PREPARE; CYD (sparse)
   at INVESTIGATE for a *named* reason (quality unanswerable), and no
   ablation worsened any verdict through absence alone. The one
   inversion runs the other way: absence *improved* SPCX (Q-audit §1.4).
11. For DIS/BNP.PA: an identity conflict, a lost price, a failed
   market-cap crossing, P/E leaving the CHEAP band, a quality reversal,
   or a SELL-strength vote — each independently reverses the course.
12. **No** — there is no "acting despite the gap because…" sentence
   anywhere; the gap sits in `missing_evidence` and the acting sentence
   claims completeness.
13. **Partially** — the grounded/provider split *is* that distinction,
   but it is invisible at the action layer (the substitution door).
14. The genuine safety refusals are the hard floor of Q2. The
   completeness gates worth re-examining: the earnings calendar is
   *not* gated (arguably right), while the vote-coverage rule makes
   *any* single signal absence fatal to RECOMMEND even where four
   others answer — that is a completeness gate doing a safety gate's
   job, and whether it over-refuses is exactly the sizing question.
15. **Yes** — action magnitude is the missing pressure valve. Every
   category-B gap has the same shape: the course is supportable, the
   *full-size* commitment is not, and the platform has no vocabulary
   between "act" and "wait".

## 6. The candidate object and the wording, tested

`DecisionSufficiency` survives as a **projection** (derived from the
cycle record + evidence bases, stored nowhere) with two corrections:
`capital action currently supportable: yes | bounded_only | no` **cannot
carry `bounded_only` yet** — nothing exists to bound an action, so
today it would be a promise, not a state; and `evidence used` must name
the *authority* of the quality basis (grounded vs provider), or the §3
substitution stays invisible. Everything else maps onto fields this
measurement produced without invention.

The three wordings hold against the corpus with one addition each:
the limited-evidence sentence works verbatim for the earnings-blind
RECOMMEND; the insufficient-evidence sentence is exactly what
INVESTIGATE/RESEARCH cases already mean (and CYD's provider-quality
ablation shows the platform even withholds the conviction number
there); the broad-evidence sentence must not name "risk" as a resting
family while the account's own risk reading is decorative (§1.7) — it
should name the security's risk measurables, which are real.

## 7. What blocks A, precisely

1. **A conviction comparable across coverage** — or the removal of
   conviction from any action-bounding role. A number that rises as
   evidence leaves cannot participate in "how much".
2. **An action-magnitude contract** — the missing pressure valve
   (Q15). `max_order_usd` exists and nothing reads it; `bounded_only`
   is unexpressible until something does. This is the separate
   measurement the #217 ruling already reserved.
3. **Gap-naming at positive dispositions** — the rationale must name
   what was unread when a capital-asking course is issued
   (`missing_evidence` already carries it; the sentence does not).
4. **Authority-naming on the quality basis** — grounded vs provider
   must be visible wherever the score acts (the substitution door).
5. **DOCUMENT_REFUSED as a stored, decision-readable fact** — until
   then its decision role cannot even be measured.

None of these is a threshold, quorum, analyst or vocabulary change, and
none was made here.

## 8. Boundaries held

One cycle, 288 calls against the 400 bound, transport-counted · no
model calls (seams forced off; transports asserted) · no Massive, SEC
or leadership acquisition · no trade, message or notification path ·
no retry added · no second cycle · additions from stored evidence only
· ablations in-process against the isolated copy with every transport
patched to raise and zero calls observed · every mutation restored and
the tree digest asserted byte-identical · `.env` in process memory
only; no balance, credential or account identifier in this report · no
completeness or confidence percentage computed anywhere · production
`data/` untouched.

---

## 9. Owner ruling — 2026-08-19

Conclusion B is accepted, with two factual corrections applied above:
the measured hard floor counts **six** families (identity free of
unresolved conflict · price · market-cap crossing · forward P/E ·
quality answer · vote coverage), and the honest non-capital ceiling is
**PREPARE with HOLD or WAIT depending on ownership**, alongside
INVESTIGATE/RESEARCH.

**A. A capital-asking course may stand beside named gaps.**
RECOMMEND/OPEN or RECOMMEND/ADD remains a valid course when the
invariant hard safety floor passes, the missing evidence is explicitly
named, the missing evidence is not represented as negative evidence,
the platform does not claim complete underwriting, and no automatic
execution occurs. **Missing analytical depth does not automatically
require demotion.**

**B. Until an action-magnitude contract exists, OPEN/ADD is a course
for the investor to consider — never a bounded capital instruction.**

**C. Conviction is not coverage-comparable and is forbidden from any
position-sizing or action-ceiling calculation under the present
semantics.** Conviction is *not* to be redesigned in the next slice:
excluding an unsuitable input is preferable to opening a calibration
project without evidence that the product needs it.

**D. Gap-naming and quality-authority naming are approved requirements
for the eventual capital-action presentation** — carried separately
from the positive rationale if changing the canonical rationale would
alter decision semantics.

**E. DOCUMENT_REFUSED propagation remains required for affected
companies, and it is a local evidence-integrity gap, not a global
prerequisite for measuring position size.** It must not delay the
magnitude measurement; it is parked as a named follow-on.

**F. The measured hard floor is accepted as the current contract, not
declared permanently optimal.** No P/E, vote-coverage, quality,
identity or other threshold change is authorized here.

**G. Information gaps may only preserve or reduce a future action
envelope. Removing evidence must never increase permitted capital.**
