# One evidence truth per decision

**Status: DV2, built. The first product correction from
[`DECISION_SUFFICIENCY_BASELINE.md`](DECISION_SUFFICIENCY_BASELINE.md)
(DV1, #179). No model call, no observation, no production write — `git
status --porcelain data/` empty before and after every measurement.
Stopped for ruling.**

> **The decision layer's evidence set was not the platform's, and the
> repair is smaller and stranger than DV1's framing suggested: the
> grounded quality assessment was *already* reaching the decision path.
> It produced the score. What it never reached was any sentence, and any
> gate.** So AAPL printed *"Quality data is unavailable"* under a score
> that the very same object had produced, and UNP was told there was
> *"nothing to base a decision on"* while its `quality_score` field held
> the 62 that reading had earned.
>
> Nothing was rerouted. One object is now read by the three things that
> speak about it — the score, the gate, and the wording — instead of by
> the score alone.

---

## 1. The two paths, traced

Both halves run inside one call, `ExecutivePipeline.execute`, and diverge
inside `DecisionEvidenceBuilder.build`:

| | reads | for AAPL | for UNP |
|---|---|---|---|
| **A — the displayed score** | `workspace.quality` (`BusinessQuality`, grounded) via `_quality_value` and `_quality_basis` | MEDIUM → 62 | MEDIUM → 62 |
| **B — the gate** | `company is not None` — the provider-fed analysis **alone** | evidenced | **not evidenced** |
| **B — the wording** | `company.signals.quality.quality == "UNKNOWN"` — the provider signal **alone** | *"Quality data is unavailable"* | *"No security-level analysis"* |
| **B — the conviction** | the mean of present scores, unconditionally | 60 | 64 |

`quality_of` returns an assessment only where the statements reached
quorum, and `_quality_value` already documented the precedence — *a
grounded assessment governs outright, including when it bands UNKNOWN*.
Path B never consulted it.

**Authoritative:** `BusinessQuality`, produced by
`business_quality_service.quality_of` from the statement store.
**Derived:** `quality_score`, `score_bases.quality`, and now the wording.
**Legacy, still correct where it is the only reading:** the provider
`QualitySignal`. **Presentation adapters only:** everything in
`app/api/models/` and the frontend parsers.

### The conviction arithmetic, measured rather than assumed

DV1 recorded four identical 64s and read them as one constant. They are
not:

- **UNP** — `(62 + 51 + 78) / 3 = 63.67 → 64` (quality, evidence, fit)
- **JPM · HON · KO** — `(51 + 78) / 2 = 64.5 → 64` (evidence, fit; Python
  rounds half to even)

Two different means agreeing by coincidence, printed beside an empty
`because`. That is worse than a constant, not better: a constant is
visibly a default, and this looked like a measurement.

---

## 2. What changed

**One authoritative object, carried.** `DecisionEvidence.grounded_quality`
holds the assessment itself — not a copy of its conclusion — so the gate,
the rationale and the review condition read the object the score came
from. A page cannot contradict itself about quality if there is only one
quality to read.

**The gate reads all the evidence.** `security_evidenced` is
`company is not None or quality_assessment is not None`. Its own docstring
already said *any*; the computation tested one half. `decision-gates@2`.

**Three quality states, kept apart** (`_absent_quality`):

| state | outcome |
|---|---|
| assessed **and banded** — either route | nothing is missing about quality |
| assessed **and inconclusive** — quorate, too few answered factors | *"assessed … and could not be concluded"*, with what a later cycle could supply |
| **genuinely unavailable** — no assessment at all, provider reads UNKNOWN | *"Quality data is unavailable"*, unchanged |

The middle row is the one that did not exist. JPM, HON and KO *were*
read; calling their data unavailable denied a reading the same page
displayed and sent the investor to acquire what was already held.

**A conviction requires something to be convinced by.** `conviction` is
`int | None`, withheld where `strengths` is empty. Not zero — zero is the
bottom of the scale, which is itself a judgment, and this is the absence
of one. `conviction-mean@2`: the arithmetic is byte-identical; only its
licence to speak changed.

Both rules were re-pinned through the designed path — the provenance
guard fired on the version bump before the pins were edited, which is
what it is for.

---

## 3. The panel, before → after

| Asset | Decision | Conviction | Because | Despite | Quality wording | Evidence weighed |
|---|---|---|---|---|---|---|
| **AAPL** | PREPARE → **PREPARE** | 60 → **60** | 2 → 2 | 0 → 0 | *"Quality data is unavailable"* → **withdrawn** (grounded MEDIUM 62 stands alone) | 7 → 7 |
| **DIS** | PREPARE → **PREPARE** | 74 → **74** | 3 → 3 | **1 → 1** (−48.3% preserved) | *"Quality data is unavailable"* → **withdrawn** (grounded HIGH 80) | 12 → 12 |
| **UNP** | INVESTIGATE → **INVESTIGATE** | 64 → **withheld** | 0 → 0 | 0 → 0 | — | 0 → 0 |
| **JPM** | INVESTIGATE → **INVESTIGATE** | 64 → **withheld** | 0 → 0 | 0 → 0 | *"assessed … could not be concluded — 2 of 3 unanswerable"* | 0 → 0 |
| **HON** | INVESTIGATE → **INVESTIGATE** | 64 → **withheld** | 0 → 0 | 0 → 0 | same, **2 of 3** | 0 → 0 |
| **KO** | INVESTIGATE → **INVESTIGATE** | 64 → **withheld** | 0 → 0 | 0 → 0 | same, **3 of 3** | 0 → 0 |

**Every state is unchanged.** Convergence supplied evidence, not
permission — and the four INVESTIGATEs now differ from each other in
print (2 of 3 · 2 of 3 · 3 of 3) where they were byte-identical.

### The rationales

- **UNP** — *"No security-level analysis is available for UNP, so there is
  nothing to base a decision on"* → **"The opportunity merits deeper
  research before a thesis can be prepared."** The posture was not
  hard-coded: `security_evidenced` became true, the case passed the risk
  and watchlist gates on its grounded 62, and stopped at
  `evidence_score 51 < minimum_prepare_evidence 60`. INVESTIGATE is what
  the existing semantics reach, and the stated basis is now true.
- **JPM · HON · KO** — the same false sentence → *"Business quality was
  assessed from 10-K … and could not be concluded, so the case cannot
  progress beyond research. 1 of 3 factors answered — fewer than 2, so no
  band is claimed. That is a limit of the established evidence, not a
  finding about the company."*

### AAPL's review condition is now empty, and that is the finding

Its only entry was the false one. Removing it leaves AAPL with no
security-specific condition for review — DV1's **F6/F7**, previously
hidden behind a falsehood and now visible. The case is still explained:
the rationale, *"quality conviction is not yet sufficient"*, is the true
reason it sits at PREPARE, and it was always there.

---

## 4. Overreach, refused

`known quality → positive recommendation` is not what happened, proved
three ways:

- **0 of 6 states moved**, at every band the panel holds.
- A grounded reading alone reaches INVESTIGATE **at every band including
  HIGH** — a company known only through its filings has no valuation, no
  risk and no execution trigger, and the gates decide that, unchanged.
- A quality score of 30 still **REJECTs** a case clearing every other
  gate. The one direction a quality reading may move a case by itself is
  caution.

---

## 5. Found, not caused: a dossier that would not render

**Any security with exactly one recorded review served a 200 payload and
rendered *"The backend is unreachable"*.** `DecisionCourse.stated` is
`""` where there is no course — the sentence lives in `absent_because` —
and the parser's `requireString` rejects an empty string, so the whole
dossier was discarded over a field the page does not even print in that
branch.

Pre-existing since `5d74e3e`, untouched on both sides by this slice, and
found only because DV2's flagship specimen was the security in that
state. Fixed here (`optionalString`), because leaving it would have made
the slice unverifiable in the product it is about — and because a 200 is
not a rendered page.

---

## 6. Recorded, not solved

- **`security_evidenced` is decision-bearing and governed by no rule of
  its own.** It selects INVESTIGATE outright, ahead of every score, and
  the eighteen-transformation audit did not name it. It is folded into
  `decision-gates@2`'s fingerprint here rather than given a rule, because
  the architecture is frozen.
- **UNP holds a quorate band and still cites no `because`.** The finding
  ledger is built from provider signals only, so a grounded factor is
  never a *reason* — only a score. Converting answered factors into
  `Finding`s would also change committee inputs, which is a wider blast
  radius than this slice earns.
- **`MATERIAL_SPREAD`-style thresholds are untouched.** No conviction
  calibration, no weighting, no quality threshold design.
- **Crypto is out of scope by instruction.** BTC/ETH still carry no
  decision sentence, and `/executive/BTC/dossier` still scores 46 — DV1's
  F4 and F5, deliberately unbundled.

## 7. Gates

`pytest -q` 2932 passed · `ruff check` clean · `ruff format --check`
clean · `mypy app` clean over 595 files · `npm run build` clean ·
`tsc --noEmit` clean. Production `data/` byte-identical throughout; the
end-to-end run used a cloned evidence root so the route's own journal
write could not touch it.
