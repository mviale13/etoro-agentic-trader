# The Investment Decision

Status: **Proposed** (2026-08-08) — the CIO phase's first deliverable,
a design document only, per the owner's brief in
[`MIGRATION_PLAN.md`](MIGRATION_PLAN.md). Nothing here is implemented,
and nothing should be until the open questions at the end are closed
the way `KNOWLEDGE_CONSENSUS.md`'s were, with the decisions recorded
in this document.

---

## Why this document exists

The knowledge platform is closed. Everything beneath this layer
answers some form of *what do we know?* — an observation answers what
one reading found, a consensus answers what readings reliably find, an
understanding answers how the business creates value, a playbook
answers how the case should be analysed. The Artificial CIO answers a
question none of them can ask: **given everything we know, what should
the investor do — and why?**

That question will eventually be answered by an engine. This document
deliberately does not design the engine. It designs the *object* the
engine must produce — because the platform has learned, twice, that
the object comes first. `CompanyKnowledge` was designed before the
extractor, and every later capability grew around it without the graph
changing shape. `CommitteeDecision` was not designed at all — it
accreted around a vote — and it is now free text beside an
unexplainable integer, which no future engine should be forced to
speak. Whatever reasoning the CIO grows — rules first, committees
later, anything after that — every generation of it must emit the same
canonical object, so that surfaces, storage, audit and the investor
never have to care which engine was running.

The owner's constraints, carried from the knowledge platform and
binding on this design:

- It consumes established facts; it never establishes new ones.
- It may weigh evidence; it may never rewrite evidence.
- It must state what changed.
- It must state why it matters.
- It must state why it matters *for this investor*.
- It must distinguish uncertainty from disagreement.
- It must refuse conclusions unsupported by its inputs.
- Every recommendation must be explainable by walking backwards
  through the existing evidence graph.

---

## The governing principle

Stated before any mechanism, in the tradition this platform's design
documents follow:

> **A decision resolves disagreement, never uncertainty.** Uncertainty
> is inherited from the facts and passed on at its narrowest width;
> disagreement — admissible inputs implying different courses — is
> what deciding exists to adjudicate, by a named rule, with the losing
> implications preserved; and where the inputs support no resolution,
> the only honest outcome is a refusal that says why.

Every design decision below is tested against that sentence.

---

## Concepts kept apart

### Uncertainty and disagreement

These are different properties, owned by different layers, and the
sixth constraint exists because collapsing them is the standard defect
of scoring systems.

**Uncertainty is a property of the facts.** It is the width of a
consensus claim, the reason on an absence, the sub-quorum count on an
understanding. The fact layer already adjudicated its own internal
disagreement — that is what consensus *is*: representativeness among
observations. By the time a fact reaches the decision layer it is
settled-with-width or absent-with-reason, and **facts do not disagree
here**. A decision inherits their uncertainty untouched: it is exactly
as firm as the narrowest claim it consumed — the platform's standing
law, already carried by the archetype's `rests_on` — and no act of
deciding may narrow a width, any more than a citation could improve a
filing.

**Disagreement is a property of implications.** The business
understanding may support pursuing the case while the portfolio says
concentration forbids it and the market context says the moment is
wrong. Every one of those inputs is admissible; nothing about any of
them is uncertain in the fact layer's sense; and they still point in
different directions. *That* conflict is new in kind at this layer,
and resolving it is precisely what a decision is. The resolution is
made by a named rule, and the implications that lost are preserved in
the decision, the way a consensus preserves its minority answers —
adjudicated, never erased.

The symmetry with the layer below is exact, and worth stating because
it is the shape of the whole platform:

```text
Observations  →  Consensus   adjudicates representativeness among readings
Implications  →  Decision    adjudicates priority among courses of action
```

And the consensus layer's hardest-won rule carries upward unchanged:
**a decision selects among courses its inputs actually imply; it never
synthesizes a compromise nobody proposed.** Averaging a case for
pursuing and a case for avoiding into a hedged half-measure is the
decision layer's version of the composed set answer `{a, b}` that no
observation gave — an outcome with no provenance, which nothing could
walk backward to an input that implied it. `CommitteeDecision`'s
tallied votes with an averaged confidence are exactly this, and it is
foreclosed.

### An assessment and a decision

Analysts assess; only the Artificial CIO decides (invariant 6, and
constitution §9–10). An assessment is an *offered implication* — the
case has these merits, these risks, under this playbook — and it is an
input to disagreement, never a verdict. The decision is a commitment:
one outcome, for one investor, at one time, on a recorded basis. The
constitution already fixes the boundary vocabulary: analysts never
produce verdicts, and the CIO's output is one of
`REJECT · INVESTIGATE · MONITOR · PREPARE · RECOMMEND`. This document
does not invent a verdict vocabulary; it adopts the constitutional
one.

### A verdict and an action

The five verdicts are postures toward a case, not broker orders. Only
`RECOMMEND` carries a proposed position action — and MOVRvest
recommends, the investor decides, so even that action is a proposal,
never an execution. An action is expressible only relative to the
investor's current position (open, add, keep, trim, exit — you cannot
"buy" without knowing whether you hold), which is one of the two
reasons portfolio context is a mandatory input rather than an
enrichment. Where an action carries a magnitude, the magnitude is
**policy-room arithmetic** — the distance between the position's
current weight and the policy's own bound, computed by the platform
the way a `MeasuredShare` is computed — never a target the platform
invented. A magnitude the arithmetic cannot produce is absent, with
the reason, per invariant 1.

### A hold and a refusal

`MONITOR` on evidence — the case is understood, and what is known
supports keeping things as they are — is a decision. *Cannot decide* —
the inputs do not support choosing any verdict — is not a weaker
decision; it is a **refusal**, a different outcome entirely, carrying
its reason in the words of the layer that refused (the selector's
discipline: never re-word another layer's absence). A refusal-shaped
hold is the decision layer's counterfeit, the exact analogue of an
estimated figure on the dashboard, and the object makes it
unrepresentable: a verdict requires its supporting clauses, and a
refusal requires its reason, and neither can wear the other's clothes.

Note what the constitutional vocabulary already absorbs: much of what
looks like "cannot decide" is actually `INVESTIGATE` — a decision that
the case merits spending to learn more. Below-quorum knowledge on a
case worth having is not a refusal; it is the CIO deciding that the
next action is acquisition (`movrvest observe` — the explicit spend
that fills a consensus). Refusal proper is narrower: identity not
established, a mandatory context missing, a disagreement no rule
resolves. The engine's rule table will draw this line case by case;
the object only insists the two outcomes are distinct types.

### A decision and the current stance

A decision is an **event**. It happened at a time, on a recorded
basis, and the investor may have acted on it. It is therefore stored
append-only and never revised — a later decision **supersedes** it,
citing it, exactly as a new observation joins a store rather than
editing one. "The current stance" is not a second object to keep
consistent; it is the latest decision for the subject, served with its
age.

This is deliberately the opposite of the consensus, which is derived
on read and never stored — and the asymmetry is principled, not
inconsistent. A consensus is a pure function of stored observations,
so storing it would create a second place for it to be true. A
decision is a function of *perishable* inputs — the portfolio as-of,
the market as-of, the policy as versioned — and recomputing it later
on fresher inputs produces a *different decision*, not a correction of
this one. The historical act must survive; its inputs will not.

---

## The object

`InvestmentDecision`, at the level of meaning rather than code. Every
field earns its place against the eight constraints.

**Subject.** The instrument, under the platform's identity discipline
— the same checked identity the knowledge layer enforces before
reading. A decision about an instrument the platform cannot identify
is a refusal.

**Decided-at, and the occasion.** When the decision was made, and
*what changed* to occasion it: a new filing observed, a quorum filled,
a policy edit, a position drifted past a threshold, a scheduled
review, the investor asking. "First consideration of this subject;
nothing preceded" is an occasion. "Scheduled review; nothing material
changed; stance re-affirmed" is an occasion. The occasion names the
changed facts by reference — it is the third constraint made
structural, not a prose field.

**The basis** — every input, by reference, each dated or versioned,
partitioned into three kinds that are never blended, because they
carry three different kinds of authority:

- **Established facts.** The consensus (by store key, with its width
  and state), the business understanding, the playbook selection with
  its authority flag. These passed identity, grounding, applicability
  and consensus — the full chain. Only these are *facts* in this
  platform's sense. Analyst assessments, when that layer arrives on
  the new stack, join the basis here as what they are: offered
  implications over these same facts, never new facts.
- **Context observations.** The portfolio snapshot as-of, the market
  context as-of. These are provider-reported and uncalibrated — the
  platform has already recorded that a single market read can flip
  between runs, and a flipped run must never silently flip a stance.
  Context enters the basis labeled as what it is: width-1,
  unverified observation. A clause may rest on it only by saying so.
- **Declared policy.** `config/policy.yaml`, versioned — the seed of
  the for-this-investor clause. Policy is not evidence at all; it is
  the investor's own instruction, and it is the one input the decision
  obeys rather than weighs. It is also the answer to *which investor*:
  a decision is made under one policy version, and a policy edit is an
  occasion to decide again, never a reason to re-read an old decision
  differently.

**The outcome.** Exactly one of:

- a **verdict** — `REJECT`, `INVESTIGATE`, `MONITOR`, `PREPARE`, or
  `RECOMMEND`, with a position action (and its policy-room arithmetic)
  attached to `RECOMMEND` only; or
- a **refusal** — no verdict, with the refusing layer's reason
  verbatim.

**The three clauses.** The Executive Brief's questions (constitution
§11) are answered *here*, structurally, and merely worded downstream —
Communication explains decisions; it never makes them, so everything
the brief will say must already be present in the object with edges:

1. **What changed** — the occasion, with references to the changed
   facts or contexts.
2. **Why it matters** — materiality for the case, stated in the
   playbook's and understanding's own terms, with references to the
   consensus claims consumed.
3. **Why it matters for this investor** — the policy clauses and
   portfolio facts that make it this investor's concern, with the
   arithmetic shown.

The clauses fail independently, and the object keeps them apart for
the same reason a segment is three claims evidenced apart: a fact can
matter for the case and not for this investor (no allocation room; the
position already at its cap), and the difference between those two is
frequently the entire content of the decision.

**What it rests on.** The narrowest agreement among all consumed
consensus claims, distribution included, plus every absence consumed,
verbatim. A decision's firmness *is* this field; there is no other.
Nothing in the object is a probability, a score, or a confidence
integer — the uncertainty vocabulary is the platform's one vocabulary
(`Agreement`, widths, worded absences), per invariant 9.

**The disagreement record.** The implications weighed, the courses
they proposed, which rule resolved them, and what lost. An empty
record is itself a statement: nothing in the basis opposed the
outcome. This field is the second half of the sixth constraint — the
first half lives in *rests-on* — and it is what "may weigh evidence"
means made visible: weighing is recorded ordering, never rewording.
The facts appear in it by reference, verbatim; the only content this
layer adds is which course prevailed and under which rule.

**The deciding rule.** The named rule that produced the outcome —
`rule_fired`, exactly as `PlaybookSelection` records it. Whatever
engine exists behind the object, a decision that cannot name its rule
cannot exist. This single field is what makes every future engine
replaceable: engines compete to fill the same object honestly, and the
object never learns which one did.

**The predecessor.** A reference to the decision this one supersedes,
or the worded statement that none preceded. The chain of decisions for
a subject is the investor-visible history of the platform changing its
mind, and it must read as *this superseded that, because this fact
changed* — never as an edit.

---

## Where the decision sits in the evidence graph

The platform is an evidence graph, not a retrieval system: every claim
carries its relationships explicitly, each edge checkable, each
checked by a different boundary. The decision does not sit beside that
graph — it **extends it upward**, with its own explicit edges:

```text
Source ── identity ──▶ Document ──▶ Cell / Span
                                        │ applicability / ownership
                                        ▼
                                     Claim
                                        │ consensus (representativeness)
                                        ▼
                                  Settled fact ──── consumed-by ───▶ Clause
                            Context observation ─── informs ──────▶ Clause
                                 Policy clause ──── governs ──────▶ Clause
                                                                      │
                                                          supports    ▼
                                              Clause ──────────▶ Outcome
                                  Decision ── supersedes ──▶ prior Decision
```

Walking backwards from a verdict therefore reaches, in order: the
clauses that support it, the facts and contexts each clause consumed,
the consensus each fact settled under, the observations behind the
consensus, the spans and cells behind the observations, and the
identity-checked document behind those — the eighth constraint,
satisfied by construction rather than by effort. **A clause that
cannot name its edges cannot be stated, and a verdict whose required
clauses cannot be stated cannot be reached** — which collapses the
seventh constraint (refuse unsupported conclusions) from a virtue the
engine must possess into a shape the object enforces.

The owner's rule on the Evidence Graph abstraction is respected: these
are the decision's own explicit edges, named and checked locally, the
way `_referenced` and `_continues` exist today — not a premature
generalized graph. If the decision layer becomes the third mechanism
that converges on the abstraction, that is the earned trigger the
migration plan already records, and it is taken *then*.

Replay is the audit primitive this buys: a decision records its basis
by reference, so the deciding rule can be re-run against the recorded
basis and must reproduce the outcome — the decision layer's analogue
of reading a cited cell back. A decision that cannot be replayed from
its own record is remembered, not explained.

---

## Reconciliation under invariant 9

One business concept, one implementation. When this object lands,
these existing objects are reconciled — in a later slice, with the
inventory updated, not by this document:

- **`CommitteeDecision`** cannot be the canonical object, and now the
  reasons are precise: its `recommendation: str` is a semantic payload
  in free text; its `confidence: int` is an unexplainable number with
  no basis edges; its vote tallies are a *survey* of conclusions — the
  pattern `KNOWLEDGE_CONSENSUS.md` forecloses at the fact layer
  (conclusions must be functions over facts, never votes over
  conclusions) reappearing one layer up; it has no refusal, no
  occasion, no investor clause, no predecessor, and nothing in it can
  be walked backward. Its one durable content — the per-analyst
  `opinions` — survives as what it always was: assessments, offered
  implications, basis inputs to a real decision.
- **`Recommendation`** (the wrapper carrying snapshots beside a
  `CommitteeDecision`) is the closest existing shape to
  decision-with-context, and it dissolves into the basis: its
  snapshots become dated context references instead of embedded
  copies.
- **`policy.yaml`** gains an explicit domain object and a version
  identity, because the for-this-investor clause must cite the policy
  it was decided under.

The research path keeps consuming its existing objects unchanged until
the flip — the playbook migration rule, applied again: outgrown, one
authoritative case at a time, the two routes never blending.

---

## What this model forecloses

- A confidence integer, probability, or score of any kind, anywhere.
- A free-text field as the semantic payload of an outcome.
- A hedged hold standing where a refusal belongs.
- A compromise action no input implied — splitting the difference is
  synthesis, and synthesis is generation.
- A decision revised in place, for any reason, including being wrong.
- Ambient context — policy, portfolio or market read at explanation
  time rather than recorded at decision time.
- A clause resting on context-grade observation without saying so, and
  any silent blending of the three basis kinds.
- Communication adding, strengthening, or softening a clause — the
  brief renders the object, and the object is complete before the
  brief exists.
- An engine establishing one more fact mid-decision because the basis
  was one fact short. The gap is an absence in the basis; the decision
  inherits it or the outcome is `INVESTIGATE`; nothing fills it here.

---

## Open questions for the design conversation

1. **The verdict set.** Adopting the constitutional five plus refusal:
   is `REJECT` terminal for a subject (a standing stance that ends
   reconsideration until a named occasion revives it), or just another
   supersedable stance? And does `INVESTIGATE` formally own the
   below-quorum case — making observation acquisition a *decided
   spend* with a decision behind it, rather than a side effect of
   anything?
2. **Magnitude.** Is policy-room arithmetic the whole of sizing in the
   canonical object (open up to X% of the portfolio before the cap),
   with anything finer — conviction weighting, tranching — refused as
   unsupported until some future layer earns it?
3. **Scope.** This object is per-subject. A rebalance is a
   portfolio-level occasion that implies several per-subject decisions
   plus a policy clause (`rebalance_threshold`). Is a portfolio
   decision a composition of these objects under one occasion, or a
   distinct object — and does v1 need it at all?
4. **Occasions.** Which occasions exist at birth — new-filing, quorum
   filled, policy edit, investor request, scheduled review — and is
   the occasion list closed (like the verdict list) or open (like
   absence reasons)?
5. **Context calibration.** Filing-grade evidence earned its trust
   through measurement (`reader-stability`). Context-grade evidence
   has no analogue — the platform knows market reads flip between
   runs, but has never dimensioned it. Does a clause resting on market
   context need a stability measurement of that feed before any
   verdict may rest on it, or is the width-1 label sufficient for v1?

---

## What acceptance would mean

Accepting this document fixes the language: every future engine —
the first deterministic rule set, committees when they return, and
anything after — produces `InvestmentDecision`s and nothing else, the
way every reader produces observations and nothing else. The next
design session after acceptance is the engine's rule table for the
first verdicts the corpus can actually earn — JPM holds an
authoritative playbook today, and the first real decision this
platform makes should be about a company whose every supporting link
is already checkable.
