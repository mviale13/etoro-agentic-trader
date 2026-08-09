# Assessment Convergence

How every future committee assessment arrives at one canonical object.

Status: **Accepted architecture, nothing implemented** (2026-08-09).
Written on the owner's ruling — *`CommitteeOpinion` becomes the
reference implementation of the future Assessment layer; do not merge
the pipelines yet* — recorded as Amendment 1 in
[`INVESTMENT_ASSESSMENT.md`](INVESTMENT_ASSESSMENT.md), which stays
frozen and unrelaxed. This document is the *how*; that document
remains the *what*, and where the two ever disagree, that one wins.

---

## The problem this solves

Two live decision paths exist, and they will exist for some time:

```text
executive pipeline      Brain → signals → committees → ExecutiveDecision → dossier
canonical decision      store → understanding → playbook → InvestmentDecision
                                                    ▲
                                              (no assessments)
```

The second can only ever reach `MONITOR` by
`entry-no-assessment-establishes-a-case`, because its kind vocabulary
is empty. The first reaches the investor every day.

The failure mode this architecture exists to prevent is the one the
repository has already paid for once: **four parallel committee
implementations, with the docs calling a dead one canonical.** If
committee reasoning keeps growing on the executive pipeline while
assessment kinds are separately designed for the decision layer, the
platform builds two evaluative vocabularies and discovers the
duplication after both have consumers.

The ruling forecloses that by naming one shape. This document makes
the naming operational: **what a committee must declare so that it
converges by construction, and what carries it across the seam when
the time comes.**

---

## The governing move: projection, not merger

> **One object, two readers.**

A committee produces a `CommitteeOpinion`. The dossier reads it as an
opinion. When a kind is earned, the decision layer reads *the same
object* as an assessment, through a pure, total projection.

```text
                    ┌──────────────────┐
   signals ────────▶│ CommitteeOpinion │
                    └────────┬─────────┘
                             │
              ┌──────────────┴───────────────┐
              ▼                              ▼
      dossier surfaces              assessment_of(opinion, kind)
      (stance, grounds,                       │
       coverage, rule)                        ▼
                                    InvestmentAssessment
                                              │  weighed-in
                                              ▼
                                     InvestmentDecision
```

Three properties follow, and each is the reason this is a projection
rather than a merge:

- **The committee never learns the projection exists.** Independence
  is total in the frozen contract, and a committee that could see the
  decision layer could shape itself to it.
- **Nothing is re-derived.** The projection reads fields; it computes
  no stance, weighs no finding and reaches no conclusion. A projection
  that computed anything would be a second rule table, which is the
  duplication the ruling exists to prevent.
- **The pipelines stay separable.** Either can be retired later
  without redesigning the object — which is exactly the optionality
  the owner asked to preserve.

---

## What already converges

The committee layer was rebuilt (PR #77) against its own reasoning and
landed on four of the frozen contract's properties without being
asked to. They are listed first because they are the reason the ruling
is cheap:

| Contract property | In `CommitteeOpinion` |
|---|---|
| Refusal and opposition are different **types** | `stance=None` + `abstained_because` is not `Stance.NEGATIVE` |
| Every absence carried **verbatim** | `uncertainty`, worded by the layer that found the gap |
| An assessment that cannot name its rule cannot exist | `decided_by` |
| Independence is total — no assessment knows another exists | no committee sees `Panel`; each is a pure function of brain, symbol, ledger |

Two more are mechanically right and wait only on evidence class:

| Contract property | In `CommitteeOpinion` |
|---|---|
| The basis is held **by reference**, never restated | `supporting` / `opposing` are content-addressed `Finding.ref`s |
| An implication is **directional** — never inferred from absence | the stance table fires only on findings that were read; neutral findings and empty remits produce no stance |

That last row is worth stating plainly, because it is the property
most easily lost: `RULE_UNOPPOSED_ADVERSE` requires two adverse
findings to have been *read*. No stance on this platform is reachable
from an absence. The directional property is already structural.

---

## What must change, on each side

### On the committee side — five declarations

The frozen contract defines a kind as four things. A committee kind is
those four plus one, and the fifth is the committee layer's own
contribution rather than a deviation: the contract asks a kind to
declare its basis, and `remit` is exactly that declaration.

| # | Declaration | Today | Gap |
|---|---|---|---|
| 1 | **The question** — the one evaluative claim, worded so a reader can check it | implicit in the committee's name | **missing** |
| 2 | **The courses** it may offer — a subset of the shared vocabulary | `Stance`, which is a *direction*, not a verb | **needs the seam below** |
| 3 | **Applicability** — which `DecisionQuestion`s it answers | — | **missing** |
| 4 | **The rule table**, deterministic and named | `opinion_builder`'s six rules | ✅ |
| 5 | **The remit** — which readings it consumes | `frozenset[Dimension]` | ✅ |

Declarations 1 and 3 are pure additions: they change no behaviour, and
they make the two live committees self-describing. That is why they
are step 0 of the sequence.

Note that 3 and 5 are **different axes** and both are needed.
Applicability says *which question this kind may answer*; remit says
*which readings it is allowed to look at*. A committee with the right
remit offered to the wrong question is inadmissible, and so is the
reverse.

### On the assessment side — three fields the projection must supply

- **The subject**, explicit. An opinion is composed inside a case that
  knows its symbol; an assessment carries it, because it is weighed
  somewhere the case is not.
- **`rests_on`** — the narrowest consumed agreement, distribution
  included, or the worded reason no consensus claim was consumed.
  Today a committee consumes no consensus claim, so the honest value
  is the worded reason. That changes with evidence class, below.
- **`because`** — carried from the rule, not composed. The rule name
  already encodes what the counts were.

---

## The seam: a stance is a direction, a course is a verb

The single most important boundary in this document, because getting
it wrong reintroduces the defect the committee rebuild removed.

`Stance` says which way the findings point. A **course** is what an
assessment offers a decision. They are not the same thing and a course
is never produced by renaming a stance — a kind declares a **table**
mapping its direction to the courses it may positively establish.

```text
    stance                     the shape the mapping takes
    ──────────────────────     ─────────────────────────────────────
    strongly positive  ──┐
    positive           ──┴──▶  a supporting course, if the kind may
                               offer one for this question

    neutral            ─────▶  a course that supports waiting — read,
                               and it argues neither way, which is a
                               conclusion and not an absence

    negative           ──┐
    strongly negative  ──┴──▶  an opposing course, only where the
                               kind's rules positively establish it

    None (abstained)   ─────▶  a refusal, worded verbatim — never a
                               course, and never an opposing one
```

**The exact course vocabulary is not fixed here, and must not be.**
The frozen contract fixes it with kind #1, under two standing rules
(refusal stays an outcome type, and a course enters only when a rule
table can positively establish it). This document fixes only the
*shape* of the mapping — that it is a declared table per kind, that
abstention leaves it entirely, and that strength has nowhere to go.

Two consequences worth stating:

- **Strength is deliberately lost at the seam.** The contract has no
  notion of a stronger implication, and inventing one would be a
  weight the decision layer could multiply by. What survives is the
  named rule, which already records whether the case was unopposed —
  so nothing is hidden, and nothing is weighable.
- **Neutral is not a refusal.** A committee that read findings on both
  sides reached a conclusion. Collapsing it into *the inputs could not
  carry a conclusion* would destroy the distinction the committee
  layer exists to preserve, and would understate what the platform
  knows.

---

## What decides whether a kind may *warrant*

Converging the shape does not make an assessment admissible. The
frozen contract's Yahoo boundary decides that, and it bites hardest
exactly here:

> A warranting assessment's load-bearing claims are filing-grade,
> full stop. Labeling is sufficient for context; it is not sufficient
> for `RECOMMEND`.

Today the committees' remits are fed by the value, quality and
momentum signals — **provider-reported fundamentals**. So:

| | shape converged | basis filing-grade |
|---|---|---|
| may exist as a kind at all | required | — |
| may offer a course that supports waiting | required | not required, if labeled |
| may offer a **warranting** course | required | **required** |

**No committee assessment can warrant today**, and no amount of
shape-work changes that. This is not a limitation of the convergence
architecture; it is the architecture reporting the same frontier the
frozen contract already found — *the frontier is acquisitional, not
architectural* — and arriving at it from the opposite direction.

### The bridge: evidence class travels with the finding

The mechanism is small and it is the pivot of the whole sequence.

`FactOrigin` — `ESTABLISHED` (read from the filing and checked against
the cell it sits in) versus `ASSESSED` (this platform's analysts
reading market data) — exists today, and it lives on the *synthesis*,
one layer too late to be useful. It belongs on `Finding`, beside
`Sense` and `Dimension`, for the same reason both of those moved
there: **the layer that composes a finding knows its class, and every
layer above has to guess.**

Once it travels:

- a ledger can be split by class, so a committee's basis states what
  it rests on rather than implying uniformity;
- an assessment's basis separates established facts from labeled
  context observations exactly as the contract requires;
- `rests_on` becomes real — established findings carry the agreement
  they were established at, and the narrowest crosses the seam;
- and the ranking gap left open by PR #77 closes for free: *strongest*
  supporting evidence becomes defensible, because established
  outranks assessed. That ordering is an evidence-class judgment, not
  a judgment about the company, which is the only kind of ordering
  this platform permits itself.

The first kind to cross is therefore the one whose remit can be fed
established findings: **business quality, from `FinancialUnderstanding`
rather than from a provider's ratios.** That is the same kind #1 the
frozen contract already fixed, reached independently. The two
documents agree, which is the strongest evidence available that the
convergence is real rather than arranged.

---

## What does not cross the seam

**`Confidence` stays on the opinion.** The contract forecloses a
confidence integer, score or probability anywhere in an assessment,
and the Reconciliation clause named per-opinion confidence explicitly
as a thing that does not survive.

It is not smuggled across under another name, and it does not need to
be, because of a property worth making a law:

> **No field may carry information the projection loses.**

Everything `Confidence` counts is already carried in a vocabulary the
contract permits. Each unmeasured input produces a
`MEASUREMENT_ABSENT` uncertainty with its own wording; the supporting
and opposing counts are the lengths of the reference lists. Coverage
is therefore *expressible* from what crosses, and `Confidence` is a
presentation of it for the dossier — where a reader benefits from one
banded line — rather than a second uncertainty vocabulary competing
with `rests_on` in front of an adjudicator.

The general rule this instances: a field may stay behind the seam
only when it is derivable from fields that cross. A field that is not
is either promoted or deleted; it is never quietly dropped.

---

## The laws

The nine that keep every future committee assessment converged. They
are the operational content of this document; everything above is why
they are what they are.

1. **One object, two readers.** Convergence is by projection. A
   projection reads fields and computes nothing.
2. **A kind is five declarations or it is not a kind** — question,
   courses, applicability, rule table, remit. Declared, never
   inferred, and never partially.
3. **A stance is a direction; a course is a verb.** Kinds map by a
   declared table and invent no verbs. Abstention leaves the mapping
   entirely.
4. **Evidence class travels with the finding.** Composed where it is
   known, never re-derived from wording.
5. **Shape converges; class admits.** A converged shape makes a kind
   *possible*; only filing-grade basis makes it *warranting*.
6. **One uncertainty vocabulary crosses the seam.** Coverage is
   carried as absences.
7. **No field may carry information the projection loses.**
8. **Independence is structural at both layers.** No committee
   consumes, ranks or answers another; no assessment does either.
9. **One kind at a time, under §19a**, with a real company, an
   established input, an obvious deterministic mapping, and a live
   case where the kind changes what is reachable.

---

## The sequence

Interleaved with the frozen contract's own sequence rather than
replacing it. Steps 2 and 4 below *are* its steps 1 and 2.

| # | Step | Changes behaviour? |
|---|---|---|
| 0 | Declare question and applicability on the two live committees; keep remit and rules as they are | no — additive |
| 1 | `FactOrigin` moves onto `Finding`; the ledger splits by class | no — every finding today is `ASSESSED` |
| 2 | **Financial Statement Acquisition** (contract step 1) | — done for one period |
| 3 | A quality dimension fed by `FinancialUnderstanding`: the first established findings in a remit | yes — first filing-grade committee basis |
| 4 | **Kind #1, Business Quality** (contract step 2): the course vocabulary is fixed, and `assessment_of` is written | yes — first admissible assessment |
| 5 | **The adjudication successor** (contract step 3) | yes — `RECOMMEND` becomes reachable |

**Nothing in this document is implemented.** It was produced on the
ruling, and the ruling said not to merge.

### The sequence under the gate (2026-08-09)

Constitution §23 arrived immediately after this document and reorders
it. The gate — *which investor-facing decision becomes better?* — is
applied here first, because this sequence is the nearest thing the
repository has to a standing invitation to do structural work.

| # | Answer to the gate | Verdict |
|---|---|---|
| 0 | none — the committees describe themselves better | **do not take alone** |
| 1 | none — every finding today is `ASSESSED`, so nothing moves | **do not take alone** |
| 3 | *the recommendation is more trustworthy, because the Quality Committee reasons from what the filing establishes rather than from a provider's ratios* | **ship it** |

Steps 0 and 1 are behaviour-free, which was written above as though it
were a virtue — *they could be taken at any time*. Under the gate it
is the opposite: behaviour-free means no investor-facing decision
improves, so they are not slices. They are **preparation that travels
inside step 3**, where the benefit is visible and their cost is
charged against it.

Step 3's answer is, word for word, the owner's own example of an
answer worth shipping. That is not a coincidence — it is the one point
in this architecture where converging the shape and improving a
recommendation are the same act.

So the sequence is not a queue to be worked through. It is the map for
one slice: **a quality dimension fed by `FinancialUnderstanding`**,
carrying with it whatever of steps 0 and 1 that slice actually needs.

---

## What this forecloses

- A second evaluative shape designed in parallel with
  `CommitteeOpinion`.
- A course invented by renaming a stance, or a strength crossing the
  seam as a weight.
- A committee assessment warranting on provider-fed fundamentals,
  under any label.
- A projection that computes, scores, ranks or resolves anything.
- A field kept behind the seam that is not derivable from what
  crosses.
- A kind declared with fewer than five parts, or declared ahead of a
  live case that needs it.
