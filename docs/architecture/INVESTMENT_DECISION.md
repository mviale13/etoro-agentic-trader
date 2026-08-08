# The Investment Decision

Status: **Proposed, accepted in principle** (2026-08-08) — the CIO
phase's first deliverable, a design document only, per the owner's
brief in [`MIGRATION_PLAN.md`](MIGRATION_PLAN.md). The owner accepted
the governing principle as the foundation and closed the five open
questions the same day — the closures are recorded at the end, in the
tradition of `KNOWLEDGE_CONSENSUS.md` — and proposed one amendment,
the decision question, which is explored and integrated below. The
freeze awaits the owner's confirmation of the integrated amendment;
nothing is implemented before it.

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

The five verdicts are postures toward a question — the concept a later
section establishes — not broker orders: `REJECT` answers the question
in the negative and closes the case against it (supersedable, like
every stance); `MONITOR` declines to answer now and keeps the question
open; `PREPARE` readies the question's affirmative and names the
trigger it waits on; `INVESTIGATE` defers the question and raises the
spend question; `RECOMMEND` answers in the affirmative, made concrete.
Only `RECOMMEND` carries an action — and MOVRvest recommends, the
investor decides, so even that action is a proposal, never an
execution. The action is the question's affirmative made executable.
For the position questions that means a position action expressed
relative to the investor's current holding — you cannot "add" without
knowing what is held, which is one of the two reasons portfolio
context is a mandatory input rather than an enrichment — with
magnitude as **policy-room arithmetic**: the distance between the
position's current weight and the policy's own bound, computed by the
platform the way a `MeasuredShare` is computed, never a target the
platform invented. For the spend question it means an observation run,
its count and cost fixed in the action itself. A magnitude the
arithmetic cannot produce is absent, with the reason, per invariant 1.

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
looks like "cannot decide" is actually `INVESTIGATE` — the decision
that the question is worth answering and that the gap in its basis is
acquirable. How that verdict relates to the spend question is fixed in
a later section. Refusal proper is narrower: identity not established,
a mandatory context missing, a question no rule table answers, a
disagreement no rule resolves. And a refusal names the question it
refused, because a refusal is never neutral in effect — refusing
*should this security enter?* leaves the investor out, while refusing
*should this position decrease?* leaves the investor in. The engine's
rule table will draw the refusal line case by case; the object only
insists that verdict and refusal are distinct types, and that both are
question-scoped.

### A decision and the current stance

A decision is an **event**. It happened at a time, on a recorded
basis, and the investor may have acted on it. It is therefore stored
append-only and never revised — a later decision **supersedes** it,
citing it, exactly as a new observation joins a store rather than
editing one. Supersession runs within one stream: a new answer to a
question supersedes the previous answer to *that* question. "The
current stance" is not a second object to keep consistent; it is the
subject's latest answer per question, served with its age.

This is deliberately the opposite of the consensus, which is derived
on read and never stored — and the asymmetry is principled, not
inconsistent. A consensus is a pure function of stored observations,
so storing it would create a second place for it to be true. A
decision is a function of *perishable* inputs — the portfolio as-of,
the market as-of, the policy as versioned — and recomputing it later
on fresher inputs produces a *different decision*, not a correction of
this one. The historical act must survive; its inputs will not.

---

## A decision answers one question

The owner's amendment at acceptance: *the object defines the verdict
but not the question being answered.* Explored here before the freeze,
and integrated — because once stated, the model is visibly incomplete
without it.

The argument is the platform's own third boundary, reappearing one
layer up. Identity, grounding and applicability are independent
invariants below, and the standing exhibit is the JPM boilerplate: a
span can be perfectly grounded and still fail to support the claim it
was cited *for*. A verdict has exactly this failure mode. It proves an
adjudication happened; it cannot, by itself, say *what was
adjudicated*. `MONITOR` on a security means one thing as the answer to
*should this enter the portfolio?* — not yet, keep watching — and the
opposite-in-effect thing as the answer to *should this position
decrease?* — no, stay in. Same subject, same basis, same verdict,
different meanings. A verdict without its question is a grounded span
cited for nothing in particular, and the cure is the one the evidence
layer already paid for: the relationship is carried explicitly, or the
object is invalid. The decision's boundaries therefore mirror the
chain's:

```text
subject   — identity        whose case this is
edges     — grounding       what the clauses rest on
question  — applicability   what the verdict is an answer to
```

Each decision answers **exactly one** question. An occasion may raise
several — one filing arriving can raise the entry question for a
security not held and the spend question for its thin consensus — and
each raised question is its own decision, with its own basis, verdict
and stream.

Two further consequences surfaced while testing the amendment, and
each argues the question is domain, not engine:

- **The same evidence legitimately answers different questions
  differently** — the owner's core claim, and it holds structurally.
  The question cannot be derived from the subject and the position
  state, because a held position admits the increase and the decrease
  questions *simultaneously*, each with its own independently
  supported answer. What is decisive for one question is a mere
  constraint for another: a position at the policy cap ends the
  increase question by arithmetic and barely touches the decrease
  question. A model without the question would need one verdict to
  serve both askings, and would answer neither honestly.
- **Supersession runs per (subject, question).** A new answer to the
  increase question supersedes the previous answer to the increase
  question — not last month's answer about decreasing. The subject's
  current stance becomes the set of its questions' latest answers,
  derived, never stored. Coherence *across* that set — a rule table
  that answers increase and decrease affirmatively at once has a
  defect — is the engine's obligation, not the object's, and it is
  checkable precisely because every decision names its rule and its
  edges.

### The questions, at birth

Four, and the list is **closed** — a question exists only with a rule
table and a live case behind it, grown one at a time under §19a, never
taxonomy-first:

- **Entry** — *should this security enter the portfolio?*
- **Increase** — *should this position increase?*
- **Decrease** — *should this position decrease?* Exit is this
  question's limiting case — the policy-room arithmetic runs to zero —
  and becomes a question of its own only when a real case earns it a
  rule table of its own.
- **Understanding** — *should the platform spend to improve its
  understanding of this subject?* The spend question. Its affirmative
  action is not a position action but an observation run — N readings
  of a named document key, the count fixed before the first reading,
  exactly as the acquisition policy already demands.

A question no rule table answers is refused with that reason —
`question unmapped`, the selector's `conclusion unmapped` one layer up
— never answered by a neighbouring table.

### INVESTIGATE and the spend question

The constitutional verdict and the fourth question meet, and the model
must say how, or it carries two implementations of one concept.
`INVESTIGATE`, reached on any question, means: *this question is worth
answering and cannot yet be answered, and the gap in its basis is
acquirable.* It **defers** the question it was answering and
**raises** the spend question — whose own decision, on its own basis
(the cost, the budget, the deferred case's promise), is where the
spend is actually decided. The owner's closure — `INVESTIGATE` owns
below-quorum and research acquisition — lands as exactly this
mechanism. The two decisions reference each other: the `INVESTIGATE`
outcome names the spend question it raised, and the spend decision
names the deferred question as its occasion. Acquisition thereby
becomes what the acquisition policy always wanted it to be — an
explicit spend with a decision behind it — and read-until-classifiable
stays foreclosed twice over: the spend decision fixes its observation
count before content, and the deferred question is re-asked only when
the observations land, which is a new occasion, never a loop.

One asymmetry follows and is deliberate: the spend question is the one
question on which `INVESTIGATE` is unreachable. Its basis — cost,
budget, promise — is never itself acquirable by spending; deferring
the decision to spend into a decision to spend would be circular.

---

## The object

`InvestmentDecision`, at the level of meaning rather than code. Every
field earns its place against the eight constraints.

**Subject.** The instrument, under the platform's identity discipline
— the same checked identity the knowledge layer enforces before
reading. A decision about an instrument the platform cannot identify
is a refusal.

**The question.** Exactly one of the four, named above. The verdict is
an answer; this is what it answers. A decision that cannot name its
question is not ambiguous — it is invalid, the way a citation without
its relationship is not weak evidence but no citation.

**Decided-at, and the occasion.** When the decision was made, and
*what changed* to occasion it: a new filing observed, a quorum filled,
a policy edit, a position drifted past a threshold, a scheduled
review, the investor asking, a deferred question's observations
landing. "First consideration of this subject; nothing preceded" is an
occasion. "Scheduled review; nothing material changed; stance
re-affirmed" is an occasion. The occasion names the changed facts by
reference and the question it raised — it is the third constraint made
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
  `RECOMMEND` — the answer to the question, with the question's
  affirmative action attached to `RECOMMEND` only (a position action
  with its policy-room arithmetic, or the spend question's bounded
  observation run), and the raised spend question referenced from an
  `INVESTIGATE`; or
- a **refusal** — no verdict, with the refusing layer's reason
  verbatim.

**The three clauses.** The Executive Brief's questions (constitution
§11) are answered *here*, structurally, and merely worded downstream —
Communication explains decisions; it never makes them, so everything
the brief will say must already be present in the object with edges:

1. **What changed** — the occasion, with references to the changed
   facts or contexts.
2. **Why it matters** — materiality for the case *and for the
   question asked*, stated in the playbook's and understanding's own
   terms, with references to the consensus claims consumed.
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

**The predecessor.** A reference to the decision this one supersedes
— same subject, same question — or the worded statement that none
preceded. The chain of decisions in one question's stream is the
investor-visible history of the platform changing its mind about that
question, and it must read as *this superseded that, because this fact
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
                                             Outcome ── answers ──▶ Question
                                  Decision ── supersedes ──▶ prior Decision
                                             (same subject, same question)
```

Walking backwards from a verdict therefore reaches, in order: the
question it answers, the clauses that support it, the facts and
contexts each clause consumed,
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
- A verdict without its question — an adjudication that cannot say
  what it adjudicated.
- A question invented ahead of its rule table and its live case — the
  list is closed, and grows only under §19a.
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

## Decisions (2026-08-08)

The design was accepted in principle by the owner the day it was
proposed, with the governing principle confirmed as the foundation.
The open questions were closed as follows, and these bind the
implementation:

1. **`REJECT` is supersedable.** No stance is terminal; a revived
   case is a new decision citing what changed.
2. **`INVESTIGATE` owns below-quorum and research acquisition.** The
   mechanism is the spend question: `INVESTIGATE` defers and raises,
   the spend decision decides, and the two reference each other.
3. **Sizing in v1 is policy-room arithmetic only.** Conviction
   weighting, tranching, and anything finer are refused as
   unsupported until a future layer earns them.
4. **Decisions are per-subject only.** A rebalance is an occasion
   that raises per-subject questions; no portfolio-level decision
   object exists in v1.
5. **The occasion list is open**, like absence reasons — an occasion
   is worded, never enumerated. The question list, by contrast, is
   closed, like the verdicts.
6. **Market observations are admissible as explicitly observed
   inputs.** They require no knowledge-style stability measurement
   before v1; the width-1 label and the context-observation partition
   of the basis are the guard.

**Amended at acceptance: the decision question.** Proposed by the
owner — the object defined the verdict but not the question being
answered — explored, and integrated throughout this document: one
decision answers one question; the question is the verdict's
applicability; four questions at birth, closed; supersession per
(subject, question). The freeze awaits the owner's confirmation of the
integrated form.

---

## What the freeze would mean

Freezing this document fixes the language: every future engine — the
first deterministic rule set, committees when they return, and
anything after — produces `InvestmentDecision`s and nothing else, the
way every reader produces observations and nothing else, and every
rule table is written per question. The next design session after the
freeze is the first such table, for the question the corpus can
actually earn: JPM holds the platform's only authoritative end-to-end
playbook and sits outside the investor's book, so the first question
this platform formally answers should be the **entry question for
JPM** — with every supporting link already checkable — and the spend
question standing ready for the companies whose consensus is still
thin.
