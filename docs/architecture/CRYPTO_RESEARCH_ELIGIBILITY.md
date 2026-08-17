# The evidence that admits an asset belongs to the system that judges it

**Status: DV5, built. Closes the boundary DV4 recorded as open. No model
call, no acquisition, no production write. Stopped for ruling.**

> **DV4 made a digital asset's judgment canonical everywhere. Its
> admission to research was still decided by the company evidence
> pipeline.** Measured on the live corpus: **1INCH, ARB and ADA each hold
> recorded committee judgments and a canonical INVESTIGATE, and all three
> were withheld from research** — not because anything about them was
> unknown, but because a *fundamentals request budget* of forty had not
> reached them.
>
> A digital asset needs no such request. Reading what its committees
> already recorded costs nothing.

---

## 1. The divergence, measured

`CandidateResearchService.evidenced` admitted a candidate when
`brain.evidence_for(symbol)` was non-empty — a provider row from the
company acquisition path — **for every asset alike**, and since DV4 a
digital asset is not judged by that path at all.

Two live measurements, at two budgets:

| watched token | provider row | recorded judgment | canonical | admitted before |
|---|---|---|---|---|
| HYPE | yes (inside budget) | yes | INVESTIGATE | yes |
| TAO | yes (inside budget) | yes | MONITOR | yes |
| **1INCH** | **no** | **yes** | **INVESTIGATE** | **no** |
| **ARB** | **no** | **yes** | **INVESTIGATE** | **no** |
| **ADA** | **no** | **yes** | **INVESTIGATE** | **no** |

And on an ordinary read with no acquisition budget at all — the page-view
case — **every one of the five was excluded**, while the judgments that
would have answered for them were already recorded and free to read.

**The inverse existed too**: a provider row alone was sufficient. A token
no committee had ever looked at would be admitted on market statistics,
which are not a judgment.

## 2. What `evidenced` meant

*The Brain holds any evidence object for this symbol* — in practice a
`CompanyRecommendation` produced by the provider path, rationed by
`candidate_limit`. Its docstring said "the candidates the Brain can
describe on their own terms", which was true when one pipeline described
everything and stopped being true at DV4.

## 3. The authoritative admission input

`DigitalAssetDecision.judged` — whether any committee has recorded a
judgment for the asset at all. It is read through the same
`DigitalAssetDecisionService` the pipeline uses, so admission and
judgment cannot diverge, and reading it is free.

It is **not** *has any data*: a provider row grants nothing, and a market
capitalisation is not a conclusion.

## 4. Was the boolean sufficient?

**Yes, and the finding is that the distinction it needed already
existed** — carried only in prose. `decide_digital_asset` already
separated *no committee has recorded a judgment* from every other
MONITOR, and said so in the rationale string. A caller deciding
admission would have had to match on a sentence.

So one field was added, not a state machine: `judged: bool`. The four
committee postures stay where they belong — inside the decision that
already renders them — and none is collapsed into an absence. In
particular **TAO reads `judged=True`**: both its committees ran and
recorded that they cannot establish whether their questions apply, which
is a conclusion reached by looking, not a failure to look.

## 5. The dispatch boundary

DV4's, unchanged: `brain.asset_class_for(symbol)`, tested against
`AssetClass.CRYPTO` itself. No symbol list, no `ASSIGNMENTS`, no
`has_no_company` — that property also covers **ETF and COMMODITY**, both
of which the company pipeline still describes, so dispatching on it would
have sent every fund's admission to a judgment path that would never
judge it.

## 6–11. The controls

| | result |
|---|---|
| **BTC / ETH** | held rather than watched, so admission never applied; both remain INVESTIGATE through the canonical path, and a provider row is not the authority for either |
| **TAO** | **MONITOR, admitted** — an informed applicability state is a conclusion, not an absence |
| **ARB** | **INVESTIGATE, admitted** with its material supply spread intact; uncertainty is a research target, not missing evidence |
| **1INCH · ADA** | **newly admitted** on recorded judgments, with no provider row |
| **watched token, no provider row** | admitted on its judgment (synthetic and live) |
| **provider row, no judgment** | **withheld**, and *named* as unevidenced — a security silently absent reads as one considered and dismissed |
| **equity / fund / commodity** | admission unchanged, on provider evidence; a crypto judgment can never stand in for a company (pinned across all three classes) |

Live effect at budget 40: **judged 40 → 43**, gaining exactly 1INCH, ARB
and ADA, losing nothing.

## 12. Regression

**0 movements** on DV2's six-equity panel and **0 movements** across all
fourteen portfolio holdings (state, conviction, rationale, because,
despite, scores, action, rank, evidence weighed, missing evidence).

DV4's laws hold on every admitted token: no company pipeline, no
provider-derived conviction, no rank without conviction, no
provider-derived strengths or risks, NOT_APPLICABLE never adverse,
MONITOR distinct from INVESTIGATE, and `digital-asset-gates@1` as the
provenance — asserted at the wire on an admitted token.

## 13. Other gates discovered

- **The funnel's counts and its named lists were computed from different
  expressions.** Admitting a candidate the request budget never reached
  made `evidenced` exceed `reviewed`, so the funnel would have reported a
  count contradicting the list printed beside it. Both are now derived
  from one `examined` set, so they cannot disagree; `reviewed` means
  *examined this cycle*, and a digital asset is examined for free.
- **`ExecutivePipeline` and the portfolio path apply no admission test**
  — every holding is evaluated, so held crypto was never affected.
- **`brain.attempted_candidates`** remains a provider-budget fact and is
  unchanged; it is now one of two ways into `examined` rather than the
  only one.
- No other independent evidence gate was found: `security_evidence` is
  consumed by the company committees and evidence builder, none of which
  a digital asset reaches after DV4.

## 14. Gates

`pytest -q` 3016 passed · ruff check + format clean · `mypy app` clean
(597 files) · `npm run build` + `tsc --noEmit` clean · production `data/`
byte-identical (the end-to-end run used a cloned evidence root).
