# One investment judgment per digital asset, wherever it is shown

**Status: DV4, built. Closes the boundary DV3 recorded as open. No model
call, no acquisition, no production write. Stopped for ruling.**

> **DV3 retired the legacy crypto *dossier*. It did not reach the
> portfolio.** BTC's canonical dossier answered INVESTIGATE with no
> conviction; the same holding in the portfolio brief answered
> INVESTIGATE **conviction 46**, ranked **eleventh of fourteen**, with
> *"Market robustness: robust — $1,308.7bn"* printed as a reason **for**
> it and its annualised volatility printed **against** it. Two reasoning
> systems, one asset, and only the retired one carried a number.
>
> The pipeline now dispatches on the asset class, and a digital asset's
> decision is the crypto path's — translated into the record shape, never
> recomputed.

---

## 1. The divergence, measured

Every consumer that turns a holding into investment language runs through
one call, `ExecutivePipeline.execute`: the portfolio briefing, the
executive brief, the research pipeline, the CLI, and the change feed's
inputs. All of them received the company reasoning system's output for a
crypto holding.

| | canonical (`/crypto/BTC/dossier`) | portfolio brief |
|---|---|---|
| posture | INVESTIGATE | INVESTIGATE |
| conviction | withheld, worded | **46** |
| rank | — | **11 of 14** |
| because | — (nothing licensed) | *"Market robustness: robust — $1,308.7bn…"* |
| despite | — (nothing licensed) | volatility 35.9%, drawdown 53.1% |
| rationale | the committees' own conclusions | *"A cryptocurrency has no business quality or valuation to assess"* |
| committee agreement | the crypto matrix, never combined | the **company** committees, over provider findings |

SOL 59 > ETH 52 > BTC 46 was a cross-asset conviction ordering of three
digital assets produced entirely by provider arithmetic, while the
canonical layer said all three were INVESTIGATE with no conviction at
all.

## 2. The authoritative path

Unchanged from DV3, and now the only one:

recorded committee judgments → Decision Bridge (`AssetConsiderations`) →
Investor Assessment → `digital-asset-gates@1` → `DigitalAssetDecision`

DV4 adds one function, `as_executive_decision`, which carries that answer
into the record shape every surface already reads. It computes nothing:
state, rationale and every sentence are copied, and `decided_under`
carries `digital-asset-gates@1` so a reader can establish which reasoning
system produced the record — an executive record from the company gates
carries `decision-gates` and `conviction-mean` instead, and the two can
never be read as one. That stamp is the provenance, reusing the structure
the rule-provenance regime already defined.

## 3. The dispatch boundary

`brain.asset_class_for(symbol)`, consulted once in
`ExecutivePipeline.execute` — the narrowest existing point at which this
platform knows what kind of instrument it is reasoning about, and the
same one the evidence builder already used.

- **The class, not a corpus list.** No `ASSIGNMENTS` check and no symbol
  list reaches the pipeline (asserted). A crypto holding outside the read
  corpus still reaches the crypto path, where it honestly answers MONITOR
  because no committee has judged it — rather than falling through to
  company reasoning.
- **`AssetClass.CRYPTO`, not `has_no_company`.** That property also holds
  for ETF and COMMODITY, so dispatching on it would have routed every
  fund to the crypto decider. Pinned by a fund test.
- **The company route is not run at all**, rather than run and filtered.
  A provider-fed finding that exists is a finding something downstream
  can find; `findings`, `committee_opinions`, `quality` and `evidence`
  are all empty for a digital asset, which is what makes a legacy score
  structurally unable to reappear beside one.

## 4–7. The specimens

| | before | after |
|---|---|---|
| **BTC** | INVESTIGATE, conviction 46, rank 11, market cap as a reason for, volatility against | INVESTIGATE, **no conviction**, **no rank**, evidence weighed = Supply Governance's own conclusion (with its *"investment meaning is not established"* clause) and Value Capture's wrong-instrument finding |
| **ETH** | INVESTIGATE, conviction 52, rank 10 | INVESTIGATE, no conviction, no rank; evidence weighed = the evidenced value-capture mechanism; *what would advance it* = the issuance-rule gap and the maximum-supply silence, each under its owner's name |
| **TAO** (weak-evidence control) | — | **MONITOR**, visibly weaker than BTC/ETH's INVESTIGATE; applicability uncertainty stays a question and never becomes adverse |
| **ARB** (uncertainty control) | — | INVESTIGATE with the 81% circulating-supply spread carried as *what a later cycle could settle* — never in `key_risks` |
| **SOL** | INVESTIGATE, conviction 59, rank 9 | INVESTIGATE, no conviction, no rank |

`key_strengths` and `key_risks` are **empty for every digital asset**.
Both committee vocabularies say their answers are not grades, and the
bridge's licensing table is empty; filing a conclusion under *what argues
for this security* would author the meaning that table refuses to grant.
The conclusions travel in `evidence_weighed` — the neutral field — so a
wrong-instrument finding can never be read as an adverse one.

## 8. Cross-asset ranking: the limitation is exposed, not solved

A rank is a place in the conviction order, so only a case carrying a
conviction takes one. Crypto has not earned a quantity comparable to an
equity conviction — S5 refuses to band any digital asset, and no
committee conclusion has a licensed investment effect — so **no number is
substituted**. `rank` is `null` where `conviction` is `null`, on both the
portfolio and research responses.

The old code numbered every case, which gave the unranked tail positions
10th, 11th and 14th over an order that was merely the sequence the broker
reported the holdings in. The tail is still listed and still explained; it
is not numbered against itself.

Ranked positions stay dense (1…N) and every one is held by a case with a
conviction. **The larger question — whether a single cross-asset ordering
should exist at all — is left open**, as the brief directed.

## 9. Conviction cannot reappear

Four independent reasons, in descending order of strength: there is no
numeric field on the canonical decision (`conviction` is a property
returning `None`); the translation passes `conviction=None` explicitly;
no scores are produced for a digital asset, so no arithmetic has inputs;
and `conviction_label(None)` is `None`, so no word is attached either.
Pinned per specimen at the domain, the pipeline and the wire.

## 10. Regression

- **DV2's six-equity panel: 0 movements** across every field.
- **The live portfolio: 0 non-crypto decision movements** — state,
  conviction, rationale, because, despite, scores, action, thesis and
  evidence all byte-identical for all eleven equities. Their *rank
  numbers* shift only because crypto stepped out of the conviction order;
  their relative order and every conviction are unchanged.
- **Funds**: an ETF still runs the company route (pinned).

Two truthful side-effects, both flowing from the same rule rather than
from a crypto special case: `committee_agreement` is now `null` where no
committee spoke (it was flattened to `0`, which the panel's own comment
says would claim they disagreed completely), and CYD/AZN — equities that
already carried no conviction under DV2 — now show no rank either.

## 11. Recorded, not solved

- **`CandidateResearchService.evidenced` still gates on provider
  evidence.** A watched digital asset with no provider row is filed as
  *unevidenced* rather than judged from its committees. That is not a
  competing judgment — it is an absent one — so it is outside DV4's rule,
  but it is the next boundary of the same kind.
- **The change feed still shows historical crypto decisions** recorded
  under the legacy path, with their original rationales. That is correct:
  a recorded rationale is the one the CIO wrote at the time, and
  rewriting it now is exactly what Judgment History forbids. Since DV4
  does not journal crypto decisions, that history is frozen rather than
  growing.
- **No crypto journal, no CLI verb** — both still open from DV3.
- **`/api/today` is market-level** (SPY, market committees) and carries
  crypto sentiment explicitly labelled as market context, not as evidence
  about a security. Left alone.

## 12. Gates

`pytest -q` 3004 passed · ruff check + format clean · `mypy app` clean
(597 files) · `npm run build` + `tsc --noEmit` clean · production `data/`
byte-identical (the end-to-end run used a cloned evidence root).
