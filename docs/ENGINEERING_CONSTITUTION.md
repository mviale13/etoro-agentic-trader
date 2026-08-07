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

## The final principle

We are not building a trading bot. We are not building a dashboard.

We are building an Artificial Chief Investment Officer that helps investors
make better decisions through evidence, reasoning, judgment and transparent
explanation — while the investor always remains in control.
