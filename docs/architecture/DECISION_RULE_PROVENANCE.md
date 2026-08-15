# Decision Rule Provenance

**Status: accepted and built (2026-08-16). Zero behaviour change,
proven.**

The Decision Philosophy Audit established that MOVRvest's decision
philosophy is implicit rather than incoherent: eighteen decision-bearing
transformations, one licensed. This slice makes every one of them
explicitly identifiable and versioned **without changing a single
decision** — describing the machine, not endorsing it.

Every decision-bearing score and gate can now answer: *which exact rule,
and which version of that rule, gave this input its investment meaning?*

---

## 1. The typed representation, and why

`DecisionRule` (`app/domain/decision_rules.py`): `key`, `version`,
`status`, `kind`, `because`. Frozen, slotted, immutable at the type.

- **`RuleStatus`** preserves the audit's three-way distinction
  structurally — `LICENSED` / `ARGUED` / `UNSOURCED` — so naming a rule
  cannot quietly upgrade it. A test asserts exactly one rule is
  LICENSED (grounded quality) and exactly one ARGUED (risk severity);
  a status cannot move without that test moving beside it.
- **`RuleKind`** answers the brief's interpret-vs-govern question:
  `INTERPRETS_EVIDENCE` (bands, score maps, confidence formulas) or
  `GOVERNS_DECISION` (gates, vote thresholds, veto mappings). A test
  asserts the kinds partition the registry.
- **`because`** carries the licensor, the argument's location, or the
  honest absence — never consulted by any code path.

**`ScoreBasis` was confirmed as the carrying boundary** and gains one
field: `rules: tuple[DecisionRule, ...]`. The shape is owner-frozen;
this brief is the owner's decision, and it is recorded in the module's
own ruling note as the freeze requires. The evidence graph is not
duplicated: `ScoreBasis` already carries the prose and evidence, and the
rules ride beside them.

Other carriers, each the smallest that fits:

| value | carrier | rules carried |
|---|---|---|
| the four signals | `rule` on `ValueSignal`/`QualitySignal`/`MomentumSignal`/`RiskSignal` | its band rule, `None` where nothing was banded |
| the vote | `rules` on `CompanyRecommendation` | `signal-vote@1`, `vote-confidence@1` |
| the five scores | `rules` on each `ScoreBasis` | the interpretation chain, in order |
| the action flags | `rules` on `DecisionEvidence` | `actionable-buy@1`, `veto-sell@1` |
| the decision | `decided_under` on `ExecutiveDecision` | `decision-gates@1`, `conviction-mean@1` |

**A rule is stamped exactly where a meaning was assigned, never where
its absence is explained.** A basis explaining an unmeasured score
carries no rules; a signal reading UNKNOWN from absent data carries
none; a grounded UNKNOWN from too few answered factors carries none.
Stamping those would claim a meaning was assigned when none was.

---

## 2. The rule inventory

Sixteen rules cover the audit's eighteen transformations. Granularity
follows behaviour, not literals: the provider triad's points, bands and
score map are one rule (they move together — audit #6+#7); the risk
bands and the risk severities are two (rebanding volatility and
re-pricing a band are different decisions — audit #1, #2).

| rule | audit # | kind | status | governed constants |
|---|---|---|---|---|
| `risk-bands@1` | 1 | interprets | unsourced | vol 0.20/0.35/0.60, dd 0.20/0.40 |
| `risk-severity@1` | 2 | interprets | **argued** | 0.20/0.45/0.65/0.85 |
| `pe-bands@1` | 4 | interprets | unsourced | <18 / <28 |
| `valuation-scores@1` | 5 | interprets | unsourced | 80/55/25 |
| `provider-quality@1` | 6, 7 | interprets | unsourced | $10bn, 3 factors, bands, 80/62/40 |
| `quality-grounded@1` | 8 | interprets | **licensed** | ≥2 answered, 2/3, 1/3, 80/62/40 |
| `momentum-bands@1` | 9 | interprets | unsourced | ±0.5 / ±2.0 |
| `signal-vote@1` | 10 | governs | unsourced | 0.40/0.35/0.25, ±0.5 |
| `vote-confidence@1` | 11 | interprets | unsourced | 50 + \|s\|·50 |
| `cognitive-confidence@1` | 12 | interprets | unsourced | floor 0.50, constant 0.80, mean of three |
| `evidence-score@1` | 13 | interprets | unsourced | mean, ×0.6 discount |
| `portfolio-fit@1` | 14 | interprets | unsourced | mean of policy rooms ×100 |
| `decision-gates@1` | 15 | governs | unsourced | the nine `DecisionPolicy` defaults |
| `conviction-mean@1` | 16 | governs | unsourced | caps 40/55/70/85/100 |
| `actionable-buy@1` | 17 | governs | unsourced | BUY → execution trigger |
| `veto-sell@1` | 18 | governs | unsourced | SELL → veto |

Audit #3 (the risk-ceiling gate) is a threshold *of* `decision-gates@1`
(`maximum_acceptable_risk` is one of the nine fingerprinted policy
fields); its written argument lives with `risk-severity@1`, which is
what the argument is about.

**No provenance was upgraded by naming.** Fifteen of sixteen rules are
exactly as unsourced or argued as the audit found them.

---

## 3. The guard: a pinned fingerprint per rule

`tests/test_decision_rule_provenance.py` holds a `(key, version,
status, fingerprint)` pin for every rule, where the fingerprint is
hashed from the **live constants in the owning modules**. Changing a
rule is therefore a two-place, written-down act — move the constant
*and* re-pin the row with the new version. Mutation-checked, all five
biting:

| mutation | outcome |
|---|---|
| FAIR 55 → 60 under the same version | `valuation-scores` pin fails |
| version 1 → 2 with no behaviour change | pin fails |
| quietly upgrade `pe-bands` to LICENSED | pin **and** exactly-one-licensed fail |
| drop the rules from a scored basis | carriage test fails |
| add `if evidence_score < 73:` to the CIO | anonymous-threshold guard fails |

The anonymous-threshold guard is architectural rather than a keyword
ban: it parses the six governed modules (four signal services, the vote,
the CIO) and rejects any comparison against a bare numeric literal other
than 0 — a threshold must be a named attribute, which is exactly what
makes it fingerprintable. Four constants were hoisted to names to pass
it (`PE_CHEAP_BELOW`/`PE_FAIR_BELOW`, `CONFIDENCE_BASE`/`SPAN`,
`CONVICTION_LIMITS`, `UNEVIDENCED_DISCOUNT`, plus the two cognitive
constants) — hoists only, values untouched.

---

## 4. Zero behaviour change, proven

The audit's corpus script rerun on the branch against its `main`
capture: **the entire output is byte-identical** — all fourteen
securities' inputs, every intermediate score, every boolean, every
vote, every state, every conviction, every binding-gate rationale, and
all 476 trials of the causal-authority mutation grid. The ugly
behaviour is intact by measurement: the FAIR wall stands, the dividend
wall stands, the one-day momentum bands stand, the veto's authority
stands, MONITOR remains unreachable, `hard_reject` remains dead.

No payload changed: the API and journal pick fields explicitly, so the
new fields reach neither unless a surface deliberately asks.

---

## 5. Transformations that took provenance indirectly

- **`cognitive-confidence@1`** spans three analysts whose assessments
  are shared, account-level objects consumed by many surfaces; stamping
  a decision rule on them would claim account reasoning is a decision
  artifact. The rule rides where the mixture becomes a decision input —
  the evidence `ScoreBasis` — and the two constants it governs are
  named on their analysts for the fingerprint.
- **`decision-gates@1`** thresholds already live in a typed, named
  object (`DecisionPolicy`); the decision carries `decided_under`
  rather than the policy carrying rules, because the policy is an
  input and the gating is the behaviour.

Everything else carries its rules directly on the produced value.

---

## 6. The two committee packages (§8)

Both are live, and the relationship is **intentional layering by
subject with naming debt**:

| | `app/committee/` | `app/application/committees/` |
|---|---|---|
| subject | the **market and account** (default symbol SPY) | **one investment case** |
| members | chairman, cash, momentum, value, risk, diversification | Investment, Risk |
| output | `Recommendation` (BUY/HOLD/SELL about the market regime) + regime weights | `CommitteeOpinion` (stance over referenced findings) |
| consumers | `RecommendationPerception` (the `/brain` surface), `daily`, `explain`, `doctor`, watchlist, brief, `movrvest committee` | the executive pipeline → synthesis, renderers |
| reaches `decide()`? | **no** — `BrainBuilderService.build` does not run it | opinions carried, deliberately inert (#129 §4) |

The follow-up finding: the old package still emits an *action*
vocabulary (BUY/SELL) that #77 removed from the security layer on
Constitution §9 grounds — defensible at market-regime altitude only
because nothing decision-bearing consumes it. Recorded as debt: three
things are called "committee" (market, security, crypto) and only the
newest two share a philosophy. Not consolidated in this slice.

---

## 7. Recommendation: the first rule to examine

**`valuation-scores@1`, jointly with `pe-bands@1`.** The audit measured
its causal authority as concentrated entirely at the RECOMMEND boundary
— the FAIR wall is these two rules touching `decision-gates@1` — and
the live corpus has never exercised FAIR, so the wall has never been
*seen*, only latent. It is the smallest rule whose examination forces
the real question this whole arc has been approaching: **who is allowed
to establish that a price level improves an investment case, and on
what evidence.** Not repaired here.
