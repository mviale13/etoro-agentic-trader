# Knowledge Consensus Architecture

Status: **Accepted** (2026-08-07) — agreed for implementation as a narrow
vertical slice: the domain model, derived-on-read consensus over the
already-stored observations, and the archetype engine as first consumer.
Automatic quorum acquisition for every company is deliberately **not** in
scope until the domain model is proven. The decisions that closed the
open questions are recorded at the end of this document.

---

## Why this document exists

The reader calibration measured something that changes what a stored
`CompanyKnowledge` *is*. Fifty readings of five immutable 10-Ks: every
segment size agreed in every reading, and everything a model reads out of
prose moved — ways of earning to 6 of 10, cited spans to 3 of 10, NVIDIA's
archetype to 6 of 10. The document never changed. The rules never changed.
The variance sits entirely in the one layer that asks a model.

So Company Knowledge is not a deterministic artifact. **It is an
observation** — one draw from a distribution the platform has now measured
— and the store presents that draw as the company's own account of itself.
Caterpillar's stored entry is a one-in-twenty reading, and it changes the
archetype.

The governing principle for the fix, stated before any mechanism:

> **Consensus must be a property of repeated independent observations of
> immutable evidence — never a preference for more complete, more useful,
> or more classifiable outputs.**

Every design decision below is tested against that sentence.

---

## Two concepts, kept apart

**An Observation** is one reading of one immutable document, by one
configured reader, under the platform's full contract — grounding,
identity, applicability, the bounded repair, all of it. It happened at a
time, it carries its provenance, and it is never revised. The object this
platform today calls `CompanyKnowledge` already *is* one: it carries
`reading: Provenance` and always has.

**A Consensus** is a statement about a *set* of independent observations:
what they agree on, claim by claim, and how far. It is derived by
arithmetic — deterministic given the observation set, the way a
`MeasuredShare` is deterministic given its two figures — and it carries
its width everywhere it goes.

An observation answers *"what did one reading find?"* A consensus answers
*"what do readings of this document reliably find?"* The platform today
stores the first and presents it as the second. The defect is not that
N = 1; it is that N = 1 was presented without its sample size.

---

## What is deterministic and what is observational

The line does not run where it appears to. It runs exactly along *who
produces the content*: the platform, or a model.

**Deterministic** — same input, same output, every run:

- Document acquisition: the bytes (hash- or accession-keyed), flattening,
  table parsing, region reading, structural section location, filing
  selection, identity checks against GLEIF and the registers.
- Verification: grounding of spans, cell read-back, ownership and
  proximity checks, share arithmetic.
- Everything downstream of knowledge: the archetype rules, the gates,
  rendering.

**Observational** — a model contributed, and stability is a measurement,
never an assumption:

| Claim | Measured stability (worst case) |
|---|---|
| which segments the document names | 7/10 (JPM) |
| which cell holds a segment's size | 10/10, all 16 segments |
| which ways a segment earns | 6/10 (NVDA, DIS) |
| whether a segment is described at all | 7/10 (META) |
| which span is cited for that | 3/10 (DIS, CAT) |
| the company's own self-description | not yet dimensioned — unmeasured |

The sizes' 10/10 is an *outcome*, not an exemption. A size stays
observational in this model; what makes its variance measure zero is the
shape of its evidence — the model only points at a cell, and the platform
reads the cell and does the division. That is worth stating as the
measurement's central lesson:

> **Verification removes falsehood, not variance.** Every one of the
> fifty readings that passed the checks was true of the document — and
> the readings still disagreed, because they disagreed about *which true
> things to report*. What survives verification is selection variance
> among grounded answers.

Which reframes what consensus is for. Consensus is **not**
error-correction — grounding, identity and applicability already did
that, deterministically, per observation. Consensus adjudicates
**representativeness**: among answers that are individually verified,
which one do independent readings reliably give?

---

## The consensus function

### The unit is the claim, and the claims already exist

Invariant 4 carved a segment into independent claims, and the calibration
already measures agreement along exactly those lines. Consensus reuses
that decomposition, unchanged:

- the document's segment set (identity) — one claim, the set taken whole;
- per segment: its size (share and cell), its ways of earning (the set
  taken whole), whether it is described at all, and the span cited.

A claim's answer is compared as the observation stated it. **The set is
atomic**: "manufacturing, services" and "manufacturing" are two answers,
not a vote on each element.

### Consensus selects; it never synthesizes

Every consensus answer must be an answer some observation actually gave,
verbatim. This is the guard that keeps consensus from becoming
generation.

The alternative — per-element voting on sets — was considered and
declined. Observations {a}, {b}, {a, b, c} would elect {a, b} by element
majorities: an answer *no reading gave*, assembled by the platform and
indistinguishable on the surface from something a reading found.
Selecting among observed answers can never introduce a statement that
was not observed; composing can.

### The rule: strict majority of those who addressed the claim

A claim settles when a strict majority of the observations that
addressed it gave the same answer. Anything less — a plurality, a tie —
leaves the claim **unsettled**, and an unsettled claim carries its full
answer distribution wherever an absence would carry its reason.

"Addressed" matters: a segment three readings named and seven never
mentioned has its per-segment claims counted over three. The seven said
nothing about it; counting silence as dissent would report one
instability twice.

### Content-blindness, including the hard case

The aggregation never looks at what an answer *says* — only at how many
observations said it. Concretely:

- **A worded absence is an answer with full standing.** "Not described"
  can win the vote. META's Reality Labs reads *not described* 7 of 10,
  against three readings that each found a real, grounded, structurally
  owned product description — and consensus settles on *not described*.
- **Ties and pluralities are never broken by preference** — not by
  completeness, not by informativeness, not by recency, not by order.
- **The observation budget is fixed before the first observation is
  taken.** Never one more reading because the result so far displeases —
  that is read-until-classifiable through the back door, and
  `architecture.md` already forecloses it for a single reading. A
  stopping rule may reference agreement *counts*; it may never reference
  answer *content*.

The hard case deserves its argument, because it looks wrong before it
looks right. If even one reading found a span that passed every
deterministic check — grounded, in the owning region — isn't that span
simply *true*, however many readings failed to find it? Shouldn't
verified presence beat counted absence?

No, and JPMorgan is the measured exhibit. The one reading in ten that
"described" Asset & Wealth Management cited *"three reportable business
segments – Consumer & Community Banking ("CCB"), Commercial & Investment
Bank ("CIB") and Asset & Wealth Management ("AWM") –"* — the boilerplate
sentence listing the segments. It is grounded, it sits where the checks
allow, and it describes nothing. The deterministic checks are necessary,
not sufficient: they remove *provable* inapplicability, and what remains
— is this actually what the filing says the segment does? — is exactly
the judgment that varies between readings. The mode is the only
instrument the platform has for that residue, and it only works if rare
presence can lose to common absence.

The cost is accepted knowingly: META's three genuine Reality Labs
descriptions lose the vote too. They are preserved as the minority in
the distribution — and the road to recovering them is *better
deterministic structure*, the treatment that took sizes to 10/10, never
a consensus rule that prefers presence. That keeps the improvement
pressure on the layer that can honestly absorb it.

---

## Independence

What makes the observations independent, and therefore makes their
agreement mean something:

- **Same bytes.** The document is fetched once per batch, and the store
  key — accession or content hash — pins identity across batches. Two
  observations of one key are observations of one string.
- **No observation sees another.** Each reading is a fresh request with
  no shared conversation state. Concurrency is a courtesy to the
  provider's rate limit, not a dependency between readings.
- **Retries and repairs live *inside* one observation.** The grounding
  retry (`MAX_ATTEMPTS`) and the bounded description repair are part of
  the protocol that produces one valid observation, and every
  observation runs the identical protocol. Independence is a property
  *between* observations, not within them.

---

## The objects

**`CompanyKnowledge` becomes `CompanyObservation`.** A rename that makes
the object what it always was. It changes no field: the object already
carries the provenance of one reading. Everything the extractor returns
is an observation, and the extractor never produces anything else.

**`CompanyConsensus` is new**, derived from
`tuple[CompanyObservation, ...]`. It mirrors the observation's shape
claim for claim, and every claim carries its `Agreement` — the type that
already exists in `app/domain/reader_stability.py` and already holds
exactly this: the distinct answers, who gave them, the modal answer, the
width. One uncertainty vocabulary, one implementation (invariant 9).

An unsettled claim surfaces through the machinery the platform already
has: the absence fields. `undescribed_because` and `unmeasured_because`
gain one more possible reason — *unsettled across N readings* — with the
distribution attached. Downstream layers already handle worded absence,
which is what keeps this migration from touching every consumer's logic.

**The store holds observations; consensus is derived on read, never
stored.** Two standing precedents decide this. `MarketSnapshotArchive`
stores the quotes and recomputes mood on the way out, so a changed
threshold leaves no stale conclusions behind it; and the tabular-evidence
rule — *storing an answer beside its inputs creates a second place for
it to be true* — applies to a consensus exactly as it applied to a
share. If the consensus rule ever changes, every consensus changes with
it, because none was ever written down.

**Schema 9 carries the schema-8 entry forward as observation one.** This
is a re-labeling, not an upgrade-in-place, and it does not collide with
the store's prohibition on upgrades: that prohibition exists because
filling in what a reading never captured is inventing it. Relabeling a
reading as *one reading* invents nothing — it records precisely what the
entry always was.

---

## Who consumes what

```text
extractor ──▶ CompanyObservation ──▶ store (N per document key)
                                        │
                                        ▼  derived on read, deterministic
                               CompanyConsensus
                                        │
                                        ▼
        Brain · ArchetypeEngine · playbooks · dossier · API · surfaces
```

- **The decision path consumes consensus, only.** An observation reaches
  a decision through the consensus function or not at all.
- **Instruments consume observations.** `reader-stability` keeps reading
  raw observations, and audit surfaces (`movrvest knowledge
  --observations`, say) may show them — labeled as observations.
- **Conclusions are functions of consensus facts — never votes over
  conclusions.** The archetype is `classify(consensus)`, not the modal
  archetype of per-observation classifications. The rules stay pure
  functions over facts (invariant 5's separation); voting over their
  outputs would let the answer distribution reach into the rule layer
  and would count the same disagreement twice. On the measured corpus
  the two routes happen to agree; the layering, not the coincidence, is
  what decides.

A consensus is not a conclusion, and storing observations does not breach
"the Brain stores facts, never conclusions": *6 of 10 readings said X*
is a fact — about the platform's observations — and is stored and
derived as one. What those facts add up to remains the rules' decision.

---

## Uncertainty is stated, never hidden — and never a probability

- Every consensus claim carries **k of n**. Every unsettled claim
  carries its distribution. Surfaces that show consensus facts state the
  width in their provenance line — "read 5 times" beside "via SEC
  EDGAR" — the same idiom that already states staleness and degradation.
- Nothing is called a probability. "6 of 10 readings" is a count of
  something that happened. The chance that an eleventh reading agrees
  was not measured and is not stated.
- **"Settled" means reproducible, not true.** A wrong-company filing
  read ten times agrees ten times. And that is why consensus is **not**
  a fourth boundary beside identity, grounding and applicability. Those
  three are **admissibility** boundaries: they decide whether an
  observation may enter trusted knowledge at all, and consensus cannot
  rescue an observation they refused. Consensus is a **stability**
  boundary: it decides whether multiple *admissible* observations are
  reproducible enough to support downstream interpretation. An
  unsettled consensus does not mean the observations are untrue — every
  one of them passed admissibility — it means the platform cannot yet
  claim representativeness.

  ```text
  Identity · Grounding · Applicability     (admissibility — per observation)
                  ↓
        Admissible observations
                  ↓
        Consensus / stability              (representativeness — per set)
                  ↓
        Business Understanding
  ```
- Consensus also does not measure completeness: ten readings that all
  miss the same thing agree perfectly. Coverage remains its own quality,
  which is why the platform reports three layers apart:

  ```text
  Acquisition Coverage  →  Knowledge Stability  →  Business Understanding
  ```

### Four words, kept apart (added on acceptance, 2026-08-07)

NVIDIA supplied the exhibit that forced this refinement: a claim that
leaned one way over ten calibration readings settled the other way over
a five-observation quorum. The system behaved correctly both times —
and it proves that *settled* must never be read as *unlikely to
change*. So four properties are distinguished, and no surface or
consumer may collapse them:

```text
Quorum              Enough observations exist.
Consensus           One observed value carries a strict majority.
Agreement strength  The winning count and the complete distribution.
Robustness          Whether the consensus survives further observations.
                    NOT ESTABLISHED — for anything.
```

Consequences in the implementation: every majority is worded with its
count ("a narrow majority (3/5)" — never "narrow" alone, which would be
an interpretation wearing a measurement's authority); an archetype
carries the narrowest claim it consumed, distribution included, and its
`rests_on` wording states outright that survival under further
observations has not been established; below quorum, a width-1 claim is
a *width*, not an agreement — "unanimous (1/1)" is arithmetic dressed
as consensus and is never printed. Downstream consumers must not treat
all majority outcomes as equally stable, and the machine-readable gate
for that is the archetype's `quorate` flag and `narrowest` agreement.

Sequential sampling and statistical confidence are deliberately not
built. Showing 3/5, 4/5 and 5/5 prominently is the first version.

## Acquisition policy (decided 2026-08-07)

The mechanism to fill a quorum exists; when its cost is paid is policy,
explicit and separate:

- **Width 1 is sufficient for developer inspection.** `movrvest
  knowledge` serves it, labeled.
- **Quorum is requested before an archetype becomes authoritative.** A
  conclusion from a width-1 entry is served and labeled
  non-authoritative; a consumer that lets an archetype steer anything
  checks `quorate` first.
- **Additional observations are acquired on demand** — the natural
  hook is opening or refreshing a dossier — not as a side effect of
  asking what the platform knows.
- **No automatic portfolio-wide rereading** until its latency and cost
  are measured.
- **Never adaptive stopping on content.** An observation run stops on
  the count, whether or not the result classifies. This is the
  read-until-classifiable boundary and it does not move.

---

## Acquisition policy and cost

- **Quorum N = 5**, odd so a bare majority exists, reasoned rather than
  measured — and its docstring will say so, like the archetype
  thresholds before it.
- **Taken as one batch at acquisition.** A new document costs one fetch
  and five readings (~5× today's reading cost; CAT ran ten readings in
  80 seconds wall at concurrency 4). The entry is complete when written,
  and `available_acquired` keeps meaning what it means. Accumulating one
  observation per cycle was considered — it spreads cost, but it leaves
  the platform serving a width that changes between cycles and makes
  "acquired" a moving state; declined for now and revisitable.
- **A new filing is a new key and a fresh quorum.** Old observations
  stay with their old key — immutable history of an immutable document.
- **Before quorum exists** (a cached schema-8 entry carried forward as
  observation one), consensus is served at its actual width and says so:
  one observation, presented as one. The defect was never N = 1; it was
  the missing label.

---

## Checked against the measured corpus

Worked from the fifty stored calibration readings, no new model calls:

- **NVDA** — Graphics' ways of earning: 6/10 `manufacturing, services`.
  Majority: settles. `classify(consensus)` = Diversified, every time.
  The coin-flip archetype disappears; the 4/10 minority stays in the
  record.
- **CAT** — Financial Products' earning: 5/10 `financial_spread`, 4/10
  `financial_spread, premiums`, 1/10 `financial_spread, services`. No
  strict majority: **unsettled**, absent-with-distribution. Archetype
  over the remaining consensus facts: manufacturing and services tie
  within 5% → **Diversified** — matching the 19-of-20 modal reading. The
  stored one-in-twenty "Service business" could not survive this
  architecture.
- **JPM** — identity settles at three segments (7/10); Corporate is
  reported as an unsettled fourth (3/10), not silently dropped. AWM's
  1-in-10 boilerplate "description" loses to 9/10 *not described* — the
  symmetric-mode exhibit.
- **META** — Reality Labs settles as *not described* (7/10); the three
  genuine product spans are preserved as the minority, and the road to
  them is structural ownership, not consensus preference.

---

## What this architecture forecloses

- Reading until the answer classifies, in any disguise — including an
  observation budget extended after seeing content.
- Any aggregation preference for completeness, informativeness, or
  usefulness.
- A stored consensus.
- A consensus answer no observation gave.
- Presenting width-1 knowledge without its width.

---

## Migration outline (after agreement, not before)

1. **Vocabulary.** Rename `CompanyKnowledge` → `CompanyObservation`;
   store schema 9 holds a tuple of observations per key, carrying each
   schema-8 entry forward as observation one; `CompanyConsensus` derived
   on read, claims carrying `Agreement`.
2. **Consumers.** The decision path moves to consensus; surfaces state
   width; unsettled claims flow through the absence machinery.
3. **Quorum acquisition.** New documents read N times at acquisition.
4. **Business Understanding resumes**, consuming consensus — with the
   noise floor known, so every improvement is checkable against it.

## Decisions (2026-08-07)

The open questions were closed as follows, and these bind the
implementation:

1. **Quorum N = 5, strict majority, uniform across claim kinds.** Small
   enough to control cost, large enough to expose instability, no result
   settles on a tie, and 3/5 is clearly distinguishable from 5/5 — which
   is the second half of the decision: **the full distribution is kept
   and shown, never only the winner.** 3/5 and 5/5 must never look
   identical downstream.
2. **The company self-description does not enter consensus until its
   variance is calibrated.** It is broader than a segment description,
   less structurally partitioned, and legitimately appears in several
   forms — it may behave unlike anything the calibration dimensioned.
   Until measured, the consensus object carries one observation's
   wording, chosen content-blind (the earliest stored observation) and
   labeled as exactly that.
3. **Spans never settle.** The claim settles; the evidence spans remain
   attached to the observations that produced them, and the consensus
   exposes their distribution and provenance. Selecting a canonical span
   would mistake stable wording for stable meaning — the exact
   conflation the calibration caught and split.
4. **Schema-8 entries serve at width 1, labeled, and are never called
   settled.** `observation_count: 1`, `consensus_state:
   insufficient_quorum`. The platform keeps operating on them, and every
   downstream consumer knows it is reading one observation rather than a
   consensus. No corpus-wide quorum re-read is forced at migration — the
   quorum arrives when a document is next observed.
5. **For collections, equality is explicit: order is normalized where
   order carries no meaning, and the collection stays atomic.** A
   ways-of-earning answer is compared as a sorted set; it is never
   decomposed into per-element votes, because a per-element winner could
   be a set no observation asserted — a value with no observational
   provenance, which nothing could walk backward to a reading that said
   it.
