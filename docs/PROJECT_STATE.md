# MOVRvest Project State

---

# Mission

MOVRvest is an Artificial Chief Investment Officer.

Its mission is to help investors make better long-term investment decisions
through transparent, explainable, evidence-based and continuously improving
intelligence.

MOVRvest recommends. The investor decides.

---

# Current Status

## Product

Status: 🚧 Active Development

The canonical pipeline runs end to end. A decision travels from eToro and
market data, through perception, reasoning, committees and the Artificial
CIO, to an executive brief on the CLI and the dashboard.

## Architecture

Status: 🟢 Cognitive Architecture v5.0, implemented

v5.0 is no longer only a design. See
[`architecture/REPOSITORY_INVENTORY.md`](architecture/REPOSITORY_INVENTORY.md)
for the package-by-package mapping, verified against the import graph.

---

# Repository Health

Green baseline, measured 2026-08-07. A figure here is an observation with a
date, not a standing claim — refresh it at slice boundaries, and keep the
test count in [`CLAUDE.md`](../CLAUDE.md) in step, so a later session does
not inherit a quality state that has silently drifted.

| Area | Status |
|------|--------|
| Ruff | 🟢 Clean |
| Mypy | 🟢 Clean |
| Pytest | 🟢 1101 passing (2026-08-07) |
| Backend | 🟢 Stable |
| Frontend | 🟢 Builds clean |
| Duplicate implementations | 🟢 Removed |

Verify the **commit**, not the working tree. Pre-commit stashes unstaged
changes but leaves untracked files in place, so hooks can pass on a tree the
commit does not contain:

```bash
git archive HEAD | tar -x -C /tmp/headcheck && cd /tmp/headcheck \
  && python -m mypy app && python -m pytest -q
```

---

# What Works Today

- `movrvest evaluate SYMBOL` — the Artificial CIO's decision and reasoning
- `movrvest brain` — what the Brain currently knows
- `movrvest record` — what each decision's security did next, or why it
  cannot be measured yet
- `movrvest knowledge SYMBOL` — what was read from a company's own annual
  report, with the table, row and column behind every measured size so the
  evidence can be checked against the filing by hand. Developer-level
  inspection, deliberately: it presents the evidence and decides nothing
- `movrvest writer-compare SYMBOL` — the identical investment case worded
  by every configured writing provider, with measured latency, reported
  token usage and cost at stated prices beside each narrative
- `GET /executive/portfolio` — every holding, ranked by conviction
- `GET /executive/{symbol}` — one investment case
- `GET /brain/` — portfolio facts, investor observation and DNA
- `GET /research/candidates` — the watched securities, judged and ranked
- The dashboard renders real account data and a real brief
- The portfolio page states the deepest fall the account has taken, the
  days it ran between, and how far below that peak it still sits
- The portfolio page reports overall risk and its four measured
  components, each with the evidence behind it
- `GET /market/` and the markets page report every instrument the
  platform prices, grouped, with what the average move netted out
- `GET /market/earnings` and the markets page report when each company
  the investor holds or watches reports next — the book's own earnings
  calendar, read once a day from the provider that already prices those
  companies, with "no date published" and "could not be read" stated
  apart, and a window the provider still publishes after the report ran
  filed as "recently reported" rather than sorted ahead of what is
  actually coming
- Every decision is recorded, and the next cycle says what changed
- Every market observation is recorded, and the next cycle says what the
  market did — the mood, the volatility band and the sentiment reading,
  each stated with the figures behind it
- The dashboard change feed reports the decisions the CIO actually changed
  and the market movements that were actually recorded
- The research page runs the CIO over the investor's own watchlists

## Recently completed

- **The playbook is selected from Business Understanding, where that
  route has earned it** (August 2026). The design in
  [`architecture/PLAYBOOK_SELECTION.md`](architecture/PLAYBOOK_SELECTION.md):
  a deterministic mapping from the archetype a quorate understanding
  concluded to the playbook that analyses it, under an unblended
  migration rule. Two rules, because the corpus at quorum has earned
  two — Manufacturer activates **Industrial**, Diversified activates
  **Diversified Business** — and every other conclusion is refused by
  name rather than defaulted, because a default would rebuild the
  industry taxonomy this selector replaces.

  `select_grounded()` is a pure function over `BusinessUnderstanding`
  alone; `PlaybookSelectionService` is the seam where a refusal falls
  back to the pre-existing industry selector, recorded — `selected_by`,
  `fallback_reason` verbatim, and `facts_consumed` empty on fallback by
  invariant, which is the proof the routes never blended. Surfaced by
  `movrvest playbook SYMBOL`. Accepted live on the five: DIS and CAT
  Diversified Business (authoritative; CAT's excluded 2/2/1 can only
  ever reach a refusal, never a silently different playbook), NVDA
  Industrial (authoritative, and contingent — either observed minority
  answer would select Diversified Business, said where the playbook is
  named), META Platform by industry fallback with the grounded refusal
  stated, JPM doubly honest: grounded refused *and* no provider profile
  exists (not on the book), so Unclassified rather than a guess. The
  research path (`ResearchStrategyFactory`, dossiers, committees) still
  consumes the industry selector unchanged; the flip is a later slice.

- **Business Understanding: how a business creates value, explained from
  consensus** (August 2026). Phase 2's first slice, and the first real
  consumer of the knowledge layer's finished contract. Company Knowledge
  answers *what has been established*; `BusinessUnderstanding` answers
  *how this business creates value* — one level above the knowledge, one
  level below the committees. Completely deterministic: no model, no new
  reading, and every statement traces to `CompanyKnowledgeConsensus`.
  `understand()` is a pure function beside `classify`, surfaced by
  `movrvest understanding SYMBOL`.

  The examples in the design conversation ("owns intellectual property",
  "designs semiconductor platforms") were deliberately not built — they
  are not derivable from consensus without inference, and the
  architectural rule outranks the examples. The engine is worded from
  settled segments, settled mechanisms and the archetype only. A
  mechanism is exactly as established as the weakest earning claim
  carrying it, and says so where it is named.

  **The genuinely new computation is contingency analysis.** For every
  earning claim that is narrow or unsettled, the engine evaluates what
  the rules would have concluded had the claim settled at each of its
  *observed* answers — the identical `classify`, over a consensus
  differing in exactly one claim. A statement about the rules, never a
  new fact about the company: no answer is evaluated that no observation
  gave, and nothing evaluated is stored or promoted. It is how "not
  established" gets the explanation it is owed — whether the gap bears
  on the conclusion — without ever being compensated for.

  Accepted live, deterministically, on the three cases:

  - **DIS** (observed to quorum first, per the acquisition policy):
    multi-engine — licensing, services and transaction lead together;
    six mechanisms each with coverage and support; the narrowest claim
    is 4/5, and the contingency shows every observed answer leaves
    Diversified unchanged — the gap does not bear on it.
  - **NVDA**: Manufacturer because manufacturing runs through 100%,
    more than 5% clear; *not* Diversified because Graphics' earning
    settled at `manufacturing`, 3/5 — and the contingency names the
    dependency exactly: either minority answer would conclude
    Diversified.
  - **CAT**: Diversified from the settled claims; Financial Products'
    earning unsettled at 2/2/1 and *excluded, not resolved* — and the
    contingency answers more precisely than the acceptance question
    asked: one observed answer (2× financial_spread, services) would
    conclude "Service business, then manufacturer", which is exactly
    the stored one-in-twenty draw the consensus architecture retired.
    The platform now explains that draw instead of serving it.

  Also this slice: the repository moved from iCloud Drive to the local
  SSD (`/Users/movr/AI Projects/etoro-agentic-trader`) after a
  `fileproviderd` sync storm throttled the old path to ~3 file reads a
  second and made the 4-second test suite look hung. The suite, the DIS
  quorum observation and all three acceptance cases were re-run on the
  new path; the identical tree passed identically, so nothing was
  attributable to the move. PlaybookSelector deliberately stays on the
  industry seam — the flip to consuming Business Understanding is
  recorded as open work with its preconditions in
  [`architecture/MIGRATION_PLAN.md`](architecture/MIGRATION_PLAN.md).


- **A conclusion is as firm as the narrowest claim beneath it, and now
  says so** (August 2026). The three layers the consensus architecture
  supports, made visible, with a terminology refinement NVIDIA forced:
  its Graphics claim leaned one way over ten calibration readings and
  settled the other way over the five-observation quorum — correctly,
  both times — so *settled* must never be read as *unlikely to change*.
  Four properties are now kept apart: **quorum** (enough observations
  exist), **consensus** (one observed value has a strict majority),
  **agreement strength** (the winning count and full distribution), and
  **robustness** (survival under further observations — not
  established, for anything).

  `CompanyArchetype` carries `quorate`, the `narrowest` consumed
  agreement (distribution included), and a worded `rests_on`. The
  archetype surface renders three layers in the order trust is built —
  acquisition, knowledge stability, business understanding — and the
  headline is inseparable from its basis: *"NVDA — Manufacturer,
  resting on a consensus of 5 observations; the narrowest claim beneath
  it is a narrow majority (3/5) — how 'Graphics' earns. Whether that
  majority would survive further observations has not been
  established."* A width-1 entry reads "not a consensus, and nothing
  decided from it is authoritative", and its 1/1 is printed as a width,
  never as unanimity — arithmetic is not agreement. Every majority is
  worded with its count; "narrow" never appears alone.

  Acquisition policy is recorded as policy, not code: width 1 suffices
  for developer inspection, quorum before an archetype is
  authoritative (`quorate` is the machine-readable gate), observations
  on demand at the dossier, no portfolio-wide rereading until cost is
  measured, and never adaptive stopping on content.

- **Knowledge became observations, and what the platform serves is
  consensus** (August 2026). The accepted design in
  [`architecture/KNOWLEDGE_CONSENSUS.md`](architecture/KNOWLEDGE_CONSENSUS.md),
  implemented as the authorized narrow slice: the domain model, the
  derived-on-read consensus, and the archetype engine as first consumer.
  Automatic quorum acquisition for every company is deliberately not
  built yet.

  `CompanyKnowledge` is renamed `CompanyKnowledgeObservation`, which is
  what it always was — one reading, admissible and one draw.
  `CompanyKnowledgeConsensus` is derived by `consensus_of` from the
  stored observations on every read and stored nowhere: a content-blind
  strict majority per atomic claim, over the observations that addressed
  the claim, with quorum 5. Every settled value is verbatim one an
  observation gave; ties and pluralities settle nothing and carry their
  distribution through the existing absence fields; the spans never
  settle at all. The store (schema 9) holds observations append-only,
  and a schema-8 entry restores as one observation — the one legitimate
  cross-schema read, because relabeling a reading as one reading invents
  nothing. Below quorum the platform keeps operating and says so:
  `insufficient_quorum`, "a single reading, not a consensus".

  The three admissibility boundaries and this one are deliberately
  different kinds: identity, grounding and applicability decide whether
  an observation may enter trusted knowledge at all; consensus decides
  whether admissible observations are reproducible enough to interpret.
  Consensus cannot rescue an inadmissible observation, and an unsettled
  consensus does not mean the observations are untrue.

  **Accepted live on the four calibration cases**, each observed to
  quorum (one carried-forward schema-8 observation plus four new):

  - **NVDA — settles, by count and against completeness.** Graphics'
    ways of earning settled at `manufacturing`, 3 of 5, over
    `manufacturing, services` — the *less* complete answer won because
    more observations gave it, which is content-blindness demonstrated
    on live data. Archetype: Manufacturer, from consensus facts, with
    the 2-of-5 minority in the record. (The ten-reading calibration
    leaned the other way, 6/10 — a near-even claim lands either way at
    N=5, and the 3/5 width on the surface says exactly how firmly it
    is held.)
  - **CAT — the one-in-twenty result cannot become authoritative.**
    Financial Products' earning came back 2× `financial_spread,
    services`, 2× `financial_spread`, 1× `financial_spread, premiums`:
    no strict majority, unsettled, refused by the rules with the
    distribution worded. Archetype: **Diversified** — matching the
    19-of-20 modal reading, where the stored single draw had said
    "Service business, then manufacturer".
  - **JPM — disagreement is visible, not removed.** Identity settled 4
    of 5 at three segments; the fifth observation's `Corporate` stands
    in the identity distribution as a minority answer. The boilerplate
    segment-list "description" that passed mechanical checks in a
    minority of readings loses to the counted absence.
  - **META — absence wins with the minority inspectable.** Reality
    Labs settles as not-described 4 of 5, and the one genuine product
    description remains in the span distribution, attached to the
    observation that found it.

  Every acceptance property is also a unit test: no consensus value
  exists that was not present in at least one admissible observation
  (selection, never synthesis — observations {a}, {b}, {a,b,c} elect
  nothing); and changing the consensus rule recomputes results from the
  same files without rewriting a byte of them (the same three
  observations are `insufficient_quorum` at quorum 5 and `quorate` at
  quorum 3).

  `movrvest observe SYMBOL` is the explicit spend that fills a quorum,
  and its stopping rule references the count, never the content — an
  entry stops at quorum whether its claims settled or not, which is
  what keeps observation from becoming read-until-classifiable.
  `movrvest knowledge` renders every claim with its width and prints
  the full distribution wherever agreement is short of unanimous: 3 of
  5 and 5 of 5 never look identical. DIS, NFLX and VOW3.DE remain
  width-1 entries, served and labeled, until they are next observed.

- **The reader is measured before it is improved** (August 2026). The
  platform's first measurement of *itself* rather than of a company, and
  it exists because NVIDIA's archetype moved with its evidence unchanged.
  Every acquisition defect before this one was the platform reading the
  wrong thing. This is the platform reading the same thing twice and
  getting two answers — the document immutable, the rules a pure
  function, and the variance entirely in the one layer that asks a model.

  `movrvest reader-stability SYMBOL --readings N` fetches the current
  document **once** — a primary source is immutable, so one fetch *is*
  every reading's document — and reads it N times under identical
  conditions. It stores nothing, and that is a boundary rather than an
  omission: a calibration that wrote what it read would let whichever
  draw ran last become the platform's account of the company, which is
  the failure it exists to quantify.

  **Fifty readings across five 10-Ks, ten each.** The finding is not a
  single number, because the variance is not spread evenly — it is
  concentrated, and where it concentrates is the point.

  | | DIS | NVDA | CAT | META | JPM |
  |---|---|---|---|---|---|
  | reading completed | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 |
  | segments named | 10/10 | 10/10 | 10/10 | 10/10 | 7/10 |
  | size (worst segment) | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 |
  | described at all (worst) | 9/10 | 10/10 | 10/10 | 7/10 | 9/10 |
  | ways of earning (worst) | 6/10 | 6/10 | 8/10 | 7/10 | 10/10 |
  | span cited (worst) | 3/10 | 4/10 | 3/10 | 7/10 | 9/10 |
  | **archetype** | 10/10 | **6/10** | 10/10 | 10/10 | 10/10 |

  **Every size agreed every time.** Sixteen segment sizes across five
  documents, fifty readings: identical share, identical cell, without
  exception. That is not luck and it is not the model being careful — it
  is the shape of the evidence. A quantitative citation is an *address*
  into a table this platform parsed, checked against the cell it names,
  with the division performed here. The model only has to point; the
  platform does the reading and the arithmetic, so there is almost
  nothing left for it to vary.

  **Everything a model reads out of prose moves.** Ways of earning fall
  to 6 of 10; spans to 3 of 10. The span figure is the softer of the two
  and deliberately reported apart from whether a description was
  established at all — ten readings cited one sentence about Caterpillar's
  Resource Industries eight ways, trimmed at "quarry", at "quarry and
  aggregates", with and without the full stop. As spans that is 3 of 10;
  as an account of what the segment does it is 10 of 10, and only the
  second reaches a decision. Reporting only the first would describe a
  reader that cannot read.

  **So the platform's noise is structural, not incidental.** Variance is
  absent exactly where evidence is an address this platform verifies, and
  present exactly where it is a model's reading of prose. That is a
  measurement of the decision taken in *"a quantitative citation is an
  address, not a span"* — and it says plainly what narrative evidence
  still lacks.

  **NVIDIA is the worst case and shows how noise becomes a conclusion.**
  Its sizes are perfectly stable at 90/10 and both segments are described
  in all ten readings. One segment's ways of earning move — Graphics
  reads `manufacturing, services` six times, `manufacturing` three and
  `manufacturing, subscription` once — and because `services` either does
  or does not run through all 100% of revenue, that single flip crosses
  the rule that separates a ranked archetype from a diversified one. 6 of
  10 Diversified, 4 of 10 Manufacturer. The rules are deterministic and
  behaved perfectly; a coin-flip arrived from above them.

  **A correction this measured.** Caterpillar was reported in the
  previous slice as classifying "Service business, then manufacturer".
  Over twenty readings it is Diversified nineteen times. The stored entry
  holds the single reading in which Financial Products was described as
  earning by `services`, which lifts services above manufacturing and
  ranks what is otherwise a tie. CAT does classify — that part stands,
  and coverage is still 3 of 7 — but *which* archetype was a one-in-twenty
  draw, and the platform had no way to know that until now.

  **What this changes about coverage.** Stored knowledge is one draw
  presented as the company's own account of itself, and every coverage
  figure this repository has published was measured on one draw. Coverage
  and stability are now known to be different qualities: a company that
  classifies every time and one that classifies 60% of the time because
  successive readings disagree are not the same finding, and until this
  slice they were reported identically. Reporting them apart, and
  deciding whether knowledge should be a reading or the modal reading of
  several, is the next question — see
  [`architecture/MIGRATION_PLAN.md`](architecture/MIGRATION_PLAN.md).

  Nothing here is called a probability. An agreement observed over ten
  readings is exactly that, and stating it as the chance a further
  reading agrees would invent a number nobody measured.

- **A section is located where the filer typeset its title** (August
  2026). The first acquisition defect found by asking what was blocking
  Business Understanding rather than what was missing from the evidence,
  and it had been invisible because it failed as an honest-looking
  absence.

  Two of seven filings in the calibration corpus classified. Of the five
  that did not, Caterpillar was the closest: four segments, all four
  described, every way of earning established — and no size, so the
  archetype was *unranked*, which is a statement that the platform knows
  what a business does and cannot order it. The surface said "no figure
  for this segment was proven against a table in the filing". The filing
  prints them in a table. This platform had never seen it.

  **Width is not a property of a section.** A 10-K's sections are located
  by pairing each occurrence of "Item 7" with the closing heading after
  it, and the widest pair won. Caterpillar names Item 7 inside its
  forward-looking-statements note, mid-sentence, and the span from that
  sentence to the next closing heading is 45,096 characters against Item
  7's own 28,215. So the platform read the wrong section — one containing
  none of the five tables the sizes are measured from. Disney, NVIDIA and
  Netflix were right by luck: each of them also has a cross-reference
  competing with its heading, and each happened to lose on width.

  **A heading begins a block; a cross-reference is part of a sentence.**
  Flattened to prose the two are the same string, so the markup is the
  only place the difference survives — the same three-layer shape the
  narrative half already uses, structure read from what the filer
  typeset and position behind it. Measured across the corpus: every
  correctly located section begins its block, and every cross-reference
  competing with one carries between 127 and 540 characters of its
  sentence ahead of it. Among block-starting candidates the widest still
  wins, because a table-of-contents entry begins a block too and what
  separates it is that it runs to its neighbour. A document whose markup
  offers no blocks at all is read by width as before — and asking the
  question anyway would have been worse than useless, because the first
  position in an unstructured document begins a block trivially.

  **The second defect was underneath the first, and only reachable
  through it.** With the right section in hand, Caterpillar's total
  revenue was refused: cited at table 1, row 11, column 6 — the correct
  cell — "whose column carries no header". Row 0 was taken as the header
  row without inspection, and Caterpillar typesets the table's own title
  *inside* the table, so row 0 reads `Sales and Revenues by Segment` and
  nothing else. The row naming the periods is row 1. A title fills one
  cell and holds words, which is a fact about the row's shape rather
  than a reading of what it says; a row holding *nothing* is not a title
  and is not skipped, because a table with no header should have its
  figures refused rather than have a row of data promoted into the role.

  **A missing size now says why it is missing.** Three claims evidenced
  apart is three absences worded apart, and only two of the three were.
  `undescribed_because` existed; the size had nothing, so four different
  causes printed one sentence — and that sentence read as a fact about
  the filing. It is what hid this: reconstructing why Caterpillar had no
  sizes meant re-deriving it from outside the platform. Each cause is
  now worded where it happens, including the one that is not about the
  company at all — JPMorgan's Item 7 is 395 characters naming the pages
  of a document filed separately, so its figures exist and are not in
  the document this platform read.

  Knowledge schema 8; every entry re-read, because an entry written
  under 7 may have been read from a cross-reference and nothing stored
  says so. Measured after the re-read: **three of seven classify, up
  from two.** Caterpillar reads Construction Industries 37%, Resource
  Industries 18%, Power & Energy 48% and Financial Products 6% — each
  naming its cell — and classifies as a service business, then a
  manufacturer. Disney is unchanged at 45/19/38. The four that still do
  not classify are blocked on something else, and each says which:
  Meta's and Volkswagen's descriptions, JPMorgan's separately filed
  discussion, and Netflix's single operating segment, which reports no
  segment table because the segment is the company.

  One caveat the re-read exposed and this slice does not close: NVIDIA
  moved from Diversified to Manufacturer without its sizes changing,
  because a second reading of the same unchanged prose reported one
  fewer way of earning for Graphics. The classification is deterministic
  over the facts; the facts are read by a model, and this is the first
  measurement of how much they move between readings.

- **A description is owned by the section it was printed in** (August
  2026). The narrative half of ownership, replacing a partition that
  Meta's 10-K inverted rather than merely strained. Ownership had been
  the most recent segment naming in flattened prose, with proximity
  (`NEARBY = 300`) standing in for "inside the part of the document
  about this segment". Meta names `Family of Apps (FoA)` and `Reality
  Labs (RL)` twenty-five characters apart, in one summary sentence,
  *after* all the descriptive prose — so both descriptions were refused
  as belonging to nothing the document had named yet, and a targeted
  repair could not have recovered them, because what was wrong was the
  region model rather than the citations.

  Three steps, each in the layer that can honestly perform it:

  ```text
  markup → headings → regions in prose coordinates   (the provider)
  regions + segment names → the owner of each claim  (the domain)
  owner + span → applicable, or a worded refusal     (the domain)
  ```

  - **A heading is the filers' idiom, not an assumption.** SEC filers do
    not use `<h1>`; a heading is a block element whose entire content is
    one short bold span. `Flattened.markup_span` gained an inverse, so a
    heading found in the markup becomes a position in the prose the
    platform cites and nothing downstream sees markup.
  - **A region runs to the next heading**, which is what keeps it
    smallest. Bounded at the end of the section, the last segment would
    own every word about competition, regulation and the workforce.
  - **Uniqueness is the whole safeguard.** The abbreviation the filer
    defined is stripped, and a heading owns a segment when it contains
    what remains, no other heading does, and it names no other segment.
    Ambiguity is never resolved by preference or by order — it means
    there is no structural owner, and position takes over.
  - **Structure decides both ways.** A span inside the owning region is
    a description however deep into the section it sits; a span outside
    it is refused however close it sits to a mention of the segment.
    Existence is still established first and identically.

  Measured across all seven stored readings: six descriptions are now
  carried by structure and four by proximity, and **none was lost**.
  Meta's two segments, which no mechanism could evidence before, now
  have owning regions. Volkswagen has no regions at all — an ESEF
  package's description is assembled from the blocks the filer tagged
  rather than laid out as a section — and keeps the positional
  mechanism. Knowledge schema 7; entries written under 6 are re-read,
  because what was wrong in them is not repairable from what was stored.

- **Evidence is repaired for a claim, never searched for** (August 2026).
  The knowledge layer's first second chance, and it is deliberately not
  a retry. A retry asks the same open question again and takes whichever
  answer passes, which turns the objective from *read this document*
  into *find something acceptable*. A repair asks a closed question
  about a claim already made: these words were refused as evidence for
  it — is there better evidence in this document, or none?

  Four things make that boundary structural rather than instructed:

  - **The claim cannot move.** A repair returns a span and nothing else.
    `repair_schema` has exactly one field, so a repair that wanted to
    add a revenue model or rename a segment has no way to say it, and
    the ways of earning come from the first reading.
  - **Only a refused citation is repairable.** A segment described with
    no words at all made no claim, so none is attempted — Volkswagen's
    three segments are untouched.
  - **Exactly one attempt.** No loop. A repair that fails is not asked
    again, and a test counts the requests.
  - **The same contract applies.** A repaired span goes through the
    identical applicability check. Coverage improves by asking better,
    never by accepting more.

  A repaired span carries `DescriptionRepair` — why the first citation
  was refused, and what performed the repair — through the store and
  onto the surface, so a second answer is never shown as a first. Schema
  version 6.

  **It recovered nothing, and that is the finding.** Every repair on the
  live population was either refused again on identical grounds (Meta)
  or answered honestly that the filing contains no such words
  (JPMorgan). The mechanism is correct and the boundary held; the defect
  is elsewhere, and this measured where. Meta's 10-K introduces both
  segments together and then describes them in order, so the first
  segment's description falls after the second's naming — and Reality
  Labs' own description sits 402 characters from its naming against a
  `NEARBY` of 300. The citation was never the problem. The partition
  was.

- **A company is classified by what it earns from, not by its industry**
  (August 2026). The first thing this platform *concludes* rather than
  reads. `ArchetypeEngine` is a pure function over `CompanyKnowledge`:
  no model is asked, and none could be, because a model asked "what kind
  of business is this?" answers from what it knows about the company —
  which is the outside taxonomy this layer replaces.

  **Coverage, not revenue.** A filing states what each segment earned
  and which ways of earning it uses; it never splits the one between the
  others. So a way of earning is weighted by the size of the segments
  that use it, and the number is called coverage because calling it a
  revenue share would be read as a measurement nobody printed.
  Coverages overlap and do not sum to 1.

  **Four regimes, because size and description fail independently.**
  Ranked (NVIDIA: manufacturing runs through 100% of revenue, licensing
  through 90% — a manufacturer). Diversified (Disney: licensing,
  transaction and services each run through all three segments and no
  arithmetic separates them). Unranked (Caterpillar: four described
  segments, no size proven, so the ways it earns are known and cannot be
  ordered). Undecided (Meta: 100% of revenue measured, 0% explained,
  because both segment descriptions were refused). Diversified and
  unranked are deliberately different answers — one is a finding about
  the business, the other is an absence of measurement.

  **The rules refuse to read names.** Volkswagen reports a segment
  called *Finanzdienstleistungen* worth 19% of revenue and nothing
  concludes that Volkswagen lends, because no description of it was
  established. Reading meaning out of a label would be a taxonomy again,
  this platform's own, in German.

  Calibrated against eight filings read for the purpose — DIS, NVDA,
  META, NFLX, CAT, JPM, VOW3.DE, and COST, whose extraction was refused
  outright. The thresholds are reasoned rather than measured, and say so
  in their own docstrings: unlike `NEARBY`, there is no observed gap
  between two populations to place them in yet.

  Surfaced by `movrvest archetype SYMBOL`, which prints the answer, then
  every rule that fired, then the facts each rule read, then what was
  not established. Nothing consumes it yet: `PlaybookSelector` still
  reads the provider's industry, and flipping that seam while two thirds
  of the population is unclassifiable would degrade every holding whose
  filing has not been read.

- **A description must be about what it is attached to** (August 2026).
  The narrative half of applicability, and the same failure in a
  different shape. Reading Volkswagen's segment note, all three segments
  were cited with one sentence — *"Die Vorjahreswerte entsprechen der
  geänderten Berichtsstruktur"* — exactly present, about accounting, and
  describing no segment at all.

  **What a table gives a number, prose gives a description: position.** A
  figure belongs to the row whose label leads it; a description belongs
  to the segment whose name most recently precedes it. The document's own
  naming of its segments partitions the prose the way row labels
  partition a table, and this platform computes that partition rather
  than accepting it.

  Two rules, both measured on real filings rather than chosen.
  **Ownership** — the span sits under this segment's name and no other's
  — refuses two of Volkswagen's three outright. **Proximity** refuses the
  third, which passes ownership by accident because the footnote follows
  the last segment named. Sound citations measured 0, 23 and 51
  characters from their naming; the boilerplate measured 814 and 1474.

  Deliberately **not** a rule: that the span contain the segment's name.
  Two of Disney's three sound citations do not, so requiring it would
  reject good evidence and drive a reading toward quoting headings.

  **A segment became three claims, evidenced apart.** The rule's first
  consequence was that Volkswagen lost everything, because one span
  proved both that a segment existed and what it did. Identity (the
  document names it), size (two cells of one table) and description (a
  span printed under that name) now fail independently, and only an
  identity failure discards a reading. Volkswagen keeps its segments and
  its measured sizes and reports what they do as absent — with the reason
  in words, because every absence in this platform carries one.

  **Two defects only a live document exposes**, both silent, because an
  inapplicable description is an absence rather than an error. Disney's
  Entertainment section says "non-sports focused global film", which
  normalised to letters contains "sports" — read as a naming, it opened
  the Sports region inside Entertainment's and refused Entertainment's own
  description. And case folding changes a string's length: German "ß"
  folds to "ss", so folding a document before indexing it shifted every
  later position, and Volkswagen's report appeared never to name "Pkw und
  leichte Nutzfahrzeuge" — discarding the whole reading, sizes included.

  Verified live. Disney: three descriptions at 0, 0 and 29 characters,
  sizes unchanged. Volkswagen: three descriptions absent, three sizes
  intact at 76 / 13 / 19%, and the reading now leaves the span empty
  rather than borrowing the footnote. Knowledge schema version 5.

- **The reader is wired into the pipeline** (August 2026). The evidence
  model was sound and nothing used it: `CompanyKnowledgeService` defaulted
  to no reader, so the pipeline had never read a filing on its own. It
  now composes one from configuration.

  **The reader is configured apart from the writer, and that is not
  tidiness.** The writer's default is a small model at low reasoning
  effort, chosen because wording a finished case is formatting. Reading
  means finding one cell among forty tables in a document that may be in
  German. A reader inheriting the writer's default would have been
  quietly downgraded by a decision taken about something else, so it
  names its own provider, model and timeout (`MOVRVEST_READER_*`). No
  feature flag: reading is how this platform knows anything structural,
  and an unconfigured reader already has an honest answer — the reason is
  worded and travels to the surface as `absent_because`.

  **Two live-money hazards were caught, both of them passing tests.** A
  test that asserts "no credentials, so it did not run" does not go red
  when its silencing misses a source — it builds a real client, calls a
  real model and passes. Moving credential reading into a shared
  `narrative_providers` broke two writer tests' patch target that way;
  then the reader becoming a default turned a signal test that had never
  touched the network into one that read a 10-K, taking the suite from
  2.2s to 72s. `tests/conftest.py` now names every module that can reach
  a credential and every variable that can turn a seam on. Adding one
  means adding it there; the cost of forgetting is invisible.

  A third, smaller: narrowing on `isinstance(..., CompanyKnowledgeExtractor)`
  rejected every test double that answers the same way, which is the
  point of the seam. A supplied reader is taken at its word.

  Verified cold and warm, both providers:

  | | cold | warm |
  |---|---|---|
  | `DIS` via EDGAR | 22s, read and stored | 1.4s, `available_cached` |
  | `VOW3.DE` via Investor Relations | 43s, read and stored | 1.9s, `available_cached` |

  The tracked `DIS` entry was schema version 2, holding a bare
  `revenue_share: 0.449732` and no evidence for it. It was **re-read, not
  back-filled** — there was nothing to check that number against, which is
  exactly what the reading version changed. Both entries are now version 4
  and carry the cell addresses behind every size.

  `movrvest knowledge SYMBOL` shows that evidence. Developer-level and
  deliberately so: it presents and decides nothing, and the investor-facing
  question of what these facts add up to belongs to a rule and a page that
  do not exist yet.

- **A quantity carries the relationship it was read from** (August 2026).
  The third validation boundary, and the same lesson as identity one level
  down. Grounding proves cited words exist in a document. It cannot prove
  those words *support the number attached to them* — and reading
  Volkswagen's segment table, the extraction cited a **column header** for
  two of three segments. The shares were right. The citations
  demonstrated nothing at all.

  The distinction is worth keeping in these words: **evidence existence**
  was handled, **evidence applicability** was not.

  Prompting cannot close it, and the wording had already been tried: the
  extraction was told not to read across a table cell, in a document whose
  cell boundaries had been stripped out before it ever saw them. A rule
  nothing can check is a wish. So the evidence changed shape.

  **The document keeps its tables.** `SourceDocument` carries
  `performance_tables` beside the prose, parsed from the same markup by
  `app/providers/document_text.py`. The prose reduction is byte-for-byte
  the one the platform always used — the sections are located by searching
  it, and a different reduction would silently locate different sections.

  **A citation is an address, not a span.** The reading names a table, a
  row and a column, and states what it believes is printed there. This
  platform reads that cell itself and compares. A header prints no number,
  so citing one is refused structurally — before anyone has to notice that
  the number beside it happened to be right.

  **A share is arithmetic this platform performs.** A revenue share is not
  a fact a filing states; it is one printed figure over another. Both are
  cited, both are checked, and `MeasuredShare` divides. `BusinessSegment`
  has no field for a bare share — a size exists only as the two figures it
  came from, which makes an unevidenced share unrepresentable rather than
  discouraged.

  **Assuming one table layout was a bug, caught by running it.** The first
  design required both figures to share a *column* — right for Disney's
  10-K, where segments run down the page, and wrong for Volkswagen's IFRS
  segment note, where they run across the top and the shared coordinate is
  the row. It would have left every European filing permanently
  unmeasurable, and the failure would have looked like honest absence. The
  rule is now: one table, agreeing on exactly one coordinate. The shared
  coordinate makes the two comparable; the other names the part and the
  whole.

  Two further alignment defects only a live document exposes. Filings pad
  tables with wide empty cells, so `colspan` has to be honoured or the
  same column sits at a different index on every row; and a filer typesets
  `$ 42,466` as two cells and `17,672` as one on alternating rows of one
  table, so a lone currency symbol is read as the front of the figure
  beside it rather than as a value.

  Verified live on both: Disney 45/19/38% under `"2025"`, Volkswagen
  76/13/19% on `"Umsatzerlöse"` — each naming the exact cells. Both sum
  above 100%, and correctly: consolidated revenue is the segments less
  what they sold each other, 102% for Disney and 108.5% for Volkswagen.
  How far above depends on intersegment trade, which no constant predicts,
  so the sum ceiling is now a backstop rather than the guard. What catches
  a misread figure is the cell it was read from.

  Knowledge schema version 4. Nothing stores the share itself — storing an
  answer beside its inputs creates a second place for it to be true.

- **A company with no register is read from its own report** (August
  2026). The first primary source no regulator received, and therefore
  the first where the platform could delegate nothing. `VOW3.DE` — a
  security this platform recommends and could describe nothing about —
  now reads as Pkw und leichte Nutzfahrzeuge, Nutzfahrzeuge and
  Finanzdienstleistungen. It read their sizes as 68%, 13% and 18% —
  figures since re-measured, because nothing stored with them said what
  total they were shares *of*. See the applicability slice below.

  The trust model came before the code, and it is three separate
  questions rather than one: what document is this, who published it, and
  does that issuer correspond to the security. EDGAR delegates all three
  to the SEC and ESEF delegates them to the European index and GLEIF. An
  Investor Relations document delegates none, so each is answered
  explicitly — a reviewed location and the hash it was reviewed against;
  the document's own LEI; and the same GLEIF boundary the ESEF provider
  already uses.

  `PrimarySource` gained `authority` and `verification` alongside its
  existing provenance. Authority describes the source and is deliberately
  not ranked — no number, no ordering — because what actually differs
  between a filed and a published document is written down rather than
  scored. Verification records which identity checks succeeded, and it is
  what stops authority being read as a ranking: EDGAR is
  `REGULATOR_FILED` and offers exactly one check, because a 10-K declares
  no LEI and so never independently says whose it is. Volkswagen's
  package, obtained from Volkswagen, is `ISSUER_PUBLISHED` and carries
  four. Both statements are true and neither survives being flattened.

  **A document that cannot identify its own issuer does not become
  company knowledge.** That is the hard line, and it cost real coverage
  immediately: Volkswagen's ESEF package holds three documents and only
  one is tagged, so the platform reads its segment note and *not* the
  thirteen-megabyte management report where the narrative account of the
  business lives. An issuer publishing only a PDF stays honestly
  unavailable. Coverage may grow later; trust does not contract to speed
  it up.

  The reviewed location is the platform's second curated trust boundary,
  and it carries the hash of the reviewed bytes. That makes `resolve`
  cost nothing but an identity lookup, makes the key honestly the bytes
  themselves, and turns "the document changed underneath us" from
  undetectable into an explicit refusal — including when the replacement
  is a perfectly genuine newer report, because nobody reviewed that one
  either.

- **A European company is read from the report it filed at home** (August
  2026). The seam was built for this and it held: `EsefProvider` is an
  adapter, and nothing downstream of it changed. Europe has no EDGAR —
  every EEA issuer files its annual financial report as Inline XBRL with
  its own national mechanism under ESEF, and XBRL International indexes
  those filings at filings.xbrl.org by the filer's LEI.

  Two things are genuinely different from EDGAR, and both are in the
  adapter.

  **Identity has to be established before anything can be asked for.**
  Europe indexes by LEI, not by ticker, and a ticker is not an identity:
  `SAN` is Sanofi in Paris and Banco Santander in Madrid. The chain is
  symbol → ISIN → LEI → filing, and only the first link is written down,
  because only the first link has no authority to ask. Deriving it was
  tried and is exactly the failure the architecture warns about:
  `yfinance` answers `ASML.AS` with `AR0725224551`, an Argentine CEDEAR
  that tracks ASML rather than ASML, and answers `BNP.PA` with nothing.
  A wrong ISIN resolves to a real company filing real reports, and the
  knowledge read from them is grounded, cited and about the wrong
  business. So `european_issuers.py` is a reviewed list of 43 issuers
  whose ISINs were each checked against GLEIF, the legal name GLEIF
  returned is recorded and re-checked on every lookup, and a symbol that
  is not on it is reported as one this platform has not identified. The
  boundary is held again at the last moment it can be: an ESEF filing
  carries its filer's LEI in its own contexts, and a document that
  identifies itself as somebody else is refused unread.

  **The document says which passage is which.** A 10-K is sectioned by
  convention and has to be found by looking for "Item 1"; an ESEF filing
  is *tagged*, and a national regulator validated the tagging. The two
  passages are therefore asked for by name from the IFRS taxonomy —
  `DescriptionOfNatureOfEntitysOperationsAndPrincipalActivities`,
  `DisclosureOfEntitysReportableSegmentsExplanatory`,
  `DisclosureOfOperatingSegmentsExplanatory` — which means the reading
  does not depend on the language the report was written in. That
  matters: heading anchors were tried against ASML's report and matched
  its running page header on every page.

  Live: BNP Paribas' 2025 registration document reads as CIB 37%, CPBS
  52%, IPS 14% and Other Activities unstated, every span verbatim;
  ASML's reads as one reportable segment, which is what ASML reports.

  Selecting *which* filing is the annual report is where the index needed
  care, and both rules came from the index rather than from imagination.
  A period that has not ended cannot have been reported on — the register
  carries a Hermès filing stated as ending December 2026 whose document
  is the report for 2025. And an interim report is not an annual one:
  Novo Nordisk files ESEF quarterly, so the oldest filing on record
  establishes where the financial year ends and the annual reports are
  the ones landing on that anniversary, within a tolerance wide enough
  for Ahold Delhaize's 52-week calendar.

  Coverage is stated rather than implied. `filings.xbrl.org` does not
  carry Germany: every German issuer resolves to a real company and to no
  filing, which is reported as a gap in what the index reaches rather
  than as a company without an annual report. `VOW3.DE`, one of the two
  securities the platform currently recommends, is exactly that case.
  `NOVO-B.CO`, the other, is read.

- **Knowledge acquisition wired into the pipeline, cache-first** (August
  2026). `CompanyResearchService` now asks `CompanyKnowledgeService` for
  a company's own account of itself, and nothing in the research pipeline
  reaches a regulator or a model directly. The policy is cache-first and
  on demand: resolve the current document, return stored knowledge if its
  key is known, otherwise acquire, validate and store. Knowledge refreshes
  only when the authoritative document changes. Live: Disney cold 48.0s,
  warm 0.6s.

  `reporting_period` is populated from the filing index and kept apart
  from the publication date — Disney's latest 10-K was published
  2025-11-13 for a period ended 2025-09-27, and comparing the wrong one
  would compare documents rather than business periods.

  Acquisition state is explicit: `available_cached`, `available_acquired`,
  `unavailable`, `provider_error`, `invalid_extraction`. A gap in coverage
  and an outage are different answers and only one is worth retrying,
  which `may_succeed_later` says outright.

  Two bugs the live run found. `BTC` resolves against the SEC to a trust
  issuing shares that track Bitcoin — a real business filing a real
  report — so a token was about to be described by a fund's segments;
  knowledge is now asked for only where the playbook expects company
  accounts. And extraction was not repeatable: one attempt in three
  survived grounding, the rest paraphrasing across a table boundary. The
  contract was not relaxed. Quotes are now asked for short — five to
  fifteen words from one run of prose — and a rejected reading is asked
  again up to three times under the identical rule. Three of three now
  pass with identical figures.

  The store gained a schema version. A source is immutable; the reading
  of it is not, so an entry written before the extraction captured
  reporting periods is treated as absent and read again rather than
  upgraded in place — filling in what a reading never captured would be
  inventing it.

- **A Company Knowledge layer, behind a primary-source seam** (August
  2026). Structural facts about a business — its segments, what each
  sells, how large each is — read from the document the company is
  legally answerable for, and kept.

  Two stores, deliberately. Evidence is dynamic and expires: a price at
  fifteen minutes, fundamentals at a day. Knowledge is structural and
  changes when the company changes, so it is keyed by the document's
  immutable identity and never expires at all. Reading Disney's 10-K
  costs 44 seconds and two model calls once; every cycle after that is
  half a second and no model call.

  The LLM reads and never decides. Every segment carries a verbatim span
  and the span is checked against the document — an extraction quoting
  words that are not there is discarded in full, not in part. Revenue
  shares are read from the performance discussion, never apportioned: a
  set summing past tolerance is refused rather than rescaled. Disney's
  10-K filed 2025-11-13 yields Entertainment 45.0%, Experiences 38.3%,
  Sports 18.7% — the revenue mix an industry code cannot express, from
  the filing rather than from assumption.

  Acquisition sits behind `PrimarySourceProvider`, with EDGAR as the
  first adapter. The canonical `PrimarySource` carries identity, type,
  identifier, publication date, reporting period, format, language,
  location and the immutable key that makes knowledge permanent — so
  extraction, storage and reuse are identical whether a document came
  from a regulator, an ESEF filing or a company's own report. European
  coverage becomes another adapter rather than a rewrite. Where no
  provider can resolve a source, every provider's reason is carried:
  "not listed" and "could not be reached" call for opposite responses.

  No archetype is decided anywhere in this work. These are facts; the
  deterministic rules that read them come next.

- **A security is read with a playbook, and the dossier says which**
  (August 2026). The pipeline already had the shape — profile → strategy
  → plan → analysts — and it did nothing: `CompanyProfiler` returned
  `business_model=STANDARD_CORPORATE, lifecycle=MATURE` as literal
  constants for every company, the factory raised for anything else, and
  `CompanyResearch` had four named fields so a security read any other
  way could not be represented. Every security was analysed identically
  whatever its kind.

  `InvestmentPlaybook` is now the explanation and the instruction both:
  the dossier shows the framework, its priorities and its coverage, and
  the `ResearchPlan` the executor runs is built from the same object, so
  what the investor is told and what the analysts were asked cannot
  drift. Coverage lists every analysis, including the declined ones with
  their reason — a question this platform chose not to ask and one that
  failed to read mean opposite things about a case. Bitcoin's absent
  valuation is now the Digital Asset playbook saying a token publishes no
  financial statements, rather than an unexplained gap.

  The classification is structural only: asset class and the industry the
  provider reports. Live, that settles Digital Asset, Fund, Software,
  Platform, Aerospace & Defence and Asset Manager — and leaves four of
  eight stocks on the general default, with the book's one bank reporting
  no industry at all and stated as not classified rather than defaulted
  silently. What kind of *business* this is beyond its industry is the
  next question, and it needs evidence this platform does not yet read.

- **A conviction that moves says how far, and what moved under it**
  (August 2026). The dashboard was static: a case's conviction was a
  number with no yesterday. Each row now carries the move — **↑1**, **↓2**
  — as arithmetic on two recorded convictions, and opening it names the
  scores that differed: *"Business quality improved, 62 → 80"*,
  *"Safety fell, 55 → 35"*. Every reason is a score that measurably
  changed between the two decisions; a score missing on either side is
  passed over rather than guessed at.

  This needed the journal to record what a decision was decided on, not
  only what was decided — so it now stores the five scores beside each
  decision. Decisions recorded before that cannot be explained, and the
  platform says exactly that rather than showing an empty list as
  "nothing changed": *"The earlier decision was recorded before this
  platform kept its scores, so what moved underneath cannot be said."*
  Live, every case reads that today; the reasons fill in from the next
  cycle in which a conviction moves.

- **The holdings became a ranking rather than ten reports** (August 2026).
  Ten cards repeated the same five sections — risk, why now, risks,
  previously, review case — so finding the one that mattered meant reading
  ten of everything. The Executive Committee is now one compact list: rank,
  symbol, which way the case is moving, what to consider doing, the
  decision state and the conviction. A row opens onto the full case, which
  is unchanged. Nothing was removed; it stopped being shown all at once.
  The expansion also stopped printing the CIO's rationale twice — the
  action's reason is shown only where it says something the summary does
  not, which for a case short of evidence is the missing figure itself.

- **Every case says what to consider, and which way it is moving**
  (August 2026). Each card's action read "Monitor" — including the ones
  the Artificial CIO had moved to RECOMMEND — because it was derived from
  nothing. It cannot be the decision state renamed either: RECOMMEND on a
  security already held and RECOMMEND on one the investor does not own
  are the same judgement and different questions, and only the portfolio
  knows which case this is. `ExecutiveAction` now carries the
  consideration ("Consider opening a position in VOW3.DE", "Continue
  holding BNP.PA", "Research ETOR before the thesis can progress",
  "Review whether to keep holding SPCX"), the CIO's own reason for it,
  and the next dated thing bearing on it. Nothing is worded as an
  instruction and no size, price or quantity is ever named: this platform
  recommends and the investor decides.

  "PREPARE was also the previous decision, recorded on August 4" asked
  the reader to do the comparison. `DecisionTrend` does it once, off the
  lifecycle ranks the states already carry: **Stable — 4 consecutive
  reviews since 2026-08-03**, **Improving — PREPARE → RECOMMEND**,
  **Deteriorating — RECOMMEND → INVESTIGATE**. A first review has no
  trend at all, because a run of one is not a settled view.

- **The dashboard opens with today, not with what you own** (August 2026).
  A Chief Investment Officer does not open a dashboard to ask what they
  hold; they ask what changed and what deserves attention. The page now
  leads with a `TodayBriefing`: the highest-priority change as the
  headline, over counted lines — "6 recommendations changed", "1 company
  reports earnings today: DIS". Every line is a count of something the
  cycle recorded, checkable against the feed beneath it, and composed in
  the backend. Holdings are counted rather than changes, because the feed
  really does hold three moves on one security in a week and counting
  those would overstate how much of the book moved. Earnings are read
  from the schedules the cycle already gathered per security, so the
  dashboard and the dossiers cannot disagree about when a company
  reports. A quiet day says so and shows no headline at all: a page that
  manufactures a highest priority every morning teaches its reader that a
  highest priority means nothing. Nothing is claimed about executed
  trades — the platform recommends and keeps no record of what the
  investor did, so it does not report on it. The portfolio's own
  statistics moved below the fold as supporting information.

- **Each investment case shows its own security's safety** (August 2026).
  Every card on the dashboard printed the *account's* risk level under a
  security's name, labelled "Risk". The account has one risk level, so
  ten cards read "Low" together — including BTC at 35.9% volatility and a
  53.1% fall, ETH at 54.4% and 67.6%, SOL at 58.0% and 74.9%. The risk
  engine was never wrong about them; every dossier stated it correctly.
  The card now carries the security's own safety, and the ten read 55,
  55, 35, 55, 35, 35, 35, 35, 35, 15. This was the fourth and last
  instance on this surface of one defect: an account-level figure printed
  as though it described a security.

- **Every score runs the same way, and says what kind of number it is**
  (August 2026). Risk was the one dimension where a high number was bad,
  which made the set unreadable and unsafe to aggregate: four nineties do
  not average to anything if one of them means the opposite of the other
  three. The Artificial CIO already knew this — it inverted risk before
  averaging into conviction — but inline, so the concept had no name and
  every surface went on showing the raw figure. It is now
  `DecisionEvidence.safety_score`, used by that same arithmetic and shown
  everywhere: **Safety**, higher is safer, with the inversion stated in
  the score's own basis. `None` stays `None` — an unmeasured risk is never
  reported as a safe security. The gates still read `risk_score`: a
  ceiling on risk is the natural way to write "too dangerous", and
  restating one policy in two directions would be the duplication this
  platform avoids. "Valuation" is now "Valuation attractiveness" and
  "Evidence" is "Evidence strength". Each score also declares its kind —
  measured from data, derived from your policy, or assessed against this
  platform's bands — because at two significant figures an interpretation
  is indistinguishable from a measurement, and borrows its authority.
  Portfolio fit is the one policy-derived score; the measurements are the
  evidence listed beneath each one.

- **A fact about one asset class reaches only cases about that class**
  (August 2026). The single sentiment index this platform reads is
  crypto's, and it was listed among the facts the Investment Committee
  weighed about a software company — correctly captioned "which describes
  crypto only", and entirely irrelevant. A caption cannot be filtered on,
  so `Evidence` now names its `subject` as data: no subject means the fact
  describes the conditions every security faces, and a named subject
  reaches only a case about that class. A security whose class nobody
  established keeps the unsubjected evidence only, rather than being
  assumed into the class that happens to fit. `Brain.asset_class_for()`
  is now the one place that answers what kind of asset a symbol is.
  Verified live: MSFT's committee no longer sees the Fear & Greed index;
  BTC's still does.

- **Every score on the dossier opens onto its own reasoning** (August
  2026). "Business quality 80 / 100" was the most measurement-looking
  figure on the page and the least measured: HIGH quality, priced by a
  band this platform chose and never showed. Each of the five scores now
  expands to the sentence that produced it — the reading, and the whole
  scale it was priced against ("HIGH at 80, MEDIUM at 62 and LOW at 40")
  — over the findings the reading rests on. Risk states that a higher
  number is worse and reads its bands off `RiskSignal`'s own severities,
  so the scale shown cannot drift from the scale scored on. Portfolio fit
  lists every term including the ones the policy could not answer, and
  says how many of how many it averaged. A score nobody measured says
  which measurement was missing instead of reading as zero. Written where
  each score is computed (`DecisionEvidenceBuilder`, `PortfolioFit`),
  carried on `DecisionEvidence.score_bases`, and only disclosed by the
  page — the dashboard still presents and never calculates.

- **A security's catalyst is its own next earnings date** (August 2026).
  The investment case's catalysts were the market's opportunities, which
  are identical under every symbol — "Stable market conditions" was
  MSFT's reason to act, and everything else's. The company's published
  report window now reaches the case the way risk and market sensitivity
  do: read by `CompanyFactsService` from the same daily cache the book's
  calendar uses, carried on `CompanyFacts` and `CompanySignals`, and
  worded once by `EarningsWindow.stated()`. A holding's catalyst reads
  "Reports earnings in 84 days (Oct 28)" — dated, per security, and
  absent when no date is published. Proven live on MSFT. The wording is
  scheduling and nothing else: nothing anywhere says what the report will
  contain. A company between reports says so among its findings, a
  calendar that could not be read is reported as missing evidence, and
  the two are never merged. The account and market opportunities are
  still weighed — as the context they always were. The Executive Writer
  receives the catalyst as its own finding, sourced "a dated event, not a
  view on its outcome", so "why now" rests on a date rather than on the
  market's mood.

- **Held-but-unwatched instruments resolve from the broker's catalog**
  (August 2026). A position on no watchlist used to be a `#id`
  placeholder and a "cannot classify" line. The resolver now asks
  eToro's own instruments endpoint — the same source the position
  comes from — to describe the ids the watchlists miss, once per
  cycle. Proven live: instrument 1238 (`#1238`, 0.2% unclassifiable)
  is BNP.PA, a stock, now named, classified and fully evaluated by the
  CIO on its own record. An id the catalog cannot describe keeps the
  placeholder and the worded absence.

- **The Executive Writer speaks through a provider seam** (August 2026).
  The model call sits behind `NarrativeProvider`: the writer builds the
  prompts and one shared JSON schema, a provider carries them over its
  own wire, and every draft — whoever wrote it — passes through the one
  validator. Anthropic is the seam's first implementation (the wire call
  moved verbatim); OpenAI is the second, holding the identical schema
  through strict structured outputs. The configured default is OpenAI's
  `gpt-5-nano` at low reasoning effort — wording a finished case is
  formatting, not deep reasoning, and default effort measurably starved
  the draft budget to an empty draft. `MOVRVEST_WRITER_PROVIDER` and
  `MOVRVEST_WRITER_MODEL` switch provider and model; keys are read from
  the environment first and the same `.env` the broker keys live in
  second. `movrvest writer-compare SYMBOL` runs the identical dossier
  through every provider and reports measured latency, reported tokens
  and cost at stated prices beside each narrative — language quality is
  deliberately not scored; judging it is the reader's. First live
  generation verified on MSFT: a fully grounded five-section narrative,
  every citation resolving, in 13.1s for $0.0006 at stated prices. The
  dossier page needed no change to render the new providers' narratives
  — the API contract is unchanged, and the writing model was already
  stated in the narrative's provenance line — but it silently dropped
  the worded absence when there was no narrative; it now presents the
  backend's own sentence (flag off, missing credentials, discarded
  draft) instead of rendering nothing.

- **The Communication layer gained an Executive Writer** (August 2026).
  An LLM language specialist — never a decision maker — that words the
  finished investment case as an investment-committee narrative. It
  receives only canonical objects (`ExecutiveDecision`,
  `InvestmentThesis`, `DecisionEvidence`, `CommitteeOpinion`), rendered
  as numbered findings; every paragraph it returns must cite the
  findings it rests on, citations to findings that do not exist are
  rejected, and a draft that changes the recommendation is discarded —
  the echo is validated against the `ExecutiveDecision`. Off by default
  behind `MOVRVEST_EXECUTIVE_WRITER`; every failure path (flag off, no
  credentials, model declined, ungrounded or empty draft) is a worded
  absence on the dossier, never a fabricated narrative. The
  deterministic renderers remain canonical. Reasoning stays
  deterministic; only the language is generated.

- **The UX/UI Alignment mission is complete** (PRs #8–#15, August 2026).
  The web product now matches the mission's model end to end: Overview,
  Portfolio, Research, Markets, Track Record and Investor Policy in
  primary nav; the five-question Dossier behind every "review case" CTA;
  one shared `DecisionCard`. The frontend no longer calculates investment
  meaning anywhere — capacity, risk bands, labels, weights, typical-day
  moves and verdicts all arrive worded or measured from the backend — and
  every absence is stated with its reason: unevidenced and unbudgeted
  research candidates are named, unmeasured risk components refuse to be
  zeros, and `/track-record` reports 99 recorded decisions with zero old
  enough to measure rather than inventing a hit rate. The audit that
  preceded this and the slice-by-slice log live in
  `docs/frontend/UX_UI_INVENTORY.md`

- **The CIO can be scored against its own decisions.** `movrvest record`
  joins the decision journal to a year of daily closes and reports what
  each security did after the call. Today it reads 61 decisions and 0
  outcomes, because every one of them is a day or two old and a decision
  must stand 30 days before its price move says anything — a record that
  measured yesterday's noise would report judgement it has not
  demonstrated. Verified end to end by moving the clock forward against
  live prices: 58 of 61 priced, `BTC` resolved through `BTC-USD`,
  `UMI.BR` through the Brussels listing, and `#1238` and `ZZZZ` reported
  unpriceable rather than skipped. MONITOR and INVESTIGATE are never
  scored as calls — they are the platform saying it does not know yet —
  and a security that has barely moved is evidence for nobody, which the
  live run caught: a flat holding was being marked against its own call

- **The market does not gate a decision, and this is the decision not to
  make it one.** `DecisionEvidence` carries no market score. The question
  was examined properly rather than answered by adding a field: the two
  scores that describe the market — momentum and volatility — never reach
  the Artificial CIO at all, and the one market input that does,
  `MarketAssessment.confidence`, carries no information about what the
  market did. It is `1 − | |momentum − 0.5| × 2 − volatility |`, which is
  exactly 1 whenever the instruments move together, so a flat market and a
  market where every instrument fell 8% both read 0.940. It is
  nevertheless one third of the cognitive average inside `evidence_score`,
  which is gated at 30, 60 and 75 — so the market already moves a gate, by
  a route nobody chose, in proportion to how uniformly the instruments
  moved. A market score would also be identical for every symbol, which is
  the exact shape this branch removed from portfolio fit, from quality and
  from risk; what would make it per-security — this security's exposure to
  the corner of the market that moved — is not measured at all. And no
  decision has yet been scored against its outcome, so no threshold could
  be calibrated rather than asserted. The reasoning, the figures behind it
  and the four things that must exist first are in
  [`architecture/MIGRATION_PLAN.md`](architecture/MIGRATION_PLAN.md). The
  code is unchanged. Figures computed from the repository's own code, not
  observed against a live account

- **The market has a past.** Quotes were fetched, cached for fifteen
  minutes and discarded, so nothing in the repository ever held two market
  readings at once and no question about the market beginning "since"
  could be answered at all. The change feed could only report decisions,
  because decisions were the only thing anything wrote down.
  `MarketSnapshotArchive` records each observation through the same
  `VersionedSnapshotStore` the eToro responses go to — the store was
  write-only and now reads back, rather than a second archive being
  invented to hold the same kind of evidence twice. **Facts are stored and
  the classification is not:** mood, volatility band and summary are
  derived from the quotes and the VIX, so they are recomputed on the way
  out by the one service that classifies markets anywhere, and a threshold
  that changes does not leave stale conclusions behind it. A quote replayed
  from the cache carries the time its price was actually taken, so a
  snapshot identical to the last recorded one is not recorded again: a
  replay is not an observation. `GET /market/` now builds its snapshot
  through `MarketPerception` rather than assembling a second one from the
  same three collaborators. Not verified against live data — this was
  built and tested in a sandbox with no credentials and no network

- **A sentiment reading now says what it is a reading of.** The only index
  the platform reads is Alternative.me's crypto Fear & Greed, and it was
  being blended with the mood of nine instruments into one outlook: a
  negative market plus crypto fear read BEARISH at 95% confidence,
  summarised "weak market conditions are confirmed by crypto fear".
  Crypto fear cannot confirm an equity sell-off, and the agreement it
  could not give was raising the confidence of the regime that weights
  the committees. `SentimentSnapshot` carries its `subject` and its
  `Provenance`; the outlook rests on market conditions alone at a stated
  50%, and the reading is reported beside it, named for the asset class
  it describes. Live today: crypto reads 28, Fear, while the market mood
  is neutral

- Sentiment reached the canonical pipeline. It lived only on the legacy
  committee path and the `intelligence` command, so the Brain could not
  see it at all and the one asset class it does describe was judged
  without it. `MarketPerception` reads it, `MarketSnapshot` carries it,
  and the `MarketAnalyst` states it as evidence naming its subject —
  never folded into momentum or volatility, which describe nine
  instruments rather than one asset class

- The second market stack is gone. `MarketResearchService`,
  `MarketBreadthAnalyst`, `EquityTrendAnalyst`, `TrendAnalyst`,
  `MarketFacts`, `MarketFactsService`, `RiskAssessmentService` and the
  fabricating `MarketContextService` — 14 modules and their tests, every
  one reachable only from the others. It was a parallel representation of
  a market the canonical `MarketSnapshot` already describes, and the
  repository has been here before: four committee implementations, with
  the docs calling a dead one canonical

- **`/markets` reports what the market mood hides.** The Brain's whole
  market view was the average move of nine instruments, and an average
  nets a rally against a sell-off and reports neither. On the first live
  call it read "Markets are broadly neutral today" while equities were up
  1.5–1.8% and oil had fallen 5.1%. The page now classifies every corner
  the platform prices — equities, technology, small caps, crypto,
  commodities, the dollar, rates and volatility — and a group nothing
  could price reads "Not priced" rather than flat. `MarketBreadthService`
  was written, tested and imported by nothing; it now reads the canonical
  `MarketSnapshot` instead of a second market representation

- The market snapshot keeps the VIX figure and knows when it was
  observed. The number was fetched, classified into an adjective and
  dropped, and the snapshot's only timestamp was the moment it was
  assembled — not when anything in it was seen

- **Overall portfolio risk is a measurement.** Market risk was the last of
  the four components still absent, and it is read off evidence the Brain
  already held: every benchmark quote carries a year of realised
  volatility, and every holding is classified, so the blend follows what
  this account actually holds. It reads **0.8% annualised** — 97.4% cash,
  which does not move with the market, 1.3% equities at 17.1% and 1.2%
  crypto at 45.4%. Overall risk is 0.20, LOW, and the only real risk this
  account carries is the fall it already took. An account in cash is
  exposed to no market, which is a measurement rather than a rule, and
  0.2% of it has no benchmark and is excluded rather than counted calm

- The portfolio page stopped inventing its own risk. `ExecutivePortfolio-
  Assessment` derived four scores in the browser from the cash percentage
  with hardcoded ladders, "Portfolio risk" among them — an inverted cash
  ladder presented beside the real figures. It now presents the four
  measured components and says "Not measured" where one is absent, which
  is what the dashboard rule has always required

- Portfolio drawdown is measured. The account fell **15.8%** from its peak
  on 10 May 2026 to its low on 25 June 2026 and is still 7.7% below that
  peak — read off 365 daily balances, not inferred from the holdings.
  Two of the risk score's four components were hardcoded 0.50s; this was
  one of them. The fall is scored against the 20% the investor stated they
  could sit through, a figure the strategy form has always collected and
  nothing had ever read, which puts the account at 0.79 of its own
  mandate. The window is stated everywhere the number is, because 15.8%
  over a year and 15.8% over a month are different statements. Market risk
  is still unmeasured, so overall risk stays absent

- The balance history reaches back a year, not a month. The first live
  call asked for one month and got 33 snapshots; asking for 365 days
  returns 365. What the archive holds is what was requested, which is
  exactly why the request window is recorded alongside the response

- The account has a past, not just a present. `EtoroHistoryBroker` reads
  closed trades, historical balance snapshots and cash transactions — the
  first figures in this repository from before today. Every decision until
  now rested on a snapshot of now, which is why no decision can yet be
  scored against its outcome. Pages are walked to a ceiling the caller
  sets, because the read budget is pooled and a loop that follows "next"
  until it runs out spends an allowance the rest of the platform needs

- The platform knows what its own key can do. `movrvest credentials`
  reads `GET /api/v1/me`: 26 scopes granted, 10 of them writes, including
  `etoro-public:trade.real:write`. Nothing in MOVRvest calls a
  state-changing route, but the permission exists and is now stated every
  time rather than assumed away. Capability is read off the `:write`
  suffix, not off a list of documented scope names — the published names
  differ from the live ones, and matching the list reported a key that can
  place real orders as read-only

- Every eToro request goes through one door, and every response is kept.
  `EtoroClient` owns the credentials, reads the published allowance off
  each response and waits for the window rather than spending into a 429.
  `/watchlists` was fetched and discarded — the only description the
  platform has of an instrument, never archived — and is now captured like
  `/pnl`. Query parameters are recorded, which the API inventory asked for
  and nothing did: a paginated capture that does not say which page it
  holds is a corrupted archive

- A source that did not answer says so. `CachedValueProvider` serves the
  last real reading when the provider fails — deliberate, and until now
  indistinguishable from a reading taken on schedule, so a Yahoo outage
  hid behind a plausible date. A degraded reading is marked and outranks
  mere age when a case reports what it rests on: "Yahoo Finance did not
  answer — last reading, 14 minutes ago"

- The investor can see how old the evidence is. Provenance travels from
  the facts through the signals, the recommendation and the decision to
  the brief and the research page, which now read "Yahoo Finance, 6
  minutes ago" under a case. It is the stalest reading behind that case,
  not the freshest, and a case with no security-level reading says so
  rather than looking freshly checked

- Evidence knows where it came from and when. `MarketQuote` carried no
  time at all, so a price replayed from a fifteen-minute cache was
  indistinguishable from a live one, and `CompanyFacts.observed_at` was
  the *fundamentals* date standing in for the whole object — one figure
  describing a third of it and dating the rest by implication. `Provenance`
  now travels with each reading, a cached quote keeps the time the price
  was actually taken, and evidence dates itself to its stalest part rather
  than its freshest. This is the foundation for stating and enforcing
  reliability rather than asserting it

- Crypto is assessed on what a token has. `CryptoQualitySignalService`
  measures network value, a day's turnover against it, how much of the
  eventual supply already exists, and how long the asset has traded — all
  four from the provider call the platform already made and was throwing
  away. BTC scores 80 on a $1,269bn network, 95.5% issued, 16 years
  traded; ADA scores 62 on $7bn and is rejected on its own 64.9%
  volatility. Crypto moved from a permanent INVESTIGATE to real, differing
  cases. None reached RECOMMEND: valuation stays absent, because there are
  no earnings to price against and inventing a metric was the alternative

- The crypto sentiment index is read from the service it cites.
  `CryptoFearGreedProvider` returned a hardcoded 72, labelled "Greed", and
  the renderer printed "Source: Alternative.me" beneath it. The service is
  real and the number was not: the published index that day read 28,
  "Fear". `movrvest intelligence` moved from NEUTRAL at 60% to BEARISH at
  95% once it read the real figure. The citation is now printed only
  beside a figure actually read from that source, with the date the source
  published it, and an unreachable index reports nothing rather than the
  last mood it saw

- Housekeeping. Three iCloud conflict copies were tracked despite the
  `.gitignore` rule that covers them; both event copies were strict
  subsets of their base, so nothing was lost. Two pre-refactor `.tsx`
  backups, and a dead cluster of seven modules — `OpportunityScoringService`
  with its hardcoded quality of 70 and valuation of 70, `PolicyAssessmentService`,
  `OpportunityFactsService` and their domain models — imported by nothing
  but their own tests. The decision journal is no longer tracked: it is
  written every cycle, its memory belongs to the machine that made those
  decisions, and tracking it is what put `data/events/` in the path of
  iCloud's conflict copies twice. The files stay on disk

- A question that does not apply is no longer reported as a measurement
  that has not arrived. "Business quality has not been measured" promised
  a later cycle would close the gap; for a cryptocurrency none ever will.
  BTC now reads "A cryptocurrency has no business quality or valuation to
  assess, and this platform judges an investment case on both", and its
  missing evidence says it has no earnings to be valued against rather
  than that valuation data is unavailable. The gates are unchanged and
  nothing became recommendable. An asset the platform could not classify
  is still told its data is pending, because "not known to have a company"
  is not "known to have none"

- The brief reports the decision's own conviction. It carried only how far
  the committees agreed, printed as "Conviction", so a RECOMMEND could
  show 32% while the Artificial CIO held the decision at 81. Both numbers
  are now stated under their own names, and they separate: UUUU draws 93%
  committee agreement — the committees are confident, and confident it is
  a sell — against 40% conviction, capped by the REJECT it reached.
  Conviction sits inside each case rather than in the header, because it
  is held in a decision about one security

- The Executive Committees review the security, not just the account. Both
  read only portfolio and market assessments, so their opinions were
  identical under every symbol: agreement could read 94% for a security
  neither had looked at. The Investment Committee now leads on the
  security's own committee verdict, and the Risk Committee speaks to the
  security's measured volatility and deepest fall rather than abstaining
  on an account risk nothing records. On live candidates they finally
  disagree with each other and with themselves across symbols — UUUU draws
  reduce and sell, VOW3.DE strong_buy and hold, and MBGL's risk stays an
  honest abstention because its price history is too short

- The account reports what it holds. Every invested euro used to sit in
  `unclassified` under a standing risk flag, because nothing joined the
  eToro asset type the watchlists already carried onto the holdings. The
  live account now reads 1.2% stocks, 1.2% crypto and 0.2% unclassified —
  a single holding no watchlist names, flagged with its exact size rather
  than a blanket disclaimer. The policy's crypto ceiling is enforceable
  for the first time, in policy alignment and in portfolio fit, and both
  decline to score it while any part of the account is unidentified

- An investment case states the security's own strengths and risks. Signal
  findings carry the sense the signal read them with, so "Negative
  earnings." is no longer indistinguishable from "Positive earnings." and
  a 94% volatility no longer reads the same as a 12% one. UUUU's case
  lists six risks and no strengths; VOW3.DE's lists four strengths. The
  portfolio and market sections are still there, under their own headings

- A committee that cannot measure something is silent, not opposed. The
  brief read "32%" beneath a RECOMMEND, and the reason was arithmetic
  rather than dissent: portfolio risk is unmeasurable, the Risk Committee
  correctly said so, and its 0.0 confidence was then averaged in as though
  a committee had objected. It reports no opinion now, and agreement reads
  94%. Confidence also stopped being the recommendation in disguise —
  both committees derived it from how bullish they were, so a bearish view
  was by construction a tentative one and a SELL could never be stated
  with conviction. It now comes from how well the assessments behind it
  were evidenced

- Asking about a security now looks at it. `movrvest evaluate SYMBOL` and
  `GET /executive/{symbol}` built a Brain with no research budget, so with
  an account holding nothing, per-security perception returned nothing and
  the Artificial CIO judged the security on portfolio and market context
  alone. `evaluate UUUU` answered INVESTIGATE while the research pipeline
  answered REJECT about the same ticker on the same day. Both now say
  REJECT, on 94% volatility, negative earnings and an analyst veto. A
  symbol no watchlist names still produces no evidence, and says so

- **The platform makes recommendations.** VOW3.DE and NOVO-B.CO are the
  first, and they were not unblocked by lowering a threshold. Portfolio fit
  measured neither the portfolio nor the fit: it was `mean(9 positions / 20,
  policy alignment 0.50)` — a constant 47 under every symbol, against a gate
  of 60. Both terms ran backwards. The account was marked down for holding
  nine positions rather than twenty, and again for sitting 97% in cash
  against a 5% target, and both marks were spent refusing the one action
  that would have corrected either. `PortfolioFit` now measures room:
  funding room from the cash target, concentration room from the
  single-position limit. It is per security, and it is absent rather than
  invented when the policy states no limit to measure against

- Nothing calls raw evidence a strength any more. `DecisionEvidence` and
  `ExecutiveDecision` carry `evidence_weighed`, and it holds only what was
  read about the security. The research page's list of a candidate now
  reads "Negative earnings", "Annualised volatility is 94.0%" and "Deepest
  fall was 61.3%" — findings that were previously the candidate's
  `key_strengths`. The account's own condition was mixed in there too and
  is gone: it was identical under every symbol. On the brief, the sections
  that do describe the portfolio and the market now say so, rather than
  printing "Healthy liquidity" under a ticker

- Crypto is evidenced. An eToro instrument is classified by `AssetClass`,
  and a crypto one is priced as a pair — `BTC` as `BTC-USD` — so six
  previously unpriceable assets now carry a real price and measured risk:
  58% annualised volatility and a 75% deepest fall on Solana against 32%
  and 34% on Microsoft. `BTC` moved from REJECT to INVESTIGATE on evidence
  rather than on a changed rule. It is also not asked for company
  fundamentals: Yahoo answers about a token with a `marketCap` of 1.26
  trillion, which read as company facts would have reported Bitcoin as a
  large-cap company

- Risk is measured, per security, from the price history a quote request
  already carries. One parameter took that request from five days to a
  year, and annualised volatility and deepest observed fall now separate
  the candidates: 94% volatility on Energy Fuels against 18% on
  McDonald's, where every candidate previously scored the same 25

- Absent evidence is absent everywhere in the decision path. An unknown
  company quality no longer becomes the portfolio's health score, an
  unknown valuation no longer becomes market momentum, and risk no longer
  contains two hardcoded 0.50 constants that made up most of it. Scores
  that were not measured are None, are excluded from conviction, and
  cannot clear the gate they belong to

- Evidence is cached and deterministic. Fundamentals are read once a day,
  quotes for 15 minutes, and a symbol the provider cannot price is
  remembered as unpriceable for 30 rather than retried every cycle. A
  research cycle went from 50 provider calls to 0 on a warm cache, and
  two runs on the same day now produce the same decisions
- Company facts stopped discarding market cap and earnings, which the same
  provider call already returned. The quality signal could not score above
  LOW before; real quality now separates the candidates

- The opportunity pipeline is real. `OpportunityPerception` reads the
  investor's watchlists, `SecurityPerception` evidences a capped number of
  the candidates, and the Artificial CIO judges each one on that evidence.
  The three fabricated services behind the old page — `OpportunityService`,
  `OpportunityDiscoveryService` and the hardcoded candidate array — are gone

- The Artificial CIO remembers its own decisions. `DecisionJournal` records
  each one, `MemoryPerception` reads them back into the Brain, and the
  investment case states what was decided before — or says nothing at all
  when the holding has never been judged
- Communication wired in; the hardcoded "No urgent decision today" is gone
- The dashboard's silent mock fallback is fixed, and its last mock removed
- Holdings are perceived per security, so the CIO judges each on its own
  evidence rather than repeating one portfolio-level verdict
- `policy_alignment_score` is measured against the Investment Policy rather
  than hardcoded to 0.80
- The legacy `BrainPipeline` chain and 45 superseded files are deleted

---

# Known Gaps

Named rather than hidden. None of these are estimated away in the product.

## Evidence quality

- eToro identity carries no reading. The watchlist fetch records no time,
  and inventing one would be the fabrication this model exists to prevent
- `TAO` and `HYPE` have no plain `-USD` listing on Yahoo. Both are reported
  unpriceable rather than guessed at under a disambiguated ticker
- A holding absent from every watchlist cannot be named or analysed
- Research covers a capped number of candidates per cycle, because
  fundamentals are uncached and the provider rate-limits. The page reports
  how many it could not reach
- A crypto case stops at PREPARE. Its quality is now measured, and its
  worth cannot be: a token has no earnings to be priced against, which the
  CIO states as this platform's limit rather than as a pending measurement

## Reasoning

- Every gate now clears on measured evidence, and RECOMMEND is reached.
  Valuation is what holds most candidates at PREPARE, which is the gate
  doing its job. Fit reads 99 for all of them — honestly, on an account
  that is 97% cash with no position above 0.5% — so nothing on live data
  yet demonstrates it separating one security from another
- Sector rotation and market events are still unmeasured. `/markets` says
  so rather than illustrating them
- The market gates nothing, deliberately. It reaches the Artificial CIO
  only through `MarketAssessment.confidence`, one third of the cognitive
  average inside `evidence_score` — and that term measures how uniformly
  the instruments moved, not what the market did. Making it mean evidence
  quality, or removing it from the score, is the first fix and it changes
  live decisions
- A security's exposure to the market is measured. `MarketSensitivity`
  computes beta and correlation against a benchmark from the same price
  history the volatility is read off, and it reaches decisions as
  per-security evidence. The market still gates nothing — deliberately,
  and `/markets` now states that on the page
- No sentiment index is read for equities. The crypto reading is the only
  one, it is labelled as such everywhere it appears, and the gap is stated
  rather than filled by the index that happens to exist
- An individual instrument's move is not reported as a change. Every
  instrument moves between any two readings, so reporting one means
  deciding which moves matter, and nothing here measures that. A threshold
  chosen to look sensible would be an invented figure on an investment
  surface. The quotes are recorded, so the measure can be built on
  evidence later. The same holds for a VIX that moved without leaving its
  band
- Cash transactions are wired but uncalled: the endpoint wants a cash
  account id, and the CID from `/api/v1/me` is rejected as invalid. Which
  route lists those ids has not been established, and none is guessed at

- `consistency_score` measures the investor's own consistency. The journal
  records what the CIO decided, not what the investor did about it, so the
  score still reports the neutral midpoint
- The track record is measurable but empty. Every recorded decision is
  younger than the 30 days a price move needs to say anything, so
  `movrvest record` reports 61 decisions and 0 outcomes. It stays that way
  until the start of September, and no hit rate is reported before 10
  measured calls
- Closed trades cannot score anything on this account: the trade history
  returns an empty list back to January 2025. A closed trade is also the
  *investor's* action rather than the CIO's, so it answers the
  `consistency_score` question, not this one
- `app/analysts` holds real per-security fundamental analysis the canonical
  reasoning layer does not yet own

## Delivery

- API routes construct services directly, so they cannot be tested without
  network access
- The change feed reads the market archive, so it reports movements only
  from the second recorded observation onwards. A fresh clone has no
  market past and says nothing rather than comparing against an invented
  first reading
- `ExecutivePipeline` recomputes symbol-independent reasoning per holding
- `ClaimEngine.test.ts` has pre-existing TypeScript errors (missing `vitest`)

## Structure

- `app/services` still mixes load-bearing and incidental modules
- Analysts accept `Brain | BrainContext`; narrowing them retires the legacy
  `BrainContext`

---

# Next Priorities

## Company Knowledge

The active line of work. What a business *is*, read from the document the
company is legally answerable for.

**Delivered**

- The Company Knowledge layer — structural facts about a business, kept
  apart from evidence because they turn over across years, not minutes
- The `PrimarySourceProvider` abstraction — acquisition behind a seam, so a
  regulator, an ESEF filing and a company's own report reach extraction,
  storage and reuse identically
- Cache-first acquisition — resolve the current document, serve stored
  knowledge if its key is known, otherwise acquire, validate and store;
  knowledge refreshes only when the authoritative document changes
- Grounded extraction — every segment carries a verbatim span checked
  against the document, and an extraction quoting words that are not there
  is discarded in full
- Schema versioning — the source is immutable, the reading of it is not, so
  an entry written under an older extraction is treated as absent and read
  again rather than upgraded in place
- Reporting-period support — the business period the filing covers, kept
  apart from the date it was published
- The ESEF provider — European filings behind the same seam, read from the
  filer's own IFRS tagging rather than from section headings, with the
  issuer's identity established from GLEIF and checked again against the
  document's own LEI
- The Investor Relations provider — a company's own published report,
  behind a reviewed location and a reviewed hash, admitted only where the
  document identifies its own issuer
- `authority`, provenance and `verification` on `PrimarySource` — what
  kind of source it is, who supplied it, and which identity checks
  actually held, carried into every citation and stored with the
  knowledge

**Next**

Ordered by what a wrong answer costs. The archetype rules are live, and
running them over eight filings measured where this platform actually
stops — which is not in the rules. Two of eight companies classify. The
rest are refused for want of an input, and every one of those refusals
is a reading that could have gone better rather than a document that
says nothing:

**Re-measured 2026-08-06 under schema 7**, every filing read again
through the full pipeline. Structural ownership changed how six
descriptions are *owned* and changed the coverage table not at all:

| | Size measured | Way of earning evidenced | Classifies |
|---|---|---|---|
| DIS, NVDA | ✅ | ✅ | ✅ |
| META, VOW3.DE | ✅ | ✗ | ✗ |
| CAT, NFLX | ✗ | ✅ | ✗ |
| JPM | ✗ | ✗ | ✗ |
| COST | extraction refused outright | | ✗ |

Two of seven classify, the same two as before. **Coverage did not
materially improve, so the next work is evidence acquisition rather than
richer taxonomy.**

**Meta is the finding.** Its segments now have owning regions and the
regions contain exactly the prose a reader would want — `Family of Apps
Products` opens with *"Facebook helps give people the power to build
community…"*. The reading does not quote it. Asked what the segment
does, the reader reaches for the sentences that contain the segment's
*stored name*, and on this filing those live under `Revenue and
Investments`: *"selling advertising placements on our family of apps to
marketers, which is reflected in FoA"*. Genuinely about FoA, genuinely
naming it, and outside the section that owns it — so it is refused, and
the bounded repair returned the same sentence and was refused again.

That is not a regression: proximity refused the same span before, for a
different reason. It relocates the defect. The ownership model is no
longer the thing standing in the way — **the reader is not being told
where the owning section is.** The document's structure is now computed
before the reading and never reaches the reading, which is the gap to
close next, and it is acquisition rather than taxonomy.

Two instabilities the re-read exposed, neither caused by this slice:

- **Segment identity is not stable across readings.** JPMorgan came back
  as `Consumer & Community Banking (CCB)` where the previous reading
  said `Consumer & Community Banking`. Both are in the filing. A stored
  entry keyed by the reader's choice of name is a fact that moves.
- **Ways of earning drift additively.** NVDA's `Graphics` gained
  `services`, which the previous reading did not report from the same
  document.

1. **Segment sizes where a table was not found.** Caterpillar and
   JPMorgan describe their segments and neither had a size proven. Both
   print segment revenue; the mix reading did not locate it. Worth
   measuring before assuming the cause
2. **Manual document ingestion.** A document handed to the platform
   directly, carrying the same identity and the same grounding contract as
   one it fetched itself
3. **Playbook selection from the archetype.** The consequence this slice
   exists to enable, and deliberately not taken yet: `PlaybookSelector`
   still reads the provider's industry, and flipping it while most of the
   population is unclassifiable would degrade every holding whose filing
   has not been read. A controlled migration, not a flag day:

   1. archetype available and sufficiently established → use it
   2. archetype unavailable or incomplete → keep the existing selector
      and expose the limitation rather than hiding the fallback
   3. retire industry-driven selection only once the grounded route
      demonstrably covers the portfolio

   An interpretation does not become authoritative merely because it
   exists. It follows coverage, not the other way round
4. **Dossier transparency for company knowledge, coverage and playbook
   selection.** Which companies the platform has read, from which document,
   as of which period; under which authority and on which identity checks;
   why a security drew the playbook it did; and, stated apart, what could
   not be read and why
5. **Multilingual presentation, with the original preserved.** The stored
   grounded span stays in the language it was published in — replacing it
   with a translation severs the evidence chain, which is the one thing
   the store exists to keep intact. Presentation gains a second, clearly
   labelled layer: a translation is a derived communication artifact and
   never the canonical span. Downstream of understanding rather than
   ahead of it: knowledge becomes understanding, and understanding is
   then communicated in whatever language the investor reads

**Open, and deliberately so**

- Symbol-to-ISIN is a reviewed list, not a lookup. It has to be: no free
  authority maps a ticker to an ISIN, and the one library that offers to
  returns another instrument entirely. Coverage grows by verifying an
  entry, and an unlisted symbol is reported as unidentified rather than
  guessed at. If a licensed reference feed ever enters the platform, this
  is the first thing it should replace
- Investor-Relations locations are reviewed, not discovered, for the same
  reason and with a sharper edge: no authority publishes which website
  belongs to which company. Each entry also carries the hash of the bytes
  reviewed, so an entry goes stale the day the company publishes its next
  report — the platform then keeps serving the reviewed document and
  states the period it covers, rather than silently following a moving
  URL. Visible staleness in exchange for invisible staleness
- Knowledge read from an original-language document is in that language.
  `VOW3.DE`'s stored description reads "Der Volkswagen Konzern berichtet
  die Segmente…", because the platform reads the filing rather than a
  translation of it. That is the correct reading and the surfaces are not
  yet ready to present it
- A segment's size is measured only where the filing prints it in a table
  this platform can read as a grid. A report whose discussion is prose, or
  whose tables have no total, keeps its segments and leaves their sizes
  absent. That is the honest outcome and the alternative is a plausible
  number, but it is a real coverage limit rather than a solved problem
- **Applicability is positional, so it cannot judge subject matter.**
  Ownership and proximity catch a description that sits under another
  segment or far from its own, and they cannot tell a description from a
  note that happens to sit exactly where a description would.
  Volkswagen's footnote was caught at 814 characters; the same sentence
  one line below a segment's description would pass. Closing that means
  judging what a sentence is *about*, which is a different kind of check
  from where it sits — and a different slice
- **A description is read once and not retried.** An inapplicable span is
  an absence rather than a rejection, so it does not trigger the reread
  that a failed grounding contract does. A single sloppy draft therefore
  costs a description that a second attempt might have evidenced. Left
  as it is deliberately: retrying until something passes is how a
  threshold turns into a search for whatever clears it
- In the layout where segments are columns, the shared row proves the two
  figures measure the same line item and does not prove they cover the
  same period — a table whose columns are segments states its period in
  its caption, not in its headers. Both figures' headers are recorded so a
  reader can see what each one is; the platform does not claim the period
  was established when it was not

## Policy — `data/knowledge/` is tracked, and is not a cache

### What a knowledge entry is

```text
Immutable primary source
        ↓
Versioned grounded reading
        ↓
Canonical knowledge artifact for that reading version
```

Company Knowledge is not universally canonical. It is canonical **for a
given source and a given reading schema version**, and the middle line is
where the versioning lives: `KNOWLEDGE_SCHEMA_VERSION` deliberately changes
what a valid stored reading means. When it changes, the platform does not
mutate old entries or fill in newly required fields — it performs a new
grounded reading of a document that never changed.

### Why it is not a cache

The test is reproducibility, not value. A cache entry is rebuildable
byte-identically from its provider; that is what makes discarding it free.
A grounded reading is not: extraction chooses which verbatim span to quote
and is retried under the grounding contract until one survives, so two
extractions of the same immutable filing can select different spans while
remaining equally truthful. `data/knowledge/` therefore does not satisfy the
technical definition of a cache, and the rest of `data/` has settled answers
that do not fit it either — `data/cache/` is ignored as re-fetchable and
never source of truth, `data/evidence/` and `data/events/` as one machine's
own record that a fresh clone should not replay.

### Migrating the corpus, and what the first migration measured

A schema bump is not storage housekeeping. It is a **new grounded
reading** of documents that have not changed, and it can change what the
platform knows. So a bump is closed the same way every time:

1. Re-read every affected company under the new version.
2. Review the diffs by meaning — segment identity, measured size, ways
   of earning, whether a description survived — rather than accepting
   them.
3. Commit the new artifacts in the same slice as the bump.
4. Record material drift, especially changed segment identity or
   segments that appeared or vanished.
4. **Never normalise a new reading back to the old one for diff
   stability.** The new reading is the reading; a corpus tidied to match
   its predecessor is no longer grounded in anything.

Leaving entries behind at an older version is the alternative and it is
worse than either extreme: a fresh clone treats them as absent and
re-reads anyway, so they give neither a stable regression corpus nor a
warm start, while presenting themselves as current.

**Schema 5 → 6, the first migration, over seven companies.** Every
measured size was identical to the digit, and every prose fact moved:

| Drift | Where |
|---|---|
| Quoted span changed | DIS, NVDA, CAT — same segments, same sizes, different words chosen |
| A way of earning disappeared | CAT lost `transaction` on all three industrial segments |
| Segment identity changed | NFLX: `One operating segment` → `one operating segment` |
| Company description reworded | CAT, NFLX, VOW3.DE |
| No segment appeared or vanished | every company except the NFLX rename |

Two things follow, and both are load-bearing.

**Cell-addressed evidence is reproducible and span evidence is not.**
Every size survived two independent readings unchanged, because a size
is an address into a table this platform reads for itself. Every quote
moved, because a span is something a reader chooses. That is the
architecture's own claim, measured rather than asserted, and it is why
sizes can be trusted across readings in a way descriptions cannot.

**A segment's identity is its name, and a name is fragile.** Netflix's
"segment" is the phrase *one operating segment*, and a change of case
made it a different segment to the store. Nothing was lost — the entry
is keyed by document, so the new reading replaced the old whole — but a
corpus keyed on model-chosen strings will drift, and the archetype
engine reads those names. Worth watching before it matters.

The classifications themselves were stable: DIS diversified, NVDA
manufacturer, CAT and NFLX unclassified, before and after.

### The policy

- **Keep `data/knowledge/` tracked.** Do not add it to `.gitignore`.
- **Treat entries as versioned, grounded knowledge artifacts**, not as
  runtime cache files.
- **Close a schema bump with a reviewed re-read of the whole corpus**,
  in the slice that bumps it. Never ship a mixed-version corpus.
- **Reassess only on evidence of an operational problem**, against the
  criteria below.

Schema versioning strengthens this rather than weakening it. Because a
revision produces a new reading instead of an edited one, Git is what
records which reading schema produced an artifact, what a schema revision
changed, which grounded spans were selected, and how downstream reasoning
behaved against a fixed historical corpus. Untracked, that history is
destroyed every time entries are regenerated.

Tracking is also the reversible option. Untracking later loses nothing;
never tracking means the historical corpus was never built.

### Reassessment criteria

1. Repository growth and clone performance.
2. Frequency and readability of generated diffs.
3. iCloud conflict-copy incidence.
4. Whether the corpus is still useful for regression and audit.
5. Whether Git remains the correct long-term storage mechanism at scale.

### The operational risk is iCloud, not size

This repository lives in iCloud Drive, which has put tracked generated
directories in the path of conflict copies twice. The `.gitignore` rule that
covers them is load-bearing for this decision and must be retained. Checked
against real knowledge filenames: `DIS.<accession> 2.json` and
`DIS.<accession> 2 2.json` are ignored; `DIS.<accession> 10.json` was not,
because the single-digit rule could not match two digits, so a
double-digit rule was added alongside it. Verify with `git check-ignore`
rather than by reading the pattern.

### If Git stops being the right store

At sufficient corpus size, validated artifacts may move to a versioned
object store or database. That would be a **storage migration, not a
reclassification** of Company Knowledge as disposable. Any such store must
preserve immutable source identity, the reading schema version, extraction
metadata, provenance, content hashes and historical revisions — which is
the same list Git supplies today.

## Trustworthy evidence

Caching and a more reliable fundamentals source, crypto symbol resolution,
and asset-class classification. Everything downstream inherits the quality of
this layer.

## Learning

Decision history is recorded. Outcome analysis — was the decision right? —
and the behavioural consistency that depends on the investor's own actions
are still open.

## Explainability

The change feed reports what the Artificial CIO changed its mind about and
what the market did. A benchmark move now also says which holdings it
touches and how much, from each holding's measured `market_sensitivity` and
its share of the account — and counts the holdings nothing was measured
for. What remains open is the same connection for moves that are not the
benchmark's: a beta to SPY says nothing about an oil move, and connecting
one honestly needs a sensitivity to that instrument nobody has measured.

---

# Long-Term Vision

MOVRvest is an Artificial Chief Investment Officer.

Its purpose is not to predict markets. It is to help investors consistently
make better investment decisions by transforming verified evidence into
transparent, explainable and trustworthy executive recommendations.

Trust is the product. Everything else exists to support it.
