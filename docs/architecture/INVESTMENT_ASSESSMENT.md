# The Investment Assessment

Status: **Proposed** (2026-08-08) — a design document only, the next
slice after the decision layer shipped. Nothing here is implemented,
and nothing should be until the open questions at the end are closed
and recorded, the way `INVESTMENT_DECISION.md`'s were.

---

## Why this document exists

The first live decision made the missing layer observable instead of
guessed. `JPM.entry.0001` is a `MONITOR` decided by
`entry-no-assessment-establishes-a-case`: the most completely
understood company on the platform, an authoritative playbook, policy
room to enter — and no honest way to conclude anything, because
understanding a business does not itself imply entering it, and
nothing admissible yet says what the established facts *imply*. The
losing implication in that decision's record — *the case is eligible
to be put to an assessment* — is a precise request. This document
designs what would answer it.

The layer boundary it must respect, in the owner's words at the
decision layer's closeout:

```text
Knowledge says what is established.
Understanding says how the business works.
Assessments say what those facts imply.
Decision resolves competing implications for one explicit question.
```

The question this document answers before any code: **what is the
smallest canonical assessment capable of offering a course to an
`InvestmentDecision`?** Not all analysts. Not committees. One object,
designed so that whatever produces assessments — a wrapped
deterministic analysis first, richer machinery later — must speak the
same language, exactly as every reader produces observations and
every engine produces decisions.

---

## The governing principle

> **An assessment states what established facts imply for one bounded
> evaluative claim. It offers a course; it never decides.** It
> inherits its facts' uncertainty at the narrowest width and never
> resolves it — and *does not establish* is not *opposes*: what its
> inputs cannot support, it refuses, out loud.

Every design decision below is tested against that sentence.

---

## Concepts kept apart

### An assessment and an understanding

Business Understanding is descriptive and course-free: it explains
how the company creates value, and nothing in it points anywhere. An
assessment is evaluative and course-bearing: it answers one bounded
claim — *does X support course Y?* — and its whole output is the
course it offers and the ground it stands on. The gap between the two
is exactly where JPM's `MONITOR` lives: a complete description, zero
evaluation. Collapsing them — deriving "quality" from the shape of a
segment table — would be an invented metric wearing determinism's
clothes, and it is foreclosed below.

### An assessment and a decision

An assessment **offers**; the decision **adjudicates**. The
constitutional boundary (§9–10) lands here as two prohibitions, one
per side:

- An assessment never names a verdict. `REJECT`, `MONITOR`,
  `RECOMMEND` are postures toward a question, and only the CIO takes
  a posture. An assessment's conclusion is a course — *entry is
  warranted*, *waiting is supported* — which the decision may weigh,
  follow, or overrule by a named rule.
- The decision never reaches inside an assessment. It consumes the
  assessment whole — the course, the because, the edges — and must
  not re-derive its facts or reinterpret its conclusion. The
  `Implication` the decision already records is the assessment's
  shadow: the receiving slot has existed since the decision model was
  frozen.

### Permitting and warranting

Two different relations to a course, and the decision's accepted
rule ordering already keeps them apart. **Policy permits** — it
bounds what may be done, is obeyed rather than weighed, and is
evaluated before anything else. **Only a merits assessment warrants**
— it establishes that a permitted course is worth taking. `RECOMMEND`
requires at least one warranting assessment to prevail; permission
alone never warrants, no matter how much room the arithmetic finds.
This pair is the precise answer to *what would make `RECOMMEND`
reachable for JPM*, worked through below.

### Refusing and opposing

*Does not establish support for entry* and *opposes entry* are
different conclusions, and the object keeps them different types: the
first is a refusal (the inputs could not carry the claim), the second
is an offered course (the inputs carry the opposite). Collapsing them
manufactures bearishness out of ignorance — the mirror image of the
estimated figure on the dashboard, and the assessment layer's own
version of the counterfeit invariant 1 forbids.

### Derived and recorded

An assessment is **derived at decision time and never stored on its
own.** It is a pure function of its basis, so storing it would create
a second place for it to be true — the same argument that keeps
consensus derived-on-read. Its durable record is the decision event
that weighed it: the decision preserves what was offered, verbatim,
in the one place where it mattered. (The asymmetry with decisions is
principled, again: a decision's inputs are perishable and the
investor may have acted on it; an assessment re-derives from the same
facts any time.)

### Independent, like observations

No assessment sees another's conclusion. Each answers its own claim
from the basis alone, and disagreement between assessments is
resolved only in the decision's adjudication, by a named rule, losers
preserved. Assessments that negotiated with each other would be a
committee hiding inside the basis — the adjudication would have
happened before the layer that is allowed to adjudicate.

---

## The object

`InvestmentAssessment`, at the level of meaning. The shape mirrors
the decision deliberately — same uncertainty vocabulary, same absence
discipline, same edges — because the decision must be able to consume
it without translation.

**The kind.** A closed vocabulary, empty at birth, grown one kind at
a time under §19a. A kind is a *contract*, not a label:

- the one evaluative claim it answers, worded as a question;
- the closed set of courses it may offer (a valuation kind may offer
  *entry is warranted* or *waiting is supported*; it may never offer
  a size);
- the decision questions it applies to — applicability is declared,
  and an assessment offered to a question its kind does not apply to
  is inadmissible, full stop;
- its deterministic rule table.

A kind without all four is not a kind. "Business quality", "risk",
"timing" enter this vocabulary the way playbook rules entered theirs:
a real company, an established input, an obvious deterministic
mapping, and a live case where the kind changes what is reachable —
case by case, never taxonomy-first.

**The subject.** One security, identity-checked upstream.

**The conclusion.** Exactly one of:

- an **offered course** from the kind's allowed set, with its
  *because* and its evidence-graph edges; or
- a **refusal**, worded — the inputs could not carry any allowed
  conclusion, and the reason travels verbatim.

**What it rests on.** The narrowest consumed agreement, distribution
included, or the worded reason no consensus claim was consumed; every
absence consumed, verbatim; no probability, score, or confidence
integer anywhere. One uncertainty vocabulary, one implementation.

**The deciding rule.** The named rule in the kind's table that
produced the conclusion. An assessment that cannot name its rule
cannot exist.

**The basis.** Established facts (the verified chain, by reference)
and labeled context observations (width-1, saying so — and admissible
only where the observer is the *primary source* of the observed
thing; the Yahoo boundary below draws this line). Assessments consume
facts; they never establish them — a gap in the basis is inherited or
refused, never filled. Whether declared
policy may enter an assessment's basis at all is an open question
below; the working position is that it may not, because policy is the
one input the *decision* obeys rather than weighs, and an assessment
that consumed policy would be adjudicating admissibility one layer
early.

### Admissibility, checked at the decision

Before weighing an assessment, the decision layer checks the
contract, never the internals:

1. the kind applies to the question being decided;
2. the conclusion is one the kind is allowed to offer;
3. the basis is admissible in kind — established facts and labeled
   observations only;
4. the rule and the edges are named.

This is the same admissibility/stability separation the knowledge
layer drew: the checks decide whether an assessment may enter the
weighing at all; whether it *prevails* is the adjudication's own
business, by the decision's named rules, with losing implications
preserved.

### Where it sits in the evidence graph

```text
Settled fact ── consumed-by ──▶ Assessment ── offers ──▶ Course
Context obs ─── informs ──────▶ Assessment
                                     │ weighed-in (as an Implication)
                                     ▼
                              InvestmentDecision
```

The edges compose: walking backwards from a decision's verdict
through a weighed implication reaches the assessment that offered it,
the facts the assessment consumed, and the cells and spans beneath
them — the eighth constraint of the decision brief, extended one
layer without changing shape.

---

## The JPM entry case, worked

What would have to exist before `RECOMMEND` becomes reachable for
`JPM — entry`? Tracing the decision model backwards:

`RECOMMEND` requires the question's affirmative to prevail in
adjudication, which requires at least one admissible **warranting**
assessment offering *entry is warranted* — permission is already
established by policy arithmetic and warrants nothing.

Now the honest inventory: every established fact the platform holds
about JPM is *structural* — which segments exist, their sizes, their
ways of earning, the archetype they add up to. Structure says what
the business **is**. No deterministic rule over structure alone can
say whether **owning it is attractive** — a "quality" score computed
from the shape of a segment table would be this platform's own
Yahoo, and the taxonomy-first door stays shut. So:

> **No warranting kind is honestly constructible from the current
> fact layer.** The frontier is acquisitional, not architectural.

Warranting needs **grounded fundamentals** — the primary financial
statements read through the exact tabular chain that took segment
sizes to 10/10: cells addressed, read back, arithmetic performed by
the platform, consensus over repeated observations. The same
discipline, pointed at the income statement. This is filing-grade,
it is the natural next knowledge acquisition, and it is its own
earned slice. Where a warranting claim compares value to price, an
explicitly observed quote joins the basis as the labeled width-1
observation it is — one side of the comparison, never the ground of
the conclusion. A multiple computed from a provider's earnings figure
is not a market observation; it is a secondary restatement wearing
one, and the next section forecloses it.

The other road that suggested itself — wrapping the strongest of the
research path's four fundamental analysts, which today consume
provider-reported fundamentals — is foreclosed by the owner's ruling
recorded in the next section.

Until that road is walked, the honest state of JPM's entry stream is
exactly what `JPM.entry.0001` says: `MONITOR`, with the eligibility
implication preserved as the loser. This document exists so that when
the first warranting assessment arrives, the decision that consumes
it will not need a single new concept.

---

## The Yahoo boundary (the owner's ruling, 2026-08-08)

> **Do not let the Assessment layer become "the place where Yahoo
> comes back."**

The knowledge platform was built to escape a specific class of data:
the **secondary restatement** — a provider's copy of what a primary
source says, unverifiable against anything this platform checks, and
measured here flipping between runs. The industry-driven playbook
selector was retired for exactly this, and the assessment layer is
where that class would return if anywhere: a legacy analyst wrapped
over provider fundamentals, its inputs labeled "context-grade" while
its conclusion carries a `RECOMMEND` to the investor. The label would
be a fig leaf — the investor reads the verdict, not the label. So the
boundary is a rule of the layer, not a preference:

- **A secondary restatement of a readable primary source is
  inadmissible in any assessment's basis** — not as a fact, and not
  as a labeled observation either. Where the primary source is a
  filing, the platform reads the filing through its own chain or does
  not know the figure. An observation label does not launder a copy
  into evidence.
- **Market price is different in kind.** The market is the primary
  source of its own prices, so an explicitly observed quote is
  admissible as the labeled width-1 observation it is. But price
  alone warrants nothing — it is one side of a comparison whose other
  side must be filing-grade.
- **A warranting assessment's load-bearing claims are filing-grade,
  full stop.** Labeling is sufficient for context; it is not
  sufficient for `RECOMMEND`.

Two of the open questions this document originally posed are closed
by the ruling:

1. **Kind #1's road is decided: the fundamentals acquisition precedes
   the first warranting kind.** The primary financial statements
   enter the knowledge layer through the same tabular chain that
   earned trust on segment tables — cells addressed, read back,
   arithmetic performed by the platform, consensus over repeated
   observations — and the first warranting kind is built on those
   established figures. There is no shortcut through a wrapped
   provider-fed analyst. This reopens the knowledge stack the only
   way it may be reopened — on an earned demand (§19a) — and the
   demand is measured, not guessed: a live decision that cannot reach
   `RECOMMEND` for want of exactly these facts.
2. **A warranting assessment may not rest materially on context-grade
   evidence.** The decision layer's saying-so rule stays for context;
   warranting requires the verified chain beneath every load-bearing
   claim.

---

## Reconciliation under invariant 9

- **`CommitteeOpinion` and the four analysts** are this layer's
  ancestors. Their durable idea — per-analyst evaluation of one case
  — survives as assessment kinds once each meets the contract; their
  free-text findings and per-opinion confidence integers do not, and
  neither do their inputs: an analyst's *question* may eventually be
  earned as a kind, but its provider-fed basis never wraps into
  admissibility (the Yahoo boundary).
  Nothing is redesigned now: the research path keeps consuming its
  existing objects unchanged until a kind is earned, the playbook
  migration rule applied a third time — outgrown, one authoritative
  case at a time, the two routes never blending.
- **`AnalystKey` and the playbook's analyst rosters** stay as they
  are: the playbook already declares which analysts run and which are
  excluded with reasons. When kinds exist, a playbook's roster
  becomes the natural declaration of which assessment kinds a case
  calls for — the explanation and the instruction staying one thing.

---

## What this model forecloses

- A kind invented ahead of its rule table, its inputs, and a live
  case where it changes what is reachable — no taxonomy-first.
- An assessment naming a verdict, or a decision re-deriving an
  assessment's facts or reinterpreting its conclusion.
- *Does not establish* collapsed into *opposes* — refusal and
  opposition are different types.
- A stored assessment — the decision event is its record.
- An assessment consuming another assessment's conclusion.
- An assessment offered to a question its kind does not apply to.
- A confidence integer, score, or probability, anywhere.
- Model-written analyst prose entering the admissible basis by
  re-labeling — an assessment's inputs are established facts and
  labeled observations, never narrative.
- A secondary restatement of a readable primary source entering any
  basis under any label — the label does not launder the copy.
- A warranting conclusion resting materially on context-grade
  evidence — labeling suffices for context, never for `RECOMMEND`.
- An assessment establishing a fact its basis lacks — gaps are
  inherited or refused, never filled.

---

## Open questions for the design conversation

Two of the original five were closed by the Yahoo boundary and are
recorded there: kind #1's road (the fundamentals acquisition
precedes the first warranting kind) and context-grade warranting
(foreclosed). Three remain:

1. **Is portfolio fit a kind at all?** The working position: hard
   policy constraints are the decision layer's admissibility and are
   never re-assessed; a fit kind could exist only for what policy
   does not already decide, and it should not exist until a live
   case demands it.
2. **The course vocabulary.** Per-kind closed sets, with no global
   course taxonomy — is that right, or should courses be drawn from
   one shared vocabulary so adjudication rules can be written
   generically?
3. **Where adjudication rules live.** Support and opposition will
   eventually arrive together; the resolution belongs to the decision
   layer's rule tables (assessments stay independent) — confirm, and
   confirm that the first such conflict earns its rule the way every
   rule has been earned: from a live case, never in advance.

---

## What acceptance would mean

Accepting this document fixes the contract: whatever produces
assessments emits `InvestmentAssessment`s and nothing else, and the
decision layer's `entry-no-assessment-establishes-a-case` rule gains
its successor: a rule that weighs offered courses. The road there is
set by the Yahoo boundary — the first implementation work after
acceptance is the **fundamentals acquisition**: the primary
financial statements through the proven tabular chain, a knowledge
slice reopened on the decision layer's own measured demand. The
first kind follows on those established figures, exercised against
the JPM entry stream — where the second decision in that stream will
either still say `MONITOR` with a richer record, or say something
more, and either way say it honestly.
