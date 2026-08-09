# MOVRvest Engineering Constitution

> The working agreement for building MOVRvest. Design reviews, code reviews
> and architectural decisions are measured against these principles.

---

## 1. Product first

MOVRvest is an Artificial Chief Investment Officer.

Every engineering decision must improve one of:

**Perception · Understanding · Reasoning · Judgment · Explainability**

If it improves none of them, question whether it belongs.

---

## 2. The architecture is settled

The canonical pipeline is:

```
Reality → Evidence → Perception → Brain → Reasoning →
Executive Committee → Artificial CIO → Communication →
Executive Brief → Dashboard
```

No new execution pipelines. No duplicate architectures.

---

## 3. Single responsibility

Every component answers exactly one question.

| Layer | Question |
|---|---|
| Evidence | What happened? |
| Perception | What is true? |
| Brain | What do we know? |
| Reasoning | What does it mean? |
| Executive Committee | What are the trade-offs? |
| Artificial CIO | What should we do? |
| Communication | How do we explain it? |
| Dashboard | What does the investor see? |

---

## 4. Engineering workflow

```
Inspect → Understand → Design → Code → Test → Commit
```

Never skip inspection. Never guess APIs.

---

## 5. Reuse before create

Before writing code, ask: does this already exist? Can we extend it? Can we
simplify it?

The best code is reused. The second best is deleted.

---

## 6. One business concept, one model

Do not duplicate domain concepts. `Brain`, `BrainContext`, `BrainSnapshot`
and `BrainState` should not coexist unless they genuinely represent
different business concepts.

---

## 7. Evidence before inference

Everything starts from evidence. Never invent facts. Never infer before
observing.

---

## 8. The Brain never lies

The Brain stores portfolio, market, macro, investor, policy, memory,
evidence and timeline.

It stores **facts** — never recommendations, never UI, never presentation.

---

## 9. Analysts never decide

Analysts produce assessments, confidence, evidence and uncertainty.

They never produce BUY, SELL, PREPARE or RECOMMEND. Those belong to the
Artificial CIO.

---

## 10. The Artificial CIO owns judgment

One component makes investment decisions.

Input: assessments, committee opinions, policy.
Output: `REJECT · INVESTIGATE · MONITOR · PREPARE · RECOMMEND`

---

## 11. Communication never thinks

Communication explains; it never decides.

Every Executive Brief answers:

1. What changed?
2. Why does it matter?
3. Why does it matter for me?
4. What should I do?
5. Why should I trust this?

---

## 12. The UI never reasons

The dashboard presents, visualises and navigates. It never calculates,
reasons, ranks or decides. Financial calculation belongs in the backend.

---

## 13. Keep the repository green

Every meaningful change preserves `ruff`, `mypy`, `pytest` and
`npm run build`. No accumulating technical debt.

---

## 14. Vertical slices

Ship one complete capability, fully integrated and fully tested, rather than
five incomplete ones.

```
Analyst → Reasoning → Executive Brief → Dashboard
```

One slice. Then continue.

---

## 15. Delete legacy carefully

Never delete first:

```
Replace → No callers → Tests pass → Delete
```

Dead code should disappear naturally.

---

## 16. Documentation follows reality

Architecture documents describe what exists. Project state describes where
we are going. Never let documentation drift from the implementation.

---

## 17. Explainability is a feature

Every recommendation must be evidence-based, explainable, transparent,
auditable and consistent. Trust is part of the product.

---

## 18. Measure the right things

Do not celebrate lines of code, service count or agent count.

Celebrate legacy removed, reasoning improved, explainability increased,
investor trust strengthened.

---

## 19. Challenge complexity

Before adding anything: is it simpler? Clearer? More reusable? Does it make
the Artificial CIO smarter?

If not, do not build it.

---

## 19a. Patterns earn architecture

A new engineering slice must be earned by a measured pattern, never by
an individual company.

One filing that defeats the reader is a backlog entry — recorded, with
its measured failure, on a watchlist. Several companies failing for the
*same structural cause* are a pattern, and a pattern earns a slice. The
instrument that tells one from the other (`movrvest reader-defects`,
and its successors) is consulted before any frozen layer is reopened;
the measurements decide, not the most recent frustration.

The same rule grows vocabularies: a grounded playbook exists only when
a real company at quorum, an established understanding, an obvious
deterministic mapping and a live acceptance case all exist. Case by
case, never taxonomy-first.

---

## 19b. The Reference Corpus is the engineering contract

A stable set of real companies — each in the corpus for a property its
filings exercise, named beside it in
`app/domain/reference_corpus.py` — is what every reasoning change
proves itself against before it reaches the investor.

The corpus formalises what the platform had already begun doing
informally: measuring every major capability against the same
companies, so a regression is caught by the company that first proved
the capability works. JPMorgan is the canonical case — the first
company carried from filing to authoritative playbook with every link
grounded — and a change that breaks any link of that chain must fail
against JPMorgan before an investor can meet it.

Two disciplines keep the contract meaningful:

- **The corpus stays stable.** Membership is earned by exercising
  something real, as measured, and is reviewed by the measurements'
  owner — never adjusted to make a change look safe.
- **The corpus is engineering, never investment.** Its companies are
  tracked under their own origin, behind the investor's lists, and can
  never enter a portfolio funnel or move a KPI.

---

## 20. The North Star

Every change should improve at least one of:

```
Observe better → Understand better → Reason better →
Judge better → Explain better
```

---

## 21. Absent evidence is reported as absent

*Added in practice, and load-bearing.*

A plausible figure on an investment dashboard reads as a measurement. Where
the platform cannot evidence something — a price target, a conviction
trend, an asset class — it says so rather than estimating.

This is why investment cases carry no upside projections, why
`consistency_score` reports a neutral midpoint, and why an unnameable
holding keeps a visible `#id` rather than a guess.

---

## 22. A test proves the seam cannot activate, not that it did not

*Added in practice, and paid for.*

The platform reaches two kinds of outside world: registers and models.
Both cost money, both are slow, and a test that touches either has
stopped being a test. The hard part is that **the failure is a green
suite**, not a red one.

**A test intending to prove an external seam is disabled must verify the
seam cannot activate — not merely observe the expected result.** A test
asserting "no credentials, so it did not run" passes identically whether
the seam was silenced or whether it woke up, called a live model, and
happened to produce the asserted shape. The assertion cannot tell the
two apart, so the silencing has to be structural.

**Disable those seams centrally.** `tests/conftest.py` names every module
that resolves a credential and every variable that can turn a seam on,
and silences all of them for every test. A module that grows a
`get_settings()` call for a key is added there in the same change.
Scattering the silencing across the tests that happen to need it means
each one carries a patch target that goes stale silently — which is
exactly how this was learned, twice in one afternoon.

**Verify a dependency boundary by contract, never by concrete type.** A
seam that accepts an extractor accepts anything that answers like one.
Narrowing on `isinstance(value, CompanyKnowledgeExtractor)` rejects every
stand-in and alternate implementation, which is the whole point of having
the seam — and production keeps working, so nothing says so.

**Treat a runtime regression as a defect, even with every assertion
green.** The suite runs in about two seconds. It once went to seventy-two
because a service had begun reading a 10-K and calling a model, and not
one assertion noticed. `python -m pytest -q --durations=5` names the
culprit immediately, and a sudden jump is evidence that a seam meant to
be dead is live.

---

## 23. Every PR answers what becomes better for the investor

*The owner's rule, 2026-08-09, in the owner's words.*

> **What becomes better for the investor?**

> *"Nothing, but the domain is cleaner."* → **the PR waits.**
>
> *"Recommendations become easier to trust."* → **ship it.**

Asked before the work starts and answered again in the PR — a scoping
gate first, and a standing question second.

**A PR that waits is not a PR that is wrong.** It is one whose product
story has not arrived. The disposition is deliberate: rejecting good
work teaches people to stop noticing it, while making it wait keeps it
available for the slice that eventually needs it — built inside that
slice, where the benefit is visible and the cost is charged against
it.

This is the reason the principle exists rather than being obvious.
Every repository accretes
work that is locally correct, passes review, ships green, and moves no
decision the investor ever sees. A platform whose product is
**trust** cannot afford that work, because the investor is not paying
for consistency — they are paying for a recommendation they can rely
on and argue with.

**Name the mechanism where you can.** *Recommendations become easier
to trust, because the Quality Committee now reasons from established
business understanding* is checkable. *It improves quality* is an
assertion wearing an answer's clothes.

**What still passes honestly.** The question has a second admissible
answer, and pretending otherwise would get the rule quietly ignored:
*a decision that is currently getting a wrong answer, or is at risk
of one, and would stay that way.* A defect that corrupts a figure, a
seam that could spend money in tests, a dependency that fails only in
CI — each names a real investor-facing decision, in the negative.
That is a legitimate answer, not an exception to the rule.

**What does not pass.** Cleaner factoring, fewer files, better
symmetry, consistency for its own sake, a layer completed because it
felt incomplete, or a step taken because it appears in a sequence
somewhere. If such work is genuinely needed, it is needed *by*
something that passes — so it travels inside that slice, and its cost
is visible where the benefit is.

**Where this sits.** It sharpens §20: the North Star's five verbs are
how the platform improves, and this names who has to be better off
when it does. It also supersedes, as *sufficient* justification, the
first, second and fourth bullets of the Migration Plan's mission —
simpler, more consistent, easier to extend. Those remain good
properties. None of them is a reason on its own.

---

## 24. No new architecture without a product story

*The owner's declaration, 2026-08-09. §23 applied to structure, and
the sentence to remember when only one survives.*

**The core architecture is frozen — deliberately, and not forever.**

The evidence stack, the knowledge and understanding layers, the
decision model, the assessment contract and the committee object are
**closed for structural work.** Enough architecture exists to build
several investor-facing capabilities; none of it needs to be more
correct before that happens.

The freeze is a direct consequence of §23 rather than a separate
policy: while every change must name the decision it improves,
architecture undertaken for its own sake cannot start.

**What the freeze covers.** New layers, new canonical objects, new
taxonomies, renamed or re-factored seams, and the completion of
designed-but-unbuilt steps purely because they are designed.

**What it does not cover.** Anything that answers §23 — including
structural work that a passing slice genuinely requires, taken inside
that slice. Defect repair is unaffected. So is acquisition that a
named investor-facing capability is blocked on.

**What lifts it.** The owner, on the same evidence any slice needs
under §19a: a measured pattern, not a single frustration, and a live
case where the missing structure is what blocks an investor-facing
decision.

The two accepted architectures left standing with nothing built —
[`ASSESSMENT_CONVERGENCE.md`](architecture/ASSESSMENT_CONVERGENCE.md)
and the profile determination in
[`COMMITTEE_OPINION.md`](architecture/COMMITTEE_OPINION.md) — are
correct and are **not** a backlog. They are the map for when a slice
needs that ground, and their behaviour-free steps are not to be taken
on their own.

---

## The final principle

We are not building a trading bot. We are not building a dashboard.

We are building an Artificial Chief Investment Officer that helps investors
make better decisions through evidence, reasoning, judgment and transparent
explanation — while the investor always remains in control.
