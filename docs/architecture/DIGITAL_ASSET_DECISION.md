# One Artificial-CIO answer for a digital asset

**Status: DV3, built. The second product correction from
[`DECISION_SUFFICIENCY_BASELINE.md`](DECISION_SUFFICIENCY_BASELINE.md)
(DV1) — F4 (no crypto decision sentence) and F5 (the legacy executive
surface still live) as one slice, because they are one defect: one
asset, two product surfaces, and the weaker one was the only one that
told the investor anything. No model call, no acquisition, no
production write. Stopped for ruling.**

> **The crypto dossier now carries the Artificial CIO's answer, derived
> from judged states and nothing else, and the legacy executive dossier
> answers 410 for every asset in the crypto corpus.** BTC's answer is no
> longer *INVESTIGATE, conviction 46* from provider-fed signals the
> crypto rulings retired — it is INVESTIGATE from the Supply Governance
> Committee's own conclusion, quoted with the standing sentence that its
> investment meaning is not established, with no number anywhere.

---

## 1. The divergence, reproduced

Before this slice, for one asset:

| | `/crypto/BTC/dossier` | `/executive/BTC/dossier` |
|---|---|---|
| evidence | committees answered, supply settled to the ledger, honest readiness arithmetic | provider strip: market cap, volatility 35.9%, drawdown 53.1% |
| decision | **none — the field did not exist** | INVESTIGATE, **conviction 46** |
| conviction basis | — | mean of evidence-coverage 68, safety 35, fit 36 — nothing crypto-judged in it |

DV2's withheld-conviction rule had already improved the legacy surface
unasked: TAO and ARB (no strengths) showed conviction None. BTC and ETH
still emitted 46 and 52, because the provider quality signal's *market
robustness* finding counted as a strength.

## 2. The authoritative inputs

Two layers, both already addressed to an investment consumer, both
consumed at read-only doors:

- **The Decision Bridge** (#128, `AssetConsiderations`) — each
  committee's conclusion with its **posture** (the protocol's five
  states), its own sentence, and the standing statement that its
  investment meaning is not established. This slice is the bridge's
  first deciding consumer, which is what it was built to make safe.
- **The Investor Assessment** (#117) — the strongest useful statement
  per subject, shaped, with every silence named.

Market context is structurally out of reach — S4's import guard covers
`app/cio` and stays intact — and Asset Quality participates by ruling
(S5: every asset UNKNOWN) rather than by object: the ceiling sentence
states it, and no readiness value is consumed. No provider payload is
re-read anywhere.

## 3. `digital-asset-gates@1` — the sufficiency rule

Posture arithmetic, and nothing else. The rule never reads a verdict's
meaning, a committee's key, or a number (#114: the framework may know
*that* Committee X answered Z; it may never know what Z means).

| condition (over committee postures) | state | sufficiency reading |
|---|---|---|
| ≥1 question ANSWERED | **INVESTIGATE** — structural evidence established and quoted; what it is worth is not established | meaningful evidence, thesis incomplete |
| ≥1 question applicable but only awaiting evidence / execution | **INVESTIGATE** — the committees name the missing evidence; research is acquiring it | conservative decision possible |
| no question even applicable (role unestablished, or every question the wrong instrument), or no judgment recorded at all | **MONITOR** — research cannot be directed | decision-blocking uncertainty |

PREPARE and RECOMMEND are unreachable and the ceiling is worded on
every decision: this platform judges a case on business quality and
valuation, a digital asset has neither to assess, and no crypto
conclusion has a licensed investment effect. REJECT has no branch at
all: no crypto evidence layer licenses an adverse reading, so there is
nothing a rejection could rest on.

**Conviction is structurally unfillable**: the domain object has no
numeric field — `conviction` is a property returning `None` — and the
serialised payload deliberately carries **no `conviction` key**,
because the crypto route guard forbids that key everywhere and the
guard is right: a field that exists as null invites a number. The
worded absence (`conviction_withheld_because`) is all a surface may
render. That is DV2's rule applied at the strongest available strength.

The rule is registered (`DecisionRule`, status ARGUED — the eighth) and
pinned: the applicable-posture partition and the two reachable states
are fingerprinted, so widening either is a deliberate re-pin.

## 4. The specimens

- **BTC — INVESTIGATE, no number.** Established: Supply Governance's
  own sentence (mechanical rule, read and re-run, consensus-bound).
  Not applicable, never adverse: Value Capture, in the committee's own
  words — fees are the security budget, the question is the wrong
  instrument. Nothing unresolved.
- **ETH — INVESTIGATE, no number.** Established: Value Capture's
  evidenced fee-burn mechanism. Unresolved, each in its owner's words:
  no mechanical issuance rule is held (Supply Governance), and maximum
  supply — where *"ETH has no cap"* is still not supportable — is a
  named silence.
- **TAO — MONITOR, the false-confidence control.** Both committees
  read `applicability_unknown`: no economic role is established, so
  this platform cannot say which questions the asset should even be
  asked. Evidence weaker than BTC/ETH produces a visibly weaker
  posture, and the advance is named (establish the role). ARB — with
  an answered committee but an 81% circulating-supply spread — stays
  INVESTIGATE with the spread carried as **material uncertainty, never
  as adverse**.

Across the eight-asset corpus: 7 × INVESTIGATE, TAO alone MONITOR, and
the exhaustive posture-pair test (25 cells over a synthetic
never-heard-of committee) proves no combination reaches an actionable
state.

## 5. What survives the crossing

NOT_APPLICABLE stays distinct from unknown and renders under its own
heading (*"knowledge, never adverse"*); insufficiencies keep their
owner's own sentence; silences stay named; ADA's judging-off state
crosses as *execution unavailable — a fact about this platform*; and
one fact keeps one owner: an assessment statement quoting a committee
(`from_committee`, the provenance field built after #126) is not
carried a second time under a second owner.

## 6. The retirement

`/executive/{symbol}/dossier` answers **410 Gone** for every symbol in
`ASSIGNMENTS` — the same declaration the crypto corpus and its switcher
serve, so the gate and the corpus cannot disagree — **before the brain
pipeline runs** (a test wires an exploding builder to prove retirement
costs no build). Gone rather than redirected at the API, because the
two payloads share no shape; the refusal names the canonical route. The
frontend translates: `getDossier` recognises 410 as `source: "retired"`
and `/dossiers/BTC` issues a real redirect to `/crypto/BTC`. A
non-corpus symbol proceeds exactly as before — the gate is the corpus,
not the asset class, so no equity and no fund can be caught by it.

**Pinned end-to-end for BTC**: legacy 410, canonical 200 with a
rationale, exactly one live answer.

## 7. DV1's six questions, re-answered for BTC/ETH

| | before | after |
|---|---|---|
| 1. Know what MOVRvest thinks I should do? | two conflicting surfaces | one: INVESTIGATE, worded |
| 2. Understand why? | "no business quality to assess" | the committees' own conclusions, quoted |
| 3. Reasons grounded? | provider strip | recorded judgments with judgment ids beneath them |
| 4. Unknowns surfaced? | best on the platform, on the undecided surface | same layers, now on the deciding surface, each in its owner's words |
| 5. Conviction justified or withheld? | 46 / 52, unfounded | withheld, structurally, with the reason worded |
| 6. Exactly one canonical answer? | **no** | **yes — 410 on the other** |

## 8. Equity untouched

The DV2 six-equity panel re-ran after the change: **0 movements** across
state, conviction, rationale, scores, because, despite and missing
evidence. No equity gate, no conviction arithmetic, no finding ledger
was edited.

## 9. Recorded, not solved

- **The executive brief and research surfaces still run the legacy
  pipeline over crypto holdings** (`/executive/portfolio`, ranking). The
  retirement covers the per-security dossier — the surface DV1 measured
  as the competing product answer. Whether BTC should appear in the
  equity-style briefing at all is a product question for the next
  slice.
- **The crypto decision writes no journal.** It is a projection, so
  page views cannot manufacture judgment events — but it also means no
  decision history accrues for crypto. If posture transitions become
  worth remembering, that is Judgment History's pattern to extend, not
  a `with_memory()` bolt-on.
- **`movrvest` has no CLI verb for it yet**; the route and the page are
  the product surfaces this slice earns.
- The bridge's licensing table stays **empty**: nothing here licensed
  an investment effect, and the INVESTIGATE/MONITOR ceiling is exactly
  what an empty table supports.

## 10. Gates

`pytest -q` 2976 passed · ruff check + format clean · `mypy app` clean
(597 files) · `npm run build` + `tsc --noEmit` clean · production
`data/` byte-identical (end-to-end run used a cloned evidence root).
