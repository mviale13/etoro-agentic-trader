# The Decision Bridge

**Status: accepted and built (2026-08-16).**

The smallest honest path from *the committees know things* to *the
investment system can consume what they know*.

The question the slice was given: **given the judgments the committees
have independently produced, what information is legitimately allowed to
influence an investor-facing decision?**

The answer the investigation produced: **the conclusions themselves, and
nothing about what they are worth** — because no layer of this platform
has ever established the second thing, and two of them say so explicitly
in their own vocabularies.

---

## 1. The investigation, before any design

### Where committee conclusions stop

Every module that imports the crypto committee layer, and what it is:

| module | kind |
|---|---|
| `services/committee_matrix_service`, `services/judgment_history_service` | the layers themselves |
| `domain/committee_matrix`, `domain/judgment_history`, `domain/committee_protocol` | the domain |
| `infrastructure/evidence/judgment_history_store` | persistence |
| `commands/committees`, `commands/judge`, `commands/judgment_history`, `commands/committee_judgment` | CLI |
| `api/routes/committee_matrix`, `api/routes/crypto_dossier` | read-only surfaces |
| `services/investor_assessment_service` | the assessment layer |
| `renderers/intelligence_synthesist`, `services/intelligence_synthesis_service` | the LLM narrator |

**Nothing that decides anything appears.** Measured as transitive
reachability from the nine named decision modules:

```text
app.cio.artificial_cio                                   no
app.cio.decision_policy                                  no
app.cio.executive_decision                               no
app.domain.investment_decision                           no
app.application.executive.decision_evidence_builder      no
app.application.executive.decision_synthesis_builder     no
app.application.thesis.investment_thesis_builder         no
app.application.workspace.executive_pipeline             no
app.application.workspace.ranking                        no
```

The only non-display consumers are the two synthesis modules, which
communicate and never decide — Invariant 7.

### Where investor-facing decisions come from instead

`ArtificialCIO.decide()` takes one input, `DecisionEvidence`. Every
branch of `_determine_state` tests `hard_reject`, `analyst_veto`,
`security_evidenced`, or one of `risk_score` / `quality_score` /
`evidence_score` / `valuation_score` / `portfolio_fit_score`. Conviction
averages those scores. **There is no structural input of any kind.**

### The crypto dossier has no decision field at all

Every section of every one of the eight assets, searched for keys
matching *conviction, recommend, score, rating, grade, rank, target,
action, buy, sell, weight, allocation*:

| asset | decision-shaped keys |
|---|---|
| 1INCH, ADA, ARB, BTC, ETH, HYPE, SOL, TAO | **0** |

The one band-shaped field is Asset Quality, and it reads `UNKNOWN` for
all eight with `scorable=1` against a quorum of 2 — S5's design, holding.

### Two unrelated things are both called "committee"

`DecisionEvidence.opinions` is `tuple[CommitteeOpinion, ...]` from
`app.domain.committee.opinion` — the **equity** layer (#77). The crypto
committees produce `CommitteeJudgment` → `JudgmentRecord` →
`CommitteeAssessment`, a type the CIO never imports.

**And the equity opinion does not move the decision either**, which is
the strongest single finding of the investigation. From
`artificial_cio.py`:

> Carried through untouched. The CIO gates on scores; it neither reads a
> committee's position nor edits one.

The plumbing this slice was asked to build already exists on the equity
side, and is deliberately inert.

---

## 2. What can be combined honestly

### Structural fact exists. Investor interpretation does not.

Three independent pieces of evidence, none of them invented here:

- **An `EligibleFinding` carries no sense.** Its fields are `ref`,
  `stated`, `claim_type`, `established_by`, `observations`. The equity
  `Finding` carries a `Sense`, recorded by the signal that read it — and
  that is exactly what `Stance` counts. The crypto evidence stream has
  no polarity to count.
- **Supply Governance refuses ordering, with the reason written down.**
  Its own verdict vocabulary: *"Deliberately not ordered. A
  protocol-fixed rule is harder to change and that is not the same as
  better: a rule nobody can change is also a rule nobody can fix, and
  this platform has established no view on which an investor should
  prefer. There is no `rank`, and adding one would mean editing this
  file with the reason written down."*
- **Fee Capture's `MECHANISM_EVIDENCED` is documented as a structural
  fact and explicitly not a favourable one** (#112).

So the domain has already refused, in writing, the exact transformation
a numeric bridge would need. The bridge does not re-open that question.

---

## 3. What was built

`InvestmentConsideration` — one committee's conclusion, addressed to an
investment layer:

```text
committee identity + contract fingerprint
question                    the committee's own words
posture                     five states, never collapsed
applicability
conclusion / stated         quoted, present only when answered
because                     the committee's own account
confidence                  carried, never compared
effect                      what it means for an investment case
policy_version              which rule set decided that
judgment_id                 the exact record it rests on
comparability
refs, evidence_count, evidence_semantics
```

`AssetConsiderations` collects them per asset with **no aggregate** — no
overall, no score, no agreement, no rank — and names the committees that
have recorded nothing at all, because *nobody asked* and *we asked and
got no usable answer* are different facts.

### The effect vocabulary has one member

```python
class InvestmentEffect(StrEnum):
    UNRESOLVED = "unresolved"
```

Not a placeholder. A second member means adding a rule to
`LICENSED_EFFECTS`, and adding a rule means writing down who established
it. The table is **empty**, keyed on `(committee key, verdict token)` —
a lookup rather than a branch, so a third committee resolves through the
same line as the first two and needs no edit here.

### It knows nothing about any committee

No import of a committee implementation. No committee key. No verdict
token. No vocabulary from fees or supply. Guarded by an AST scan that
strips docstrings and comments before looking, so the module can explain
*why* it knows nothing without the guard mistaking the explanation for a
rule.

---

## 4. Persistence: a projection, not a record

§7 asks which model preserves historical truth more cheaply. A
consideration is a **deterministic function of an immutable, versioned
judgment and a versioned licensing table**, so it can always be
recomputed and needs no store, no schema and no migration.

What it must not lose is the version, and it does not:
`BRIDGE_POLICY_VERSION` rides on every consideration. If a rule is added
later, a projection taken today and quoted tomorrow still says which
rules made it — PR #127's principle, applied without PR #127's cost.

---

## 5. Corpus measurement

*(see the report accompanying the slice for the rendered matrix)*

Sixteen judgments consumed, sixteen considerations produced, and **zero
with an established investment effect**. The postures are all five, and
they survive the crossing intact.

A high unresolved count is what the domain knows. Invented certainty is
what it refuses.

---

## 6. Why there is no new dossier section

§11 permits one. It was measured and declined.

The crypto dossier already renders every committee's conclusion — with
its question, applicability, reasoning, confidence and provenance — in
*What each committee concluded*. A second section reading *What the
committees establish* would print the same conclusions again, which is
precisely the defect PR #126 spent a slice removing, arriving one slice
later under a new name.

The bridge's value is what it makes *possible*, and nothing consumes it
yet. `movrvest considerations [SYMBOL]` renders it for inspection; when a
real consumer exists, that consumer earns the surface.

---

## 7. The architectural question, answered

> Can MOVRvest move from *the committees know things* to *the investment
> system can consume what they know* without inventing the missing
> investment philosophy?

**Yes — and the shape of the answer is the finding.** The committees'
conclusions now travel in a typed, provenance-carrying object that an
investment layer can consume. What does not travel is any claim about
what they are worth, because that claim does not exist anywhere in this
platform: not for crypto, and not for equity, where the same wire is
already strung and already inert.

The bridge is therefore complete and connected to nothing, on purpose.
The next question is not *how do we weight these* but **who is allowed
to establish that a structural conclusion improves an investment case,
and on what evidence** — an investment-policy layer that does not exist,
and that this slice deliberately did not invent.
