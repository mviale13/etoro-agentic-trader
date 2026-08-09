# The Committee Opinion

Status: **Implemented** (2026-08-09). The object, its rules and the
Executive synthesis that consumes it are live on the executive
pipeline. Two things in this document are **not** implemented and are
recorded here as decisions for the owner: the investment-profile
determination (§4) and the two-stack question (§5).

---

## Why this document exists

The Artificial CIO explained *what happened* and never *why one
conclusion prevailed over another*. Every recommendation carried the
same sentence — *the investment case satisfies quality, evidence,
valuation, risk, and portfolio gates* — and beneath it two committees
each emitted a recommendation, a confidence float and a summary they
had written themselves.

Three things followed from that shape, and all three were visible in
the output:

- **A committee named an action.** `STRONG_BUY`, `SELL`. Constitution
  §9 reserves that for the Artificial CIO, and a committee that says
  `SELL` has decided.
- **A committee's grounds were unrecoverable.** The opinion carried
  its own prose, so nothing downstream could say which finding a
  position rested on — or check that one existed.
- **Confidence measured the wrong thing.** It was an average of three
  numbers that were themselves judgments, and the figure the dossier
  labelled *committee agreement* was the mean of those averages. Two
  committees flatly contradicting each other on well-read evidence
  scored higher than two agreeing on thin evidence.

The enabling defect sat one layer lower. `Finding` carries the `Sense`
its signal read it with — the platform's one record of polarity — and
the evidence builder flattened every finding to a bare string on the
way out. The polarity was computed and discarded, so every layer above
either re-derived it or did without.

---

## The object

```text
CommitteeOpinion
  committee          the panel, named
  remit              the readings it speaks for  (frozenset[Dimension])
  stance             strongly_positive … strongly_negative, or None
  abstained_because  worded, exactly when stance is None
  supporting         Finding.ref[]  — addresses, never prose
  opposing           Finding.ref[]
  uncertainty        Uncertainty[]  — what it could not settle
  confidence         Confidence | None  — counted, never supplied
  decided_by         the named rule that produced the stance
  summary            one line, composed from the counts
```

### Five rules that shape it

**A committee advises; it never decides.** `Stance` replaces
`Recommendation`, and *replaces* rather than joins it — two
enumerations for *what this committee thinks* is the duplication
invariant 9 exists to prevent. A stance is a position; what to do
about it is resolved one layer up, against policy and the portfolio.

**Polarity is never invented.** `supporting` and `opposing` are
selections over findings whose `Sense` the producing signal recorded.
This layer classifies nothing; it counts what the signals already
said.

**Evidence is referenced, never restated.** Every entry is a
content-addressed `Finding.ref` into the case's own ledger. A
committee carrying its own wording could state something the platform
never read, and no surface downstream could tell.

**Not knowing is not a position.** A committee shown nothing abstains,
worded — it does not return `NEUTRAL`. The platform paid for this
distinction twice: a Risk Committee returning `HOLD` read as *risk is
acceptable*, and the same committee returning confidence `0.0` dragged
committee agreement down as though it had objected. `stance=None` is
not a sixth stance and never averages.

**An opinion that cannot name its rule cannot exist.** The bar the
decision tables already hold themselves to. A conclusion whose rule is
invisible can be believed but not challenged.

### What made references possible

`Finding` gained a `Dimension` — which reading produced it —
**preserved at composition, never inferred**. Every finding on this
platform is built where the producing signal is known by name
(`signals.value.evidence`, `signals.quality.evidence`, the risk
signal's own list, the analysts' verdicts). That knowledge was being
dropped, exactly as `Sense` had been dropped before it.

A committee's remit is a set of dimensions. Reading a remit off
preserved provenance is the difference between a committee that
reports what a reading found and one that pattern-matches sentences.

`FindingLedger` is the canonical list, addressed by content hash
rather than position — a positional index would silently come to point
at a different finding the moment a signal changed its reporting
order. The ledger travels on `DecisionEvidence` and on
`ExecutiveDecision`, so a decision preserves both the findings it was
reached over and the positions taken on them.

### Confidence

Every field is a count of something that happened: inputs the remit
asked for, inputs measured, findings by sense, uncertainties
outstanding. There is no input float, no weighting and no scale
factor.

Confidence measures **the reading, not the security**. A low figure
says this committee saw less than it asks for; it never says the
business is worse. Stance and confidence are orthogonal on purpose —
folding completeness into the stance is what made a bearish view
tentative by construction.

The counts travel with the band, always: `Agreement` learned first
that "narrow" printed without `3/5` is an interpretation wearing the
authority of a measurement.

### What is deliberately absent

**A ranking of findings.** The owner asked for *strongest* supporting
and opposing evidence. This platform does not measure how strong a
finding is, so `supporting` and `opposing` are in the order the
signals reported, and the docstrings say so. Presenting that order as
strength would publish a measurement nobody took. Earning a real
ordering needs a strength this platform can defend — the obvious
candidate is `FactOrigin`, once established facts reach a committee's
remit at all.

**Any knowledge of another committee.** No opinion consumes, ranks or
answers another. The property is borrowed from the assessment
contract, where it is constitutional: committees that negotiated
before the Executive layer ran would move the adjudication a layer
early, and the losing position would vanish before anything recorded
it. `Panel` reads the opinions together; no committee can see it.

---

## The Executive synthesis

`DecisionSynthesis` gained two parts, and every string in both is
either carried verbatim from a canonical object or is one of the
builder's own worded absences.

```text
Supporting case  because      + which committee stood on each fact
Reservations     despite      + which committee stood on each fact
Uncertainty      uncertainty  + which committee could not settle it
Decision         deliberation what prevailed, over what, and why
```

**Uncertainty is its own part**, not a footnote to the opposing case.
A fact against the security is a reason to hesitate; something
unmeasured is a reason the platform cannot yet say. Folding the second
into the first is how not knowing becomes bearishness — the mirror of
the estimated figure invariant 1 forbids, and the reason
`UncertaintyKind` separates *missing*, *conflicting*, *absent* and
*outside current knowledge*: they differ in what would close them,
which is the only thing an investor can act on.

**The Decision part states a procedural truth, because that is the
true one.** The Artificial CIO gates on measured scores; it does not
tally committee stances. A sentence implying the stances had been
weighed would describe a deliberation that did not happen. So the
synthesis reports what the committees held, names the position that
did not carry, and says plainly that the gate decided.

That is also the honest limit of this slice: it makes the reasoning
**visible and auditable**; it does not make the committees' positions
**causal**. Making them causal is the assessment layer's job (§5).

### One defect found and fixed in passing

`_dissent` originally chose which side lost by reading
`state.belongs_to_watchlist`, which is true for every state except
`REJECT`. Under `PREPARE` — a case held back — it named the *negative*
committee as overruled, when the platform had in fact declined to
follow the positive one. Four of the five states reported the wrong
dissent. Only `RECOMMEND` acts on the bullish case; everything else
declines to act now.

---

## §4 — Investment profiles: the determination

The owner asked whether High Growth / Compounder / Turnaround /
Cyclical / Income should be **inferred**, be **committee
conclusions**, or **emerge from existing evidence** — and asked for a
determination, not an implementation.

**Determination: none of the three as posed. The need is real, the
layer that owns it already exists, and the evidence it would need does
not.**

### They are not a classification the platform is missing

The platform already classifies a company twice, and the owner has
already ruled that these are two different classifications that must
never be merged:

- `Archetype` — what kind of business it is, established from its own
  filing at quorum;
- `FinancialModel` — what language its statements speak, established
  from the statements.

A profile is neither. *High Growth*, *Turnaround* and *Cyclical* are
not claims about what a business **is** — they are claims about
**where it sits in its own trajectory**. That is a statement about a
time series.

### The platform holds no time series of established facts

This is the decisive constraint, and it is a measurement gap rather
than a design question:

| Profile | What would establish it | What is held today |
|---|---|---|
| High Growth | revenue growing across ≥2 comparable periods | one period at quorum |
| Compounder | returns on capital sustained across periods | one period at quorum |
| Turnaround | a measure that was worse and is improving | one period at quorum |
| Cyclical | a full peak-to-trough cycle | one period at quorum |
| Income | distributions sustained across periods | not acquired |

The Financial Statement Domain establishes **one period**. Every
profile in the owner's list needs at least two, and two of them need
many.

So *inferring* a profile is estimation — a plausible label on an
investment dashboard, which reads as a measurement, and which
invariant 1 exists to forbid. "High Growth" printed beside a company
whose growth was never measured is the estimated figure wearing a
name.

### And a committee must not conclude one

A committee states a position on evidence; it does not establish facts
about the company. The stack's verbs are already settled:

```text
Knowledge establishes.  Understanding describes.
Assessments imply.      Decisions conclude.
```

A committee concluding *this is a Compounder* would be a committee
**establishing**, which is two layers away from its own verb. Worse,
a profile set by one committee and consumed by another is precisely
the cross-committee dependency this design and the assessment contract
both forbid.

### Where it belongs when the evidence exists

The owner's real requirement — *the same metric does not mean the same
thing for a growing company as for a mature one* — is **already owned
by an accepted layer**. The playbook ruling states it outright:
playbooks choose which financial questions are meaningful per company
kind, and supply the thresholds.

So a profile should enter as **one more established fact consumed by
playbook selection**, never as a third taxonomy standing beside the
archetype and the financial model. That keeps one business concept in
one implementation, and it means the profile changes *which questions
are asked* rather than adding a label to a dashboard.

### The smallest slice that would earn it

Per §19a — case by case, never taxonomy-first:

1. Establish period-over-period revenue for **one** corpus company at
   quorum. JPM is the candidate: it is the one company already carried
   filing → statements → authoritative playbook, and it is already
   measured for a single period.
2. Add **one** profile whose rule is deterministic and obvious over
   that fact, and whose absence changes nothing.
3. Require a live case where the profile changes which question the
   playbook asks. No such case, no profile.

Until step 1 exists, no profile should be introduced under any of the
three mechanisms the question offered.

---

## §5 — For the owner: two decision stacks

Recorded because it is an owner's decision, not an implementation
detail, and because this slice necessarily landed on one side of it.

The repository carries **two live decision paths**:

| | Executive pipeline | Canonical decision layer |
|---|---|---|
| Entry | `ExecutivePipeline.execute` → dossier | `movrvest decide` → `entry_question` |
| Evaluative objects | committees (this document) | `InvestmentAssessment` — **none exist** |
| Output | `ExecutiveDecision` — state + conviction | `InvestmentDecision` — verdict + weighed implications |
| Reaches the investor | yes | no |

`INVESTMENT_ASSESSMENT.md` is **frozen** (accepted 2026-08-08) and its
kind vocabulary is *empty at birth*. Because no admissible assessment
exists, `entry_question` can only ever reach `MONITOR` by
`entry-no-assessment-establishes-a-case` — which is exactly what
`JPM.entry.0001` records.

That document also says, of the canonical evaluative object: *"Not all
analysts. Not committees."*

**This slice does not contravene it.** It lives entirely on the
executive pipeline; committees offer no course and name no action; and
no committee knows another exists. But the owner should decide which
of these is intended:

- **(a)** The committee layer is the executive pipeline's presentation
  of reasoning, and the canonical decision layer grows its own
  assessments separately. Two paths, deliberately.
- **(b)** `CommitteeOpinion` is the shape the first
  `InvestmentAssessment` kinds should take, and the two paths converge
  — in which case the frozen contract is amended here, by the owner,
  as it requires.
- **(c)** The executive pipeline is legacy and should be retired once
  the assessment layer produces its first kind.

Nothing in this slice forecloses any of the three. The recommendation
is **(b)**, on one observation: the committee object was designed to
the assessment contract's own properties without being asked to be —
referenced evidence, named rule, worded absence, no cross-talk — and
the only real divergence is `Confidence`, which the assessment
contract bans as a number and this object derives entirely from
counts. That is a narrower gap than two parallel stacks.

---

## What this slice measured

- 1500 tests green; `mypy` clean over 477 files; frontend build green.
- 42 new tests across `test_canonical_committee_opinion.py` and
  `test_executive_deliberation.py`, including an end-to-end case that
  runs the real pipeline and asserts every committee reference
  resolves in the decision's own ledger.
- Two defects fixed in passing: the writer formatted a 0-to-1
  confidence with `:.0f`, so every committee reported confidence `0`
  or `1` to the model writing the investor's narrative; and the
  dissent side was read off the wrong state property.
