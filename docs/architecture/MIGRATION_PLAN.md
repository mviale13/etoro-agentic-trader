# MOVRvest Migration Plan

> Living roadmap for converging the repository toward the canonical
> architecture.

Status: Active

---

# Mission

Every sprint must make the repository:

- Simpler
- More consistent
- More explainable
- Easier to extend

Rule:

> Migrate before deleting.
> Delete only after verification.

---

# Migration Principles

## 1. One Concept = One Owner

Every business concept has exactly one canonical implementation. If
duplicates exist: choose the canonical one, migrate callers, remove the rest.

## 2. Verify Before Believing

A package is canonical when the import graph says so, not when a document
does. Check with `grep -rln` from a real entry point before building on
something — and before deleting it.

## 3. Preserve Behaviour

Migrations improve structure, not functionality. Where behaviour must change,
say so explicitly.

## 4. Keep Quality Green

Ruff, mypy and pytest stay green after every migration. Verify the commit,
not just the working tree: pre-commit stashes unstaged changes but leaves
untracked files in place, so hooks can pass on a tree the commit does not
contain.

## 5. Never Estimate What You Cannot Measure

A plausible number on an investment dashboard reads as a measurement. Where
evidence is missing, report it as missing.

---

# Completed

## The canonical pipeline is live

Brain → Reasoning → Committees → Artificial CIO → Communication → Dashboard
now runs end to end, from `movrvest evaluate` and from `GET /executive/...`.

- Communication wired in: `ExecutiveBriefBuilder` populates
  `ExecutiveWorkspace.brief`, replacing a hardcoded "No urgent decision
  today" that no computation could change
- `BrainBuilderService` completed and reachable from a live entry point
- The dashboard consumes real data: the field-name mismatch that silently
  substituted demo values is fixed, and the last mock is gone
- Holdings are perceived per security: the broker reports each position, the
  watchlists name it, and per-security signals reach the Brain as evidence
- The Artificial CIO judges each holding on that evidence, so decisions
  differ per symbol rather than repeating one portfolio-level verdict
- `ReasoningSnapshot` carries all five assessments; `policy_alignment_score`
  is measured against the Investment Policy rather than hardcoded
- The legacy `BrainPipeline` chain and 45 superseded files are deleted

## The Artificial CIO has memory

Each decision is recorded once per symbol, per day, per state, and the next
cycle perceives it:

```
ArtificialCIO → ExecutiveDecision → DecisionJournal → EventRepository
                                          ↓
                        MemoryPerception → Brain.decision_history
                                          ↓
                        InvestmentThesis.previous_decisions → CLI · API · web
```

- `MemoryPerception` was an empty class; it now reads the journal
- A symbol the CIO has never judged reports an empty history, and the
  investment case says nothing rather than "no change"
- The pipeline only writes when a journal is injected, so a test or a
  what-if evaluation never enters the record
- `ChangeFeedService` returned three hardcoded examples ("NVIDIA upgraded")
  and was imported by nothing. It now reads the journal, reports each
  recorded state change newest first, and reaches the dashboard through
  `GET /executive/portfolio`. Severity is the distance the decision moved
  along the lifecycle, so it is measured rather than asserted
- The Python reasoning stranded inside `apps/web/movrvest-web` is deleted,
  along with two uncommitted migration shims

## The opportunity pipeline is evidenced

```
Watchlists → OpportunityPerception → Brain.candidates
                                          ↓
                     SecurityPerception (capped) → evidence
                                          ↓
              CandidateResearchService → ExecutivePipeline → /research/candidates
```

- Only candidates the Brain can describe on their own evidence are judged.
  Judging the rest would produce a verdict about the account wearing the
  candidate's name, so they are counted and reported as unevidenced
- The funnel separates "not reviewed" from "reviewed but not evidenced", so a
  rate-limit budget is never mistaken for a screening result
- `ExecutiveWorkspace` now keeps the `DecisionEvidence` the decision was made
  on, which is what the page shows as quality, valuation, risk and fit
- Deleted: `OpportunityService` and `OpportunityDiscoveryService` (both
  returned hardcoded companies), `GET /opportunities/`, the dead
  `TopOpportunitiesCard`, and the hardcoded candidate array in the page

## Evidence is cached, and therefore deterministic

```
CompanyFactsService → CachedValueProvider  → fundamentals, once a day
                    → CachedMarketProvider → quotes, 15 minutes
```

- Fundamentals are read once per UTC day, so two runs on the same day cannot
  produce different decisions on their own. That matters more than the saved
  requests: the journal records decision changes, and provider noise was
  about to be reported to the investor as the CIO changing its mind
- A quote is never served stale. A price is a claim about now, so an expired
  one is fetched or reported absent — never replayed
- Fundamentals *are* served stale when the provider fails, carrying the date
  they were actually observed. Old evidence is still evidence; it is simply
  never dated today
- Symbols the provider cannot price (crypto without a `-USD` suffix, eToro
  futures) are remembered as unpriceable for 30 minutes instead of being
  retried on every request
- Measured on the live account: a research cycle went from 50 provider calls
  and 9.0s to 0 calls and 2.2s, with identical decisions across runs

## Absent evidence is absent in the decision path

Three substitutions filled a missing measurement with a number measured
about something else:

| Missing | Was filled with | Now |
|---|---|---|
| Company quality | The portfolio's health score | Absent |
| Company valuation | Market momentum | Absent |
| Market and drawdown risk | `0.50` each, hardcoded | Absent, and named |

Consequences, all deliberate:

- `DecisionEvidence.quality_score`, `valuation_score` and `risk_score` are
  `int | None`. None means not measured — never zero, never borrowed
- An unmeasured score is not a reason to reject: not knowing something is
  not the same as knowing it is bad. It is a reason not to progress, so
  unmeasured quality caps the case at INVESTIGATE and unmeasured valuation
  or risk caps it at PREPARE
- Conviction averages only the scores that exist, so a gap is neither
  counted as zero nor credited as full marks
- Overall risk stays absent while any component is missing. Averaging the
  measured half reported "risk: 0" for an account whose market and drawdown
  exposure nobody had looked at — and because low risk is scored as
  conviction, that zero pushed two candidates to RECOMMEND
- The research page separates what was measured about the company from what
  was measured about the account: "Your portfolio's risk" and "Fit with your
  portfolio" no longer sit in the per-company row

## Risk is measured from the security's own record

```
yf.download(period="1y")  →  MarketQuote.realized_volatility, .max_drawdown
                                        ↓
                          CompanyFacts → RiskSignalService → RiskSignal
                                        ↓
                     DecisionEvidence.risk_score, per security
```

- The quote request already existed and fetched five daily bars. A year
  costs the same single request, and it is cached, so the measurement is
  effectively free
- Volatility is the annualised standard deviation of daily returns;
  drawdown is the deepest peak-to-trough fall in the window. Both describe
  the observed past and neither predicts anything
- The bands that turn those measurements into LOW/MODERATE/HIGH/SEVERE are
  policy, stated in `RiskSignalService` rather than buried in a score
- SEVERE sits above `DecisionPolicy.maximum_acceptable_risk`, so a security
  is rejected on its own record rather than on a judgement about the account
- A security whose history is too short reports UNKNOWN, and the case cannot
  reach RECOMMEND on it

## Deleted

See the Removed table in `REPOSITORY_INVENTORY.md`.

---

# Open Work

## Open: knowledge is one draw, and coverage was measured on it

Settled by measurement, not yet acted on. `movrvest reader-stability`
established the acquisition layer's variance over fifty readings of five
10-Ks, and it is concentrated rather than spread: every segment size agreed
in every reading, and everything a model reads out of prose moves — ways of
earning to 6 of 10, cited spans to 3 of 10, and NVIDIA's archetype to 6 of
10 on a single segment's ways of earning crossing a rule threshold.

Three consequences, in the order they have to be taken:

1. **Coverage and stability are different qualities and must be reported
   apart.** A company that classifies every time and one that classifies
   60% of the time because successive readings disagree are not the same
   finding, and every coverage figure this repository has published was
   measured on one draw. The layering the platform now needs is

   ```text
   Acquisition Coverage  →  Knowledge Stability  →  Business Understanding
   ```

   with the middle term measured rather than assumed. Nothing surfaces it
   yet; `reader-stability` is a developer instrument.

2. **Then decide what a stored reading is.** Today it is whichever draw ran,
   presented as the company's own account of itself — Caterpillar's stored
   entry is a one-in-twenty reading, and it changes the archetype. The
   options are to keep one reading and state that it is one, or to store the
   modal reading of several and state how far they agreed. Neither is free,
   and the second is one careless step from reading until an answer pleases,
   which `docs/architecture.md` forecloses: what makes a mode legitimate and
   a retry illegitimate is that a mode is chosen without reference to
   whether the answer is liked.

   **Done.** [`KNOWLEDGE_CONSENSUS.md`](KNOWLEDGE_CONSENSUS.md) was
   accepted and the authorized slice is implemented: observations (schema
   9, append-only, schema-8 entries carried forward as width 1),
   `consensus_of` derived on read, the archetype engine consuming
   consensus only, and `movrvest observe` filling quorums on a count-only
   stopping rule. Accepted live on NVDA, CAT, META and JPM at quorum —
   CAT's one-in-twenty "Service business" is structurally unreachable and
   reads Diversified. Still open from the original list: surfacing the
   three-layer reporting (coverage / stability / understanding) beyond
   the developer CLI, and automatic quorum acquisition, which is
   deliberately unbuilt until the cost is taken knowingly.

3. **Only then return to acquisition coverage.** An improvement smaller
   than the variance it is measured against cannot be told from another draw
   of the same distribution. The measured floor is what makes the next
   acquisition slice checkable.

**What the measurement says to build.** Variance is absent exactly where
evidence is an address this platform verifies against a parsed table, and
present exactly where it is a model's reading of prose. That is the
strongest available evidence for giving narrative evidence the treatment
quantitative evidence already has — the model pointing at structure the
platform reads, rather than the model returning the words.

## Open: PlaybookSelector consumes Business Understanding

The Business Understanding layer exists (`understand()` over
`CompanyKnowledgeConsensus`, surfaced by `movrvest understanding`), and
the selector's question changes with it: not *what industry is this*,
but *which investment playbook best matches this business
understanding*.

**Done in the selection slice:** the deterministic mapping and the
unblended seam, per
[`PLAYBOOK_SELECTION.md`](PLAYBOOK_SELECTION.md). `select_grounded()`
maps a quorate understanding's archetype to an earned playbook or
refuses by name; `PlaybookSelectionService` falls back to the industry
selector on refusal, recorded with the reason verbatim; `movrvest
playbook` is the surface. Accepted live on all five quorate companies —
three authoritative, two honest fallbacks.

**Still open — the research-path flip.** `ResearchStrategyFactory`,
the dossiers and the committees keep consuming the industry selector
unchanged. Before the flip: enough of the book's holdings at quorum for
it not to degrade every case whose filing is thin, and the mapping's
vocabulary grown case by earned case (a grounded Bank rule, for
instance, needs `financial_spread` established at quorum for some
company — JPM's filing points elsewhere for exactly the figures that
would do it). The two routes stay unblended throughout.

## Next phase: Operation First Reading (accepted 2026-08-07)

The coverage measurement (first run: 75 securities, 70 never read, 2
grounded) settled the question the reasoning slices kept deferring:
**the bottleneck is acquisition breadth, not reasoning quality.** The
Evidence Graph, consensus, Business Understanding and the
PlaybookSelector are each sufficient for the corpus they see; none is
expanded until the measurements demand it. The build-the-engine phase
is over; the feed-the-engine phase begins.

**Frozen until measured demand:** new playbooks, new Business
Understanding features, new consensus work, new evidence theory. A new
grounded playbook still requires all four of: a real company at quorum,
an understanding that establishes the pattern, an obvious deterministic
mapping, and a live acceptance case. Case-by-case, never
taxonomy-first.

**The KPI is investor-visible understanding, not observation width.**
`movrvest playbook-coverage` leads with the funnel — companies → read →
understanding decided → playbook mapped → quorate — portfolio first.
Moving a company from 0 → 1 observations moves it through three rows;
moving 1 → 5 moves it through one. The authority gate does not move: a
width-1 decision is visible and labelled, and only quorum makes it
authoritative.

1. **Phase A — portfolio.** Every held company reaches: identity
   resolved, primary source acquired, one grounded observation, a
   Business Understanding, a playbook. Width 1 is vastly more valuable
   than width 0; quorum is not chased here.
2. **Phase B — watchlist.** The same, in the same order.
3. **Phase C — quorum promotion.** Only after A and B, and per
   company: repeated observation becomes a quality investment chosen
   on the funnel's numbers, never a default.

Each acquisition is the explicit, counted spend it always was
(`movrvest knowledge`, then `movrvest observe` for promotion) — the
phase changes what is prioritised, not how carefully it is paid for.

### Revised after Phase A (2026-08-07): three streams, not one backlog

Phase A's result (portfolio 71% read; the two remaining gaps not
acquisition-shaped) classified the blockers by engineering class, and
the roadmap follows the classes:

- **Stream A — acquisition.** First readings only where acquisition is
  genuinely the blocker. SPCX is complete for now: no annual report
  exists; it waits for a filing, not for engineering.

  **The acquisition slice (2026-08-07, approved after Reader Slice 1).**
  Reader Slice 1 localised the bottleneck one layer up: the reader was
  never failing on JPM or VOW3.DE, it was correctly refusing to invent
  descriptions absent from the text it was handed. So a located section
  is now searched for the filer's own cross-reference — "under the
  heading «X»", the filer's words, never this platform's guess at what
  a section might be called — and what it names is read too, on two
  conditions: the filer must say it is referring, and the heading it
  quotes must occur exactly once in the document as something that
  begins a block. Two blocks carrying it means the filing did not
  disambiguate, and it is refused rather than chosen between (the rule
  `owning` already applies). Measured on the earning filing: Item 1's
  reference resolves to one block among nine occurrences and Item 7's
  to forty-two, so the first is followed and the second declined.

  Schema 10 follows necessarily: entries under 9 are faithful records
  of what their readings were *shown*, and they were shown less of the
  filing, so pooling them with readings of the wider text would derive
  a consensus over two different strings. They are absent, not
  relabeled, and the corpus is re-read.

  **Verified live with the reader unmodified:** all four JPMorgan
  segments now carry grounded descriptions — financial_spread,
  services, transaction, asset_management_fees — where nine stored
  readings had found none.

  **Three findings this slice measured, none of them a defect:**

  1. **The referenced chapter's tables are deliberately not merged.**
     Handing the size reading JPMorgan's twenty-five MD&A tables made
     it cite a cell whose column carries no header, and a mix that
     cannot be checked discards the whole reading — descriptions
     included. Sizes are a different claim and are not worth trading
     for descriptions. Reading tables of that shape is a measurement of
     its own.
  2. **VOW3.DE is not reachable by this mechanism, and its case is now
     precise.** Its narrative lives in the package's *management
     report* — 13.4 MB, and confirmed to carry **zero** XBRL tags, so
     the tagged route cannot see it. Three language-independent
     locators were tried and all three land on tables rather than on
     the description: densest occurrence of the IFRS term "segment"
     (lands on the ratings chapter), smallest window naming all three
     segments (lands on a table header row), and naming-outside-a-table
     (VW's layout defeats the table test). The descriptive passage
     exists and was read by hand — "Im Segment Pkw und leichte
     Nutzfahrzeuge …", "Das Segment Nutzfahrzeuge umfasst …", "Der
     Konzernbereich Finanzdienstleistungen …" — so the evidence is
     real and the *locator* is what is missing. Not earned by one
     company; recorded here rather than guessed at.
  3. **JPM cannot move the portfolio KPI, because JPM is not in the
     portfolio** — it is on neither the book nor a watchlist. The KPI
     path from this slice runs through BNP.PA, a held bank at 1/5:
     JPM's descriptions establish `financial_spread` at quorum, which
     is exactly what a grounded Bank rule was waiting on, and BNP.PA
     becomes its first live acceptance case. That rule is a vocabulary
     decision reserved to the measurements' owner, so the KPI does not
     move inside this slice and the reason is structural rather than a
     failure of the mechanism.

  **Measured at quorum (JPM, 5 observations under protocol 10).** The
  targeted causes are gone: `description never arrived` and `no
  description found when asked by name` are both **zero**, and every
  remaining JPM absence is a *size*. Four revenue mechanisms are
  established — `financial_spread` (4/5, across all four segments),
  `asset_management_fees`, `services`, `transaction` — and Business
  Understanding reaches quorum.

  **The chain now stops exactly one link further along, and names its
  own next bottleneck unanimously:**

  | Link | Before | After |
  |---|---|---|
  | grounded descriptions | absent | **established, 3/3** |
  | revenue mechanisms | none | **four, at quorum** |
  | Business Understanding | blocked | **quorate** |
  | archetype | — | refused: sizes unsettled |
  | authoritative playbook | — | refused |
  | portfolio KPI | 2 | 2 |

  The archetype's own words: "The ways this business earns are known
  and cannot be ordered. Counting segments would weigh its largest and
  smallest parts equally." All four size claims carry one reason —
  *document points elsewhere for its tables* — which is precisely the
  finding (1) this slice declined to attack. **The next slice is
  therefore earned by measurement rather than inferred: read the
  referenced chapter's tables**, which is the same cross-reference
  mechanism applied to the tabular half, and which the size reading
  must be shown to survive before the chapter's tables are handed to
  it.

  **The tabular slice (2026-08-07, approved after PR #52).** The same
  cross-reference discipline applied to the tabular half, and the
  reader again unmodified — three parse rules, each measured on the
  filing that earned it: a spanned group's words cover every column
  the filer's colspan asserted (numbers and lone currency symbols are
  never repeated — an aliased figure would defeat the duplicate-cell
  check); a table split by the page is read as the one table it is,
  proven by the label column the filer repeated and gated by the
  headers (JPMorgan's pair merges; Volkswagen's repeated prior-year
  pair does not); and a pointer discussion is served the referenced
  chapter's tables. Schema 11 supersedes the corpus.

  **The chain closed end-to-end on JPM for the first time:**
  descriptions (3/3) → four mechanisms → sizes grounded — CCB 41.0%,
  CIB 42.3%, AWM 13.0%, each the platform's own division of two
  checked cells of the merged table — → archetype **Diversified**
  (financial_spread, services and transaction lead together, within
  5%) → **authoritative playbook: Diversified Business**, resting
  stated on its narrowest claim (3/5 on the segment frame).
  `document points elsewhere for its tables` is **zero**; JPM's one
  remaining defect is an earning disagreement at AWM (noise, the
  consensus's own territory). The portfolio KPI stayed 2, exactly as
  the slice predicted: JPM is on no tracked list, and the KPI path
  still runs through BNP.PA and the unearned Bank rule.

  **Operational finding, stated rather than smoothed over:** the
  protocol-11 re-read ran out of OpenAI credits at BNP.PA and
  VOW3.DE, so their superseded entries are absent until the account
  is funded and `movrvest observe` completes them — the portfolio
  funnel reads lower in the interim, and VOW3.DE's
  `no description found when asked by name` claims are unmeasurable
  rather than resolved. A second finding from the same failure: a
  provider outage inside an observe run surfaced as a raw traceback
  instead of a worded PROVIDER_ERROR outcome, against this platform's
  own absence discipline — recorded for a small follow-up fix.
  **Fixed (2026-08-08), earned by a second measurement:** the first
  statement reading hit the same exhausted balance and the same
  traceback, so both narrative providers now wrap their SDK's errors
  into the seam's worded decline, and the same 429 renders as
  `invalid_extraction` with the provider's sentence carried verbatim.

  **The Evidence Graph** (the owner's strategic note on PR #52): the
  natural abstraction once narrative and tabular cross-references both
  exist — evidence nodes related by *describes / quantifies /
  references / continues / defines*. Deliberately not built yet, per
  the owner's own rule: generalise only once two or three independent
  mechanisms converge on the abstraction. Two exist today
  (`_referenced` follows *references*; `_continues` merges
  *continues*); the third convergence is the earned trigger.

  **The Reference Corpus (2026-08-07, the owner's designation after
  PR #53).** An engineering status, not a user-facing concept: the
  companies every reasoning change must keep passing through, each in
  the corpus for a property its filings exercise —
  `app/domain/reference_corpus.py` names all seven with their reasons
  (JPM the complete chain; DIS, NVDA, CAT, VOW3.DE, META, UMI.BR the
  edges they each proved). The coverage measurement tracks them under
  their own origin, behind the investor's lists: a reference company
  the investor also holds or watches counts under the origin they
  gave it, and one tracked for engineering alone can never enter the
  portfolio or watchlist funnels or move the KPI. JPM thereby becomes
  the platform's canonical regression company without ever being a
  recommendation.

### The knowledge stack is closed (the owner, 2026-08-07, after PR #54)

**No further infrastructure slice unless the measurements demand one.**
Identity, evidence, consensus, Business Understanding, grounded
playbooks and the Reference Corpus together are sufficient: the
nervous system is built, and §19a governs any reopening — a measured
pattern earns a slice, nothing else does. The Reference Corpus is now
part of the engineering contract (constitution §19b): every reasoning
change proves itself against it before reaching the investor, and the
corpus stays stable.

**Remaining operational work, in order, none of it engineering:**

1. Fund the observation account (the owner, at the provider's
   billing page).
2. Complete the protocol-11 corpus: `movrvest observe BNP.PA` and
   `movrvest observe VOW3.DE` — one background run.
3. Measure BNP.PA at quorum under the better tables. Its protocol-10
   reading left CPBS (52% of revenue) unsettled five ways; whether
   protocol 11 settles it is the case-earns-the-rule test for the
   first grounded financial-services playbook. The case earns the
   rule, never the other way around.

**The next major engineering effort is the Artificial CIO.** The
question changes from "how does this business make money?" to "given
everything we know, what should the investor do?" — Business
Understanding becomes an input, grounded playbooks become an input,
and portfolio, market, valuation, macro and investor context become
peer inputs. That is the product. Deliberately not started here: it
begins after the corpus completes, with its own design phase, on top
of a nervous system that is for the first time mature enough to build
the brain on rather than alongside.

### The Artificial CIO design brief (the owner, 2026-08-08)

**The CIO begins with a design question, not a coding question: what
is an investment decision?** Not what the UI shows, not what data to
add, not which committee should exist. The decision model comes
first; everything else — committees, scoring, portfolio reasoning,
opportunity ranking, risk balancing, executive briefs — derives from
it, exactly as the platform once grew around `CompanyKnowledge`.

**The first deliverable, before any code: the minimal canonical
Decision object.** A design document only, in the tradition of
`KNOWLEDGE_CONSENSUS.md`.

**The owner's constraints, carried from the knowledge platform:**

- It consumes established facts; it never establishes new ones.
- It may weigh evidence; it may never rewrite evidence.
- It must state what changed.
- It must state why it matters.
- It must state why it matters *for this investor*.
- It must distinguish uncertainty from disagreement.
- It must refuse conclusions unsupported by its inputs.
- Every recommendation must be explainable by walking backwards
  through the existing evidence graph.

The CIO is another deterministic consumer of the platform — not a
replacement for it. Success criterion: the knowledge platform
answered *how well do we understand this company?*; the CIO answers
*given everything we know, what should the investor do — and why?*

**Noted at the boundary, for the design session:** the existing
`CommitteeDecision` is a vote-count object — `recommendation: str`,
`confidence: int`, buy/hold/sell tallies — free text beside an
unexplainable number, and it cannot be the canonical object; it will
need reconciliation under *one business concept, one implementation*
when the model lands. `config/policy.yaml` (risk profile, allocation
targets, position constraints) is the seed the *for-this-investor*
clause grows from.

### The assessment contract is frozen; the acquisition begins (2026-08-08)

The decision layer shipped (PR #58: `JPM.entry.0001` = `MONITOR`, the
model validated by what it refused to manufacture) and the assessment
design was accepted and merged (PR #59). The owner then confirmed the
three-step course, executed in order:

1. **The Assessment contract is frozen.**
   [`INVESTMENT_ASSESSMENT.md`](INVESTMENT_ASSESSMENT.md) records it:
   the object, the boundaries and the sequence hold through all three
   implementation steps, and amending any of them is an owner's
   decision recorded there — never a side effect of implementation.
2. **The Financial Statement Acquisition slice is open** — the earned
   §19a reopening of the knowledge stack, designed in
   [`FINANCIAL_STATEMENT_ACQUISITION.md`](FINANCIAL_STATEMENT_ACQUISITION.md)
   and implemented as its own observation stream: the income statement
   located where the filer typeset its title (the structural-section
   rule's third application), anchors checked by the tabular chain,
   rows read by the platform with no model claim in them, consensus
   with widths over `data/statements` (schema 1, never pooled with
   segment readings). Surfaces: `movrvest statements`,
   `movrvest observe-statements`. The segment corpus is untouched — no
   re-read, no supersession. The measurement plan is JPM to quorum,
   which requires the funded observation account.
3. **Business Quality waits** until the acquisition is complete and
   measured. Nothing in the slice defines a kind, a course or a rule
   table.

**Measured at opening, before any model spend.** The structural half
was verified against JPMorgan's live 10-K (accession
0001628280-26-008131, filed 2026-02-13): the income statement is
located under its own typeset title — one table, 34 rows, periods
2025/2024/2023 — and both concept rows are readable by the row
expansion, "Total net revenue" (182,447 / 177,556 / 158,104) and "Net
income" (57,048 / 58,471 / 49,552), each with the filer's own header
and the "(in millions, except per share data)" caption. No observation
is stored from that check, deliberately: storing one requires the
reading, and the reading is blocked on the same exhausted provider
balance the protocol-11 re-read hit. The first attempt surfaced that
blocker as a worded `invalid_extraction` (the fix above), and the JPM
quorum — the slice's measurement — runs once the account is funded:
`movrvest observe-statements JPM`.

  **The earlier corpus re-read under protocol 10 (2026-08-07, 9
  companies at quorum 5).** What the taxonomy then found, and what it
  no longer did:

  - `description never arrived`: **zero, corpus-wide.**
  - `no description found when asked by name`: VOW3.DE only — one
    company, not a pattern, correctly a frozen backlog entry with its
    cause precisely known (the untagged Lagebericht, finding 2).
  - **The queued applicability slice is un-earned.** JPM's CCB is now
    described, so *description rejected by applicability* reaches META
    alone — one company, below the pattern threshold. The measurement
    that earned it has been superseded by this slice's result, and the
    queue entry is withdrawn rather than kept on momentum.
  - **BNP.PA reached quorum in the re-read** (a held bank, previously
    1/5): three of four segments sized, `financial_spread`, `services`,
    `transaction` and `asset_management_fees` established through CIB
    and IPS — but CPBS, 52% of revenue, has its ways of earning
    unsettled across 5 observations. The Bank-rule case is closer and
    not clean; whether CPBS's disagreement warrants spend or a rule can
    rest on the settled majority engine is the owner's call.
  - The ledger's history begins again at protocol 10 — its stated
    limit, behaving as designed under supersession — and PR #51's
    resolution claim is now surfaced as *unadjudicated*: the pattern it
    resolved lives in history the current schema no longer restores.
    The credit discipline did exactly what it promises: it never
    trusted, and when the evidence base moved, it said so.
- **Stream B — reader quality.** A measured defect list, not a work
  queue. One company is insufficient to unfreeze reader work; several
  foreign private issuers failing for the same structural reason would
  earn the slice. Until then: known, measured, accepted.

  **Reader watchlist:**
  | Symbol | Measured failure | Times |
  |---|---|---|
  | ETOR | grounding contract refused: "the extractor described no business" (foreign-private-issuer filing shape) | 2×, identical, 2026-08-07 |
  | VOW3.DE | *resolved into a document fact by Reader Slice 1*: asked by name, the reader finds no describing words — the tagged note prints tables and accounting boilerplate, verified by inspection of all 6,121 characters | 6 of 6 asked-by-name readings, 2026-08-07 |

  **The taxonomy ran (2026-08-07, `movrvest reader-defects`: 9
  companies scanned, 7 carrying defects, 14 absent claims) and the
  pattern rule returned its verdict — two causes reach two companies
  each and have earned an engineering slice:**

  | Cause | Companies | Claims |
  |---|---|---|
  | description never arrived | JPM, VOW3.DE | 4 |
  | description rejected by applicability | JPM, META | 3 |
  | document points elsewhere for its tables | JPM | 3 |
  | quotes words not in the document | UMI.BR | 1 |
  | no table cell located | BNP.PA | 1 |
  | observations disagree (noise, never a defect) | CAT | 1 |
  | other (no template names it) | NFLX | 1 |

  Total refusals (ETOR's class) store nothing and stay countable only
  on this watchlist — a measurement limit the taxonomy states. The
  earned slices are *not started here*: the verdict is recorded, and
  beginning them is a decision the measurements' owner takes.

  **The defect ledger shipped (2026-08-07, `movrvest defect-ledger`,
  accepted in review of PR #48).** The taxonomy's snapshot became an
  engineering history: the store is append-only and every observation
  is dated, so the ledger *replays* it — after each stored reading it
  derives the consensus that was served at that moment (current
  document by `published_on`, the same `consensus_of`, the same
  `defects_of` classification the taxonomy walks) and records each
  defect pattern's first appearance, last finding, occurrences and
  status. Both design questions closed structurally: the ledger is
  derived on every read from the store alone, and the final replay
  state *is* the taxonomy's answer, so the two cannot disagree; and
  "resolved by PR" is a claim a PR records in
  `app/domain/defect_ledger.py` (`CLAIMED_RESOLUTIONS`, empty until a
  reader slice lands) that the ledger *credits* only while a rerun
  stops finding the pattern — never trusts. A pattern can also resolve
  unattributed (a new filing, or new observations settling a claim),
  and the surface says which happened.

  **First replay (2026-08-07, 9 companies): 20 defect instances ever,
  14 still found — the taxonomy's exact 14.** The six historical
  instances no rerun finds are five *observations disagree* — JPM's
  segment frame, META's Reality Labs, NVDA's Graphics, UMI.BR's frame
  and its Recycling earning — and one *description never arrived*
  (JPM's Commercial & Investment Bank earning), every one of them
  resolved by nothing but more observations: width absorbed them, the
  consensus architecture doing precisely what it was accepted to do.
  Disagreement is thereby the costliest pattern the store has ever
  carried (6 claims ever) *and* the one needing no engineering — 5 of
  its 6 resolved by width alone, and only CAT's remains open. The
  history the snapshot could never show is exactly this column.

  **Reader Slice 1 executed (2026-08-07, approved by the owner):
  *description never arrived* fell 4 open claims → 0, and the causal
  chain's prediction was tested and failed at its first link — which
  is the finding.** The slice: a segment whose description arrives
  with no words is now *asked about once, by name* — a closed,
  one-field question held to the identical applicability contract and
  recorded like a repair, overturning the leave-it-as-it-arrived rule
  the measurement had falsified (on JPM's 10-K, readings found words
  intermittently that the focused question then judged honestly).
  Asked by name, the reader returned empty for every targeted segment
  in every new reading — JPM to 9 observations, VOW3.DE to 11 — and
  the absence now carries the stronger cause: **no description found
  when asked by name**, a fact about the text read, not about the
  reader. Two supporting facts, verified before the spend: JPM's Item
  1 names its segments once and states their descriptions are
  *included elsewhere* in the 10-K (the same pointer shape as its
  sizes), and VW's tagged note is 6,121 characters of accounting
  boilerplate and tables with not one describing sentence. JPM's CIB
  also *lost* a phantom description — the segment-listing sentence,
  carrying no way of earning — which the closed question declines to
  reach for; total absent claims rose 14 → 15 because the platform now
  claims less and says why.

  **The prediction's verdict: grounded authoritative playbooks
  (portfolio) 2 → 2, unchanged.** The chain reader → grounded
  descriptions → mechanisms → understanding → playbook → KPI broke at
  link one, for a measured reason: the descriptions are not in the
  text this platform reads. Per the constitution's own rule, that
  failed hypothesis names the next bottleneck instead of patching
  around it — and the taxonomy's pattern rule now returns it as
  earned: *no description found when asked by name* reaches JPM and
  VOW3.DE (5 claims), so the earned slice is **reading the part of
  the document that describes the segments** (JPM: the exhibit its
  Item 1 and Item 7 both point into; VOW3.DE: the untagged
  management-report narrative). Recorded, not started — the owner
  decides.

  **Still queued, awaiting the owner's go:** the second earned reader
  slice — *description rejected by applicability* (JPM, META), JPM
  the regression case.

- **Stream C — authority.** The highest-leverage spend after Phase A:
  holdings at width 1 are four observations from an authoritative
  conclusion, and every observation upgrades a company already in the
  portfolio. Ranked by expected investor value, not mechanically:
  does quorum unlock a new authoritative playbook, a new grounded
  pattern, a meaningful holding, a more diverse grounded corpus?
  Every observation spend answers "does this increase authoritative
  investor understanding?" — and where it does not, the spend
  justifies itself or is not made.

  **Measured so far:** VOW3.DE reached quorum first (before the
  ranking was revised) and unlocked nothing — its 2025 annual report
  settles sizes and describes no segment, a finding now on the reader
  watchlist. The spend still bought the reclassification of VOW3.DE's
  blocker from *below quorum* to *no revenue mechanisms established*:
  an authority problem became a measured reader problem, which is what
  keeps the streams honest. BNP.PA is deliberately queued last: its
  quorum cannot unlock authority until a 'Service business' rule is
  earned, so its observations buy confidence, not authority.

**Portfolio and watchlist are no longer one optimisation problem.**
Holdings steer investor decisions and deserve confidence — the 1→5
trust investment. Watchlist companies support discovery and mainly
need enough understanding to be found — the 0→1 coverage investment.
The funnel KPI carries a headline for the number that now matters
most: **grounded authoritative playbooks in the portfolio**.

The measurements choose these investments. The platform stopped
telling us what to build and started telling us where to spend model
calls; the roadmap follows the report, not a predetermined phase plan.

## Agreed order

1. ~~**Crypto symbol resolution.**~~ Done. `BTC`, `ETH`, `SOL`, `ADA`, `ARB`
   and `1INCH` now price and carry measured risk. `TAO` and `HYPE` have no
   plain `-USD` listing and stay absent rather than guessed at.
2. ~~**The `strengths` mislabel.**~~ Done. `DecisionEvidence.strengths` and
   `ExecutiveDecision.key_strengths` are now `evidence_weighed`, and carry
   only what was read about the security. The brief's remaining sections say
   whose strengths they are. The claim that the brief printed "Insufficient
   quality data." under **Strengths** was wrong: those sections are built by
   `InvestmentThesisBuilder` from portfolio and market assessments and never
   contained company evidence.
3. ~~**The portfolio-fit gate.**~~ Settled: it measured the wrong thing, and
   both its terms ran backwards. The 47 was `mean(9 positions / 20, policy
   alignment 0.50)` — the account marked down for holding too few positions
   and for sitting in cash against a 5% target, with both marks then used to
   refuse the only action that would fix either. `PortfolioFit` now measures
   the room this portfolio has for this security: funding room from the cash
   target, concentration room from the single-position limit. VOW3.DE and
   NOVO-B.CO are the platform's first RECOMMENDs.

## Settled: the market does not gate a decision, and must not yet

`DecisionEvidence` carries no market score, and this is the decision not to
add one. It was examined because the market currently reaches the Artificial
CIO only as one third of an evidence-confidence average and as context
strings that are identical under every symbol.

**What the market evidence actually is.** `MarketAnalyst` produces two
scores from one day's `change_percent` across the nine instruments
`YahooMarketProvider` prices. `momentum_score` is that day's average move
rescaled linearly, −5% to 0.0 and +5% to 1.0; `volatility_score` is the
average *absolute* move over 5%. There is no window and no baseline: a
broad −3% day scores 0.200 momentum, a flat day 0.500. Neither score
reaches `DecisionEvidence` at all — both are consumed inside the analyst to
pick a `trend` and a `regime`.

**The route that does reach the CIO carries no market information.**
`MarketAssessment.confidence` is one third of the cognitive average inside
`DecisionEvidenceBuilder._evidence_score`, and `evidence_score` is gated
three times, at 30, 60 and 75. But that confidence is
`sample_confidence × 0.60 + consistency × 0.40`, where consistency is
`1 − | |momentum − 0.5| × 2 − volatility |` — which is exactly 1 whenever
the instruments all move together, whatever they do. A flat market and a
market in which every instrument fell 8% both produce confidence 0.940.
Across 200,000 sampled dispersed nine-instrument days the whole term spans
0.549 to 0.940, which moves the cognitive average by 13.0 points and
`evidence_score` by at most 6.5. So the market already moves a gate, by a
route nobody chose, in proportion to how *uniformly* the instruments moved
rather than to what the market did.

*(Those figures are computed from this repository's own code, not observed
against a live account.)*

**Update (2026-08-04): the dispersion term is gone.**
`MarketAssessment.confidence` now measures how well evidenced the reading is
— how much of the panel priced, and how much of it carries the year-long
`realized_volatility` — not cross-sectional dispersion. A flat market and one
down 8% across the board now read the same confidence, because direction is
the trend's and the regime's, not the reading's trustworthiness. It still
reaches `evidence_score`, but as a reading's trustworthiness rather than as a
market-direction term nobody chose.

**Why no market score should be added on this evidence.**

1. **It cannot separate one security from another.** Any market score is
   the same for every symbol in a cycle. Every gate the CIO holds today
   rests on a per-security measurement — quality, valuation, risk, fit —
   and this repository has spent commit after commit removing scores that
   were constant under every symbol: fit was `mean(9 positions / 20, policy
   alignment 0.50)`, a constant 47; quality fell back to the portfolio's
   health score; risk *was* the portfolio's risk score. A market gate
   reintroduces exactly that shape under a name that sounds per-security.
2. **What would make it per-security is not measured.** A market gate is
   only about *this* security if the platform knows how exposed this
   security is to the corner of the market that moved. Nothing measures
   that. `MarketBreadthService` classifies corners and `AssetClass`
   classifies securities, but sharing a label is not exposure — no beta, no
   correlation, nothing regressed against anything. **Update (2026-08-04):
   now measured.** `market_sensitivity` regresses each security's year of
   returns on the benchmark's for a beta and the correlation beside it, so
   exposure is a number per security and reaches the CIO as evidence on the
   security's `RiskSignal`. This removes the "cannot separate one security
   from another" objection — the remaining blockers are the two below.
3. **The evidence is one day deep.** Both scores come from a single day's
   change. The market archive has only just started recording, so there is
   no history to calibrate against yet — and note the analyst does not use
   `MarketQuote.realized_volatility`, which the platform already measures
   over a year per instrument and which is the honest volatility figure it
   holds.
4. **No threshold could be justified.** Every existing gate number is a
   judgement, but each sits on a measurement whose meaning is established:
   an annualised volatility band, a valuation band, room against a stated
   policy limit. For "the market must read at least X before this security
   may be recommended", nothing establishes X. No decision has yet been
   scored against its outcome, so there is no evidence base to calibrate
   one — the number would decide real recommendations with nothing behind
   it.
5. **It is market timing, and that is outside the stated purpose.** A score
   identical for every symbol cannot rank securities. It can only move
   every case up or down together, which is a judgement about *when* to
   act rather than about *what is worth owning*. "Its purpose is not to
   predict markets."

**What has to exist first, in this order.**

- [x] Make `MarketAssessment.confidence` mean how well evidenced the market
      reading is. **Done (2026-08-04).** It measures panel breadth and how
      much of it carries the year-long volatility figure, not cross-sectional
      dispersion, so it no longer moves a gate by how uniformly the
      instruments happened to move.
- [x] Measure a security's exposure to the market, from the year of daily
      closes the quote request already fetches. **Done (2026-08-04).**
      `market_sensitivity` (beta and correlation against the benchmark) rides
      `MarketQuote` to `CompanyFacts` and is reported on the security's
      `RiskSignal`, so a market reading now bears on one security more than
      another.
- [ ] Accumulate market history, now that `MarketSnapshotArchive` records
      it, so a market reading can be placed against its own past rather
      than read as a single day
- [ ] Score decisions against their outcomes, so any proposed threshold can
      be calibrated rather than asserted

Two of the four now hold. Until the remaining two do — market history deep
enough to place a reading against its own past, and decisions scored against
their outcomes so a threshold can be calibrated rather than asserted — the
market stays what it honestly is: context stated beside the decision,
per-security exposure weighed as evidence, and a movement reported in the
change feed. It does not gate.

## Evidence quality

- [x] Portfolio-level drawdown is measured from the account's own equity
      curve. `PortfolioHistoryService` reads eToro's `/balances/history`,
      `PortfolioDrawdownService` measures the fall, and `PortfolioPerception`
      carries it onto the snapshot for `RiskAnalyst` — absent only when the
      history is unreachable, which is reported as unmeasured, not zero
- [x] `portfolio_fit_score` measures this security against this portfolio.
      `OpportunityAssessment.portfolio_fit_score`, which described only the
      account, is now `portfolio_readiness_score`
- [ ] Fit reads 99 for every candidate today — not by construction any
      more, but because a 97%-cash account with no position above 0.5% has
      near-full room for all of them. It will separate them once positions
      grow; nothing yet proves that on live data
- [x] Asset-class room is part of fit, for the one class the policy caps.
      Stock and ETF targets are targets to rebalance toward, not ceilings a
      new position can breach, so they are not scored as room
- [x] Every reading carries a `Provenance` — its source and the time it
      was taken. A cached quote keeps the time the price was taken, not the
      time it was served
- [x] The age is stated on the brief and the research page, coarsely —
      "14 minutes ago", not a timestamp implying precision the number
      lacks. `Provenance.is_older_than` lets a caller set its own limit;
      no gate rejects on age yet, and none should until a real one is
      identified
- [x] eToro identity carries a reading. The watchlist fetch stamps the
      moment it returns, `WatchlistItem` carries that `Provenance`, and
      `CompanyFacts.identity_reading` holds it beside the price and
      fundamentals — the other half of two-source provenance. A stale
      identity ages the whole object, since `observed_at` now takes the
      oldest of all three
- [x] A degraded source is named. `Provenance.last_known` marks a reading
      served because its source failed, and `least_reliable` surfaces it
      ahead of a merely older one — a last-known reading keeps its original
      time, so it can be newer than the price beside it
- [x] Crypto tickers resolve. `AssetClass` classifies an eToro instrument,
      and a crypto one is priced as a pair
- [ ] `TAO` and `HYPE` have no plain `-USD` listing on Yahoo. Both are
      reported unpriceable rather than guessed at under a disambiguated
      ticker
- [x] A crypto case says why it cannot progress: the platform judges on
      business quality and valuation, which a token has neither of. Stated
      as this platform's limit, with the gates unchanged
- [x] `CryptoFearGreedProvider` reads Alternative.me rather than returning
      a hardcoded 72 under that service's name
- [x] Crypto is assessed on token fundamentals — network value, turnover,
      issuance and age — read from the provider call already being made
- [ ] Crypto valuation stays absent. There are no earnings to price
      against, and exchange volume is not on-chain volume, so an NVT-style
      ratio would be a metric invented rather than measured. A crypto case
      therefore stops at PREPARE
- [x] Holdings absent from every watchlist are described by the broker's
      own catalog. `/api/v1/market-data/instruments?instrumentIds=…` is
      the same source the position comes from, so asking it for the
      symbol, name and type of a held-but-unwatched instrument is a
      measurement, not a guess. `InstrumentSymbolResolver.items_for`
      asks it once per cycle, only about the ids the watchlists miss;
      both perceptions use it, so such a holding is now named,
      classified and evidenced like any other (proven live: eToro id
      1238 was `#1238`, 0.2% unclassifiable — it is now BNP.PA, a
      stock, evaluated by the CIO on its own Yahoo record). An id the
      catalog does not return, or a catalog that cannot be reached,
      degrades to the placeholder and the worded "cannot classify"
      line — the same honest absence as before the fallback existed
- [ ] Research still evidences a capped number of candidates per cycle. With
      the cache warm the cap could rise substantially; the first cycle of a
      day is what costs
- [x] Holdings are classified by asset type. `PortfolioPerception` joins
      the watchlist instrument onto each position, `PortfolioService.allocate`
      splits the invested share by class, and the crypto ceiling is scored
      in both `BehaviorAnalyst` and `PortfolioFit`

## Reasoning

- [x] `movrvest evaluate SYMBOL` and `GET /executive/{symbol}` evidence the
      symbol they are asked about. `BrainBuilderService.build` takes
      `focus_symbols`, which `SecurityPerception` evidences whatever the
      candidate budget says. Both paths now return REJECT for UUUU, where
      the CLI returned INVESTIGATE and the research pipeline REJECT
- [x] `InvestmentThesis.conviction` carries the decision's own conviction
      to the brief and to `GET /executive/{symbol}`, beside the committees'
      agreement rather than in place of it
- [x] `CommitteeOpinion.confidence` is `float | None`. A committee that
      could not form a view is excluded from agreement rather than averaged
      in as a zero, and confidence comes from the assessments' own
      confidence rather than from how bullish the view is
- [x] `InvestmentCommittee` and `RiskCommittee` review one investment case.
      `CommitteeService.review` takes the symbol, `Brain.security_evidence`
      is the single accessor both use, and a committee with nothing to go on
      abstains rather than opining on the account
- [x] A security no watchlist names is told apart from one that was looked
      at. It still draws no committee view — `InvestmentThesis.confidence`
      stays None — but the Artificial CIO no longer says "business quality
      has not been measured", which promised a reading of a security the
      platform never fetched. `DecisionEvidence.security_evidenced` is false
      when the Brain held nothing about the symbol, and the CIO states that
      plainly: "No security-level analysis is available for X." It asserts
      the fact, not the cause — a fetch may have failed rather than the
      symbol being unknown. Analysing an unevidenced symbol from Yahoo alone
      is a larger, separate step, and this does not attempt it
- [ ] Signal evidence has no polarity, so favourable and adverse findings
      cannot be told apart. `InvestmentThesis.strengths` and `.risks`
- [x] Signal evidence carries polarity. `Finding` pairs each statement
      with the `Sense` the signal read it with, so `InvestmentThesis`
      states the security's own strengths and risks, and the portfolio and
      market keep `context_strengths` and `context_risks`
- [ ] `consistency_score` needs a record of the investor's own actions. The
      decision journal records the CIO's decisions, not what the investor did
      with them
- [x] Decisions are scored against what the security did next.
      `DecisionOutcomeService` joins the journal to a year of daily closes;
      a decision must stand 30 days before its move counts, MONITOR and
      INVESTIGATE are not calls and are never scored as ones, and a hit
      rate is withheld below 10 measured calls. The journal is young, so
      the honest reading today is 61 decisions and 0 outcomes
- [x] `app/analysts` is wired into the canonical decision. `ValueProvider`
      reads the growth, margins, balance sheet and cash flow already in the
      one `.info` call it makes; `CompanyFactsService` carries them; and
      `CompanySignalService` runs the four analysts for a company and attaches
      the research to `CompanySignals`. Each verdict reaches the case as
      weighed evidence on the decision, the way risk and sensitivity do — not
      as a gate, until it can be calibrated

## Delivery

- [x] API routes can be tested without the network. The network-coupled
      composition roots (`BrainBuilderService`, `BrainSnapshotService`,
      `AccountService`, `BriefService`, `MarketPerception`,
      `DashboardService`) are FastAPI dependencies now —
      `app/api/dependencies.py` — so a test overrides them through
      `app.dependency_overrides` and exercises the route offline. Proven in
      `tests/test_api_routes.py`: `/brain/` serialization including the
      null-vs-zero honesty, `/executive/{symbol}` over real offline
      reasoning (and its unevidenced-symbol wording), the
      `/executive/portfolio` 404 branch that no test could reach before,
      `/portfolio/` over the real `PortfolioService`, `/api/today`,
      `/market/` over the real `MarketBreadthService` (with the VIX,
      reading and sentiment served as null when unread), `/research/candidates`,
      and `/dashboard/`. Every route that reached for the network is now
      injectable; `BrainBuilderService.build` takes the candidate budget as
      a per-call argument so the research route needs no second service.
- [x] The change feed reports market and macro movements. Every observation
      is recorded through the same `VersionedSnapshotStore` the eToro
      responses go to, and `MarketChangeService` reports the mood, the
      volatility band and the sentiment label that moved between the last
      two. An individual instrument's move is reported now as well, where it
      is large *for that instrument*: each quote carries a year of realised
      volatility, so a day's move is judged in multiples of the instrument's
      own typical daily move rather than against a threshold nothing measured.
      A move on an instrument whose history was too short to measure a typical
      one for is still not reported — there is no scale to judge it against
- [x] A benchmark move says which holdings it touches, and how much. The
      `/executive/portfolio` feed carries each holding's measured
      `market_sensitivity` beside its share of the account, so a named SPY
      move states who rides it — ordered by weight × |beta|, correlation
      shown so a line fitted through noise is visible — and counts the
      holdings nothing was measured for, so the line never reads as "the
      rest are untouched". Any other instrument's move says nothing about
      holdings: a beta to SPY says nothing about an oil move, and a book
      with no measured sensitivity anywhere gets no holdings line at all,
      because even which instrument it would move with is unmeasured
- [x] `ExecutivePipeline` reasons the account once per cycle. The portfolio,
      market and risk assessments do not depend on the security being judged,
      so `execute_all` reasons them once and shares the one `ReasoningSnapshot`
      across every holding, rather than repeating three analyst passes per name

## Structure

- [ ] `app/services` (66 modules) still mixes load-bearing and incidental
      code
- [x] Analysts reason over a `Brain` and nothing else. The portfolio,
      market, risk and behaviour analysts were narrowed from
      `Brain | BrainContext` to `Brain`, their dead `BrainContext` branches
      removed, and the legacy `app.domain.brain_context.BrainContext`,
      `app.domain.market_context.MarketContext` and the unused
      `CommitteeMember` protocol deleted — the domain `BrainContext` was
      never constructed, only ever accepted as a type
- [x] `ClaimEngine` and its test are deleted. The test carried pre-existing
      TypeScript errors (`vitest` was never installed), and `ClaimEngine.ts`
      was imported by nothing but that test — a dead module. The honest fix
      was to remove the pair, not install a runner to test code the app does
      not use. (The rest of `lib/acio` and `lib/investor` outlived this note
      by one mission: the UX migration proved the whole frontend reasoning
      engine reachable only through an unmounted onboarding mock and deleted
      it — see below.)
- [x] The frontend UX/UI Alignment mission is complete (PRs #8–#16, August
      2026). The dead dashboard generation, the fabricated `/briefs` route,
      the frontend reasoning engine (`lib/acio`, `lib/investor`) and every
      frontend banding function are gone; navigation matches the product
      model with `/track-record` as its last screen; the frontend calculates
      no investment meaning. The audit and slice-by-slice log live in
      [`docs/frontend/UX_UI_INVENTORY.md`](../frontend/UX_UI_INVENTORY.md).
- [x] `docs/` is indexed and the superseded documents are quarantined.
      [`docs/README.md`](../README.md) names the current set and the one
      reference doc; the ~20 older documents moved to `docs/archive/` (with
      its own README mapping each to what replaced it), and the two iCloud
      `architecture` conflict copies were deleted. `CLAUDE.md` and the root
      `README.md` point at the index.

---

# Success Metrics

## Architecture

- One implementation per concept
- No duplicate pipelines
- One-way dependency graph

## Product

Every executive recommendation can answer:

- What changed?
- Why?
- Why now?
- What should I do?
- Why should I trust this?

---

# North Star

```
Reality
    ↓
Evidence
    ↓
Brain
    ↓
Analysts → ReasoningSnapshot
    ↓
Executive Committee → CommitteeOpinion
    ↓
DecisionEvidence
    ↓
ArtificialCIO → ExecutiveDecision
    ↓
InvestmentThesis
    ↓
ExecutiveBrief
    ↓
Executive Workspace
```

No parallel paths. No duplicate ownership. No ambiguity.

End of document.
