# The Valuation Comparison Boundary

**Status: accepted and built (2026-08-16).** The first implementation
slice after the Valuation Authority investigation: Observation →
Comparison, and nothing past it.

The platform now knows *less* about valuation than it appeared to know
yesterday, and every remaining claim is true. That trade is the slice.

---

## 1. The unsupported claims found, exactly

Measured on the live corpus before any change:

- **9 securities** carried the false evidence sentence — 8 ×
  *"Forward P/E below historical market average."* (sense: favourable)
  and 1 × *"…above historical market average."* (sense: adverse,
  SPCX). No "historical market average" observation exists anywhere on
  this platform; the actual comparand was the constant 18.
- **1 market-level site** — the old Value committee
  (`app/committee/value.py`) — produced *"Forward P/E is attractive."*
  / *"elevated."* / *"reasonable."* from its own independent copy of
  the band (**18/30**, against `pe-bands@1`'s 18/28): interpretation
  vocabulary resting on no benchmark, feeding the `/brain` market
  recommendation.
- The valuation `ScoreBasis` opened *"Valuation reads CHEAP, from the
  findings below"* — presenting a house classification as a reading of
  evidence, directly above the false finding.
- 0 securities held a legitimate comparison. FAIR was not exercised.

## 2. The typed representation

`app/domain/valuation_comparison.py` — four shapes, one boundary:

- **`ValuationObservation`** — metric, label, value, unit, provenance.
  `stated` is the whole claim an absolute multiple licenses:
  *"Forward P/E of 17.4×."*
- **`ValuationBenchmark`** — name, value, `Provenance`, non-empty
  `evidence`. Construction raises without any of them: **a constant in
  code cannot become one**, because a constant has no reading and no
  evidence. `pe-bands@1`'s 18 was not grandfathered.
- **`ValuationComparison`** — observation + benchmark + descriptive
  relation (BELOW/WITHIN/ABOVE — *not* cheap/expensive) + a named,
  versioned `DecisionRule` + `because`. Refuses construction without a
  real benchmark. Its `stated` carries the whole chain.
- **`AbsentComparison`** — the honest third state and the live state of
  every security today: an observation held, no benchmark held. **Not
  neutral, not FAIR** — its stated form is the observation alone, and
  its `because` names the constant for what it is.

`ValueSignal` carries `observation` and `comparison`. The two absences
stay distinct: no multiple at all → UNKNOWN with neither field; a
multiple with no benchmark → `AbsentComparison`.

## 3. What was withdrawn or corrected

| site | before | after |
|---|---|---|
| value signal finding (all three bands) | *"below/above historical market average"* / *"within a reasonable range"*, favourable/adverse/neutral | **the observation only** — *"Forward P/E of 9.6×."*, always neutral |
| valuation `ScoreBasis` | *"Valuation reads CHEAP, from the findings below…"* | *"No valuation benchmark is held… the platform's legacy valuation policy (pe-bands@1, unsourced) classes it CHEAP against its own fixed bands — a house rule, not an evidenced comparison…"* |
| old Value committee rationales | *"attractive" / "elevated" / "reasonable"* | *"below/above/within this committee's own fixed band — legacy policy, not an evidenced comparison"*, with the P/E value stated |

The sense demotion is deliberate and disclosed: a favourable CHEAP
finding asserted that an unsourced band argues *for* a security.
Withdrawn, the finding no longer counts as supporting evidence in
committee stances — measured: a controlled Investment Committee fixture
drops from 3 supporting to 2. That is a display-layer honesty gain;
no decision field moves (§5).

## 4. Behaviour preservation, proven

- `pe-bands@1`, `valuation-scores@1`, `decision-gates@1` untouched —
  the provenance pins from #130 confirm no constant moved.
- Band edges and confidences pinned in the new tests (17.9→CHEAP,
  18.0→FAIR, 27.9→FAIR, 28.0→EXPENSIVE; 90/80/85).
- **The decision corpus is byte-identical**: the audit's full
  measurement script — all 14 securities' inputs, scores, booleans,
  votes, states, convictions, binding gates and the 476-trial
  causal-authority grid — reruns identical to the last byte.
- Analytical surface, before → after: P/E observations 14 → 14;
  comparison claims **9 → 0**; band words in findings 0 → 0;
  unsupported benchmark sentences **9 → 0**; securities with a
  legitimate comparison 0 → 0 (honest: none exists).

## 5. The guards

`tests/test_valuation_comparison.py` (16 tests). The primary guard is
structural and by equality, not a word blacklist: a banded signal's
finding must equal its observation's own stated form, so *any*
substituted language breaks it. Mutations, all five biting:

| mutation | failed by |
|---|---|
| hard-code 18, claim "below benchmark" in the finding | equality with the observation |
| produce CHEAP language / favourable sense with no comparison | equality + neutral-sense guard |
| strip the benchmark-evidence requirement from the type | constructor-refusal test |
| substitute benchmark language into `AbsentComparison.stated` | equality guard |
| restore "attractive" in the old committee | AST string-literal scan (comments exempt, so the module may still *explain* the withdrawn words) |

## 6. SPCX, confirmed and recorded

The mapping table is correct (`_ETORO_ASSET_TYPES`: 5 → STOCK,
6 → ETF). The defect is upstream: **eToro's own instrument metadata
reports SPCX (instrument 15618) with `asset_type_id` 5**, so the
platform classifies the SPAC and New Issue ETF as a stock on the
broker's word, with no cross-check — and every company question
follows (P/E 71.8 → EXPENSIVE, LOW quality, SELL veto). F1's
`has_no_company` boundary is right and never fires because the class
never becomes ETF. **Entry boundary: broker-supplied classification,
trusted unverified** — the same provider-hygiene family as the ×100
`dividendYield`. Next planning decision, not this slice.

## 7. The duplicate Value committee

Confirmed making the same class of unsupported claim, now corrected
under the same invariant: votes, thresholds (18/30) and confidences
untouched; the rationale names its own fixed band as legacy policy.
The architectures were not consolidated; the second copy of the band
constant remains, recorded as debt (it is outside `pe-bands@1`'s
fingerprint, in a package the provenance guard does not govern).

## 8. Residuals, recorded not repaired

- `SCORE_LABELS["valuation"] = "Valuation attractiveness"` — the
  score's display label still names an interpretation; renaming
  touches every equity surface and belongs with the Interpretation
  layer decision.
- `CompanyRecommendation.summary` still reads *"value is cheap…"* —
  the legacy vote's self-account.
- The CIO's PREPARE rationale *"The company is attractive, but
  valuation does not currently support action"* — decision-machine
  wording, preserved for byte-identity.

## 9. Recommendation: the first legitimate benchmark, if any

Unchanged from the authority investigation, sharpened by this slice's
type: the first candidate worth *investigating* is **market-implied
expectations under a named, versioned model** — it is the only
candidate that produces a `ValuationBenchmark`-shaped thing honestly
(a value with provenance and checkable evidence: the price, the base
earnings, the model's parameters), and its output feeds
`ValuationComparison` without touching Interpretation. A peer-median
or own-history benchmark would also fit the type's demands but imports
a mean-reversion preference the platform has not established. If
nothing is built, the corpus stays at `AbsentComparison` everywhere —
which is now a true statement, rendered honestly.

Not implemented here.
