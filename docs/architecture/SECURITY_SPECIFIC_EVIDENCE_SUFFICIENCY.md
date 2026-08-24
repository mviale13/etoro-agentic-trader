# Security-Specific Evidence Sufficiency

**Status: research. Conclusion B — typed coverage ready, decision
mapping not ready.** No production code, no provider or model calls, no
funded cycle. Measured offline against the held corpus at cycle
`d98cf859932e`, main `3779126`.

The owner principle this measurement serves:

> Companies will not have equal information coverage. Missing
> information must constrain what the system can claim, but must not
> become evidence that the company is poor. Every security should still
> receive the most honest course supported by what is available.

---

## Stage 1 — what `evidence_score` actually measures

`evidence_score = (cognitive_confidence + vote_confidence) / 2`, where
`cognitive_confidence = (portfolio + market + risk) / 3` — **85 for
every security in the book, containing no security-specific content at
all** — and `vote_confidence = 50 + |vote| × 50`, which rises with
distance from neutral **in either direction**.

So the only security-specific term in the platform's measure of how
well a security is evidenced is *how far its three bands are from
neutral*.

### The corpus

| symbol | role | facts | quality read | vote \|s\| | evidence | state |
|---|---|---|---|---|---|---|
| AAPL | large control | 7/18 | 1 of 3 | 0.40 | 77 | INVESTIGATE |
| MSFT | large control | 18/18 | 3 of 3 | 0.60 | 82 | PREPARE |
| DIS | capital-asking | 18/18 | 3 of 3 | 1.00 | **92** | RECOMMEND |
| BNP.PA | capital-asking, foreign | 15/18 | 3 of 3 | 0.50 | 80 | RECOMMEND |
| AMD | repaired candidate | 18/18 | 3 of 3 | 0.65 | 83 | PREPARE |
| UUUU | repaired candidate | 17/18 | 3 of 3 | 1.00 | **92** | INVESTIGATE |
| UDMY | sparse control | **0/18** | 0 of 3 | 0.00 | **67** | INVESTIGATE |
| SPCX | coverage-gated vote | 15/18 | 2 of 3 | 0.65 | 83 | INVESTIGATE |
| NESN.ZU | foreign issuer | 18/18 | 2 of 3 | 0.40 | 77 | INVESTIGATE |
| ETOR | grounded example | 17/18 | 2 of 3 | 0.15 | 71 | INVESTIGATE |
| VOW3.DE | foreign, grounded | 18/18 | 2 of 3 | 0.15 | 71 | INVESTIGATE |
| NOVO-B.CO | foreign, grounded | 18/18 | 2 of 3 | 0.15 | 71 | INVESTIGATE |
| CYD | provider-only | 13/18 | 3 of 3 | 0.15 | 71 | PREPARE |
| AZN | provider-only | 18/18 | 3 of 3 | 0.75 | 86 | RECOMMEND |
| GRE.MC | foreign, provider-only | 17/18 | 3 of 3 | 0.20 | 72 | INVESTIGATE |

**The row that settles it: UUUU scores 92 — the joint highest evidence
score in the corpus, tied with DIS.** UUUU earned zero of three quality
points; DIS earned three of three. UUUU's maximum evidence score comes
from having a maximally negative vote.

### The six required demonstrations

**1 + 2 — same coverage, different momentum direction and magnitude.**
Only the momentum band is varied; every fact and every other band is
held identical.

| | BULLISH | NEUTRAL | BEARISH | coverage |
|---|---|---|---|---|
| MSFT | ev **82** | ev **76** | ev **70** | unchanged: 18 facts, 3 of 3 |
| AAPL | ev 71 | ev 77 | ev **83** | unchanged: 7 facts, 1 of 3 |
| DIS | ev 92 | ev 86 | ev 80 | unchanged: 18 facts, 3 of 3 |
| AMD | ev 71 | ev 77 | ev 83 | unchanged: 18 facts, 2 of 3 |

**18 of 18 securities change evidence score on the momentum band
alone.** MSFT spans 70–82 across the 75 recommendation gate. The
direction is not even consistent: a bullish MSFT gains evidence, a
bullish AAPL loses it — because AAPL's other bands sit on the opposite
side of neutral. Nothing about what was read moved in any row.

**3 + 4 — more and less evidence at identical directional readings.**
**29 ordered pairs exist where the security holding more facts scores
lower evidence.** Representative:

| better-scored | facts | evidence | | worse-scored | facts | evidence |
|---|---|---|---|---|---|---|
| AAPL | 7 | 77 | beats | VOW3.DE | 18 | 71 |
| AAPL | 7 | 77 | beats | NOVO-B.CO | 18 | 71 |
| AAPL | 7 | 77 | beats | ETOR | 17 | 71 |
| BNP.PA | 15 | 80 | beats | NESN.ZU | 18 | 77 |

**5 — `DOCUMENT_REFUSED` versus never read versus unavailable.**
Every security in the corpus reads `UNAVAILABLE`. Two separate causes,
both structural, are in section D below.

**6 — provider-only versus grounded.** Indistinguishable in
`evidence_score`: AZN (provider-only, 86) outscores AAPL
(statement-grounded, 77), and the score contains no term that could
tell them apart.

---

## Stage 2 — the existing candidate carriers

### A · `DecisionAuthority.relative_coverage`

Direction-blind and already computed. Takes exactly **three values**
across the corpus — 0.00, 0.67, 1.00 — because it is participation over
three signals.

**Contamination to name**: one of those three signals is *momentum*, so
a security whose price history is unreadable loses coverage for a price
reason. Not magnitude and not direction, so it does not breach the
invariant — but a coverage measure partly counting the availability of
a price series is not a measure of what has been read about the
*business*.

### B · `QualityCoverage.earned / available` — **not a coverage measure**

`earned` is `sum(points)`. It is **performance**, not coverage.
`available` is the number of factors that could be read, which *is*
coverage. The ratio has a performance numerator over a coverage
denominator, and it is **inverted for both controls**:

| | band | earned | available | `earned/available` | `available/expected` |
|---|---|---|---|---|---|
| UUUU | LOW | 0 | 3 | **0.00** — reads as uncovered | **1.00** — fully read |
| AAPL | UNKNOWN | 1 | 1 | **1.00** — reads as fully covered | **0.33** — 1 of 3 read |

UUUU was read completely and failed; AAPL was barely read at all. The
proposed ratio says the opposite of both. **Using it would make missing
information into evidence that the company is poor — precisely the
owner principle this slice exists to protect.**

**`available / expected` is the honest pair**, is already computed, and
discriminates correctly: UUUU 1.00, MSFT/DIS/BNP.PA/AZN 1.00, SPCX and
the UNKNOWN-band foreign issuers 0.67, AAPL 0.33, UDMY 0.00.

This platform has already ruled on this exact confusion once, in
`crypto_quality.py`: *"not knowing what an asset is cannot be a form of
knowing about it."*

### C · Canonical decision-family participation

`ScoreParticipation` carries participating, expected and **named**
absent families — a typed absence, not a hole. Live range 2/5 to 5/5,
and the named absences are already investor-legible (*business
quality*, *valuation*, *safety*).

**Circularity to name**: `evidence` is itself one of the five
`SCORE_FAMILIES`. Deriving `evidence_score` from family participation
makes the measure partly self-referential — the evidence family would
be counted as present because an evidence score was produced.

### D · Source and evidence authority — **typed, and currently blind**

`KnowledgeState` is already exactly the vocabulary the owner asked for:
`AVAILABLE_CACHED`, `AVAILABLE_ACQUIRED`, `UNAVAILABLE`,
`PROVIDER_ERROR`, `INVALID_EXTRACTION`, `DOCUMENT_REFUSED`, with
`may_succeed_later` already separating a retryable failure from a
structural refusal. Nothing needs inventing.

Two measured facts stop it being usable today:

1. **The refusal states are never persisted.**
   `CompanyKnowledgeService.established()` — the read-only door every
   decision path uses — can return only `AVAILABLE_CACHED` or
   `UNAVAILABLE`. `DOCUMENT_REFUSED`, `PROVIDER_ERROR` and
   `INVALID_EXTRACTION` are produced by the *acquiring* path and
   discarded. A search of the whole evidence root finds no stored
   occurrence of any of them. **At the point of decision,
   `DOCUMENT_REFUSED` is indistinguishable from never read.**

2. **The grounded corpus is unreadable pending a funded re-observe.**
   Of 34 stored knowledge documents, **31 are at schema 11 and 2 at
   schema 12 against a current 14**, and there is no cross-schema read
   by design. Exactly **one** company (ALL) has readable grounded
   narrative knowledge. Statement evidence is healthier — 24 companies
   at the current schema 3 — but of the named corpus only AAPL and DIS
   have it.

So the authority axis today would classify essentially the entire book
`UNAVAILABLE` and discriminate nothing.

### E · A typed vector

Carrying C and D side by side, with `available/expected` and fact
breadth beside them, satisfies every invariant without averaging unlike
facts. It is the only candidate that does.

### Invariant results

| invariant | `evidence_score` | A | B (`earned/avail`) | B (`avail/expected`) | C | D | E |
|---|---|---|---|---|---|---|---|
| price direction alone cannot change sufficiency | **fails 18/18** | ok | ok | ok | ok | ok | ok |
| bullish and bearish at equal coverage score alike | **fails** | ok | ok | ok | ok | ok | ok |
| more evidence cannot lower sufficiency | **fails, 29 pairs** | ok | **fails** | ok | ok | ok | ok |
| removing evidence cannot improve sufficiency | **fails** | ok | **fails** | ok | ok | ok | ok |
| account confidence cannot substitute for security evidence | **fails** | ok | ok | ok | ok | ok | ok |
| `DOCUMENT_REFUSED` distinct from never read | **fails** | n/a | n/a | n/a | n/a | **fails (store)** | **fails (store)** |
| provider evidence not promoted to grounded | **fails** | n/a | n/a | n/a | n/a | ok | ok |
| missing evidence never lowers quality/valuation/safety | ok | ok | **fails** | ok | ok | ok | ok |

`evidence_score` fails five of eight. The one measure that fails an
invariant *as a formula* rather than *as a store limitation* is
`earned/available`.

---

## Stage 3 — decision consequences

### Contract 1 · NUMERIC COVERAGE

A security-specific 0–100 coverage number replaces vote confidence;
the 35 / 60 / 75 thresholds are retained. Modelled as the unweighted
mean of fact breadth and `available/expected`.

**One movement across the corpus: UDMY `INVESTIGATE → MONITOR`.** No
capital-asking course lost — DIS and BNP.PA keep RECOMMEND at coverage
100 and 92. No AMD or UUUU regression: AMD holds PREPARE, UUUU holds
INVESTIGATE, and UUUU's evidence falls 92 → 47, which is the defect
being corrected.

Three problems the movement count hides:

- **UDMY's course gets worse, not better.** MONITOR's course is
  `WATCH` — *"there is nothing to act on yet"* — where INVESTIGATE's is
  `RESEARCH`. A company nothing has been read about is precisely the one
  to research. Sparse coverage should cap progression; here it
  redirected the course away from the action that would fix it.
- **Coverage 100 is reachable with an unbandable quality.** NESN.ZU,
  META, VOW3.DE and NOVO-B.CO all score 100 while their quality band is
  UNKNOWN and *business quality* is a named absent family. Averaging
  breadth with `available/expected` produced a number that says "fully
  covered" about securities the decision itself records as missing a
  family. This is the "do not average unlike facts" warning arriving as
  a concrete wrong answer.
- **The thresholds stop meaning what they meant.** 35 / 60 / 75 were
  calibrated against a quantity whose live range is 67–92 and whose
  floor is an account-level 85/2. A coverage fraction has a different
  distribution entirely — mass at 100, a real zero, and a genuine
  spread. Reusing the numbers is not a translation; it is a new policy
  wearing old constants.

### Contract 2 · TYPED SUFFICIENCY

Breadth and authority stay typed; progression is capped by explicit
conditions rather than a synthetic mean. Satisfies every invariant that
is satisfiable today, and preserves the distinction `earned/available`
destroys. **It cannot be completed**: the cap conditions must be able to
say *"the filing was retrieved and the section refused"* separately from
*"nothing has been read"*, and the store does not carry that.

### Contract 3 · HYBRID

A numeric breadth measure travelling beside typed authority and refusal
states, with no averaging between them. Strictly better than 1 — it does
not manufacture NESN.ZU's 100 — and blocked by the same store limitation
as 2.

---

## Answers to the required questions

1. **Which candidate measures breadth rather than direction or
   enthusiasm?** `available/expected` and fact breadth. Not
   `earned/available`, which measures performance. Not `evidence_score`,
   which measures distance from neutral.
2. **Do a bearish and a bullish observation with identical coverage get
   the same result?** Under every candidate, yes. Under `evidence_score`
   today, no — 18 of 18 securities move.
3. **Can a company with incomplete evidence still receive an honest
   course?** Yes, and it already does: UDMY holds INVESTIGATE/`research`
   at zero facts. Contract 1 would demote it to `watch`, which is worse.
4. **Do gaps cap progression without reducing business quality?** They
   can — `available/expected` and family participation are read
   independently of the quality band, and UUUU demonstrates the
   separation (coverage 1.00, band LOW).
5. **Can `DOCUMENT_REFUSED` remain distinct from never read?** **Not
   today.** The vocabulary distinguishes them; the store does not
   persist which occurred, and the read-only door cannot return the
   refusal.
6. **What happens to current states, courses, blockers, convictions?**
   Contract 1: one movement (UDMY), no course lost, no regression, no
   capital-asking course affected. Contracts 2 and 3 are not
   computable end-to-end.
7. **Can a company improve its sufficiency because its price move is
   more extreme?** Under `evidence_score`, yes — that is the defect.
   Under every candidate, no.
8. **Does the measure work across large US, smaller, foreign and
   provider-only securities?** `available/expected` and family
   participation do: they discriminate AAPL 0.33, foreign issuers 0.67,
   fully-read securities 1.00, UDMY 0.00, without reference to domicile
   or size. The **authority** axis does not work today, because 97% of
   the grounded corpus is unreadable.
9. **Is a numeric score still justified?** Partly. A single 0–100
   number is defensible for *breadth* alone. It is not defensible as a
   blend of breadth with authority: NESN.ZU's 100 beside a named absent
   family is what that blend produces. **Typed coverage plus an explicit
   course ceiling is the more honest shape.**

---

## Conclusion — B · TYPED COVERAGE READY, DECISION MAPPING NOT READY

**What can be carried safely today**, all already computed and all
direction-blind:

- `QualityCoverage.available / expected` — factors readable over
  factors expected.
- Security-specific fact breadth over a named field set.
- `ScoreParticipation` — participating, expected and **named** absent
  families.
- `KnowledgeState` as the authority type, carried without being
  averaged into anything.

**What prevents replacing `evidence_score`, and needs an owner ruling:**

1. **The refusal states are not persisted.** Until the store records
   which of `DOCUMENT_REFUSED`, `PROVIDER_ERROR`, `INVALID_EXTRACTION`
   and never-read occurred, no consumer can honour the invariant that
   they stay distinct. This is a store contract change, not a formula.
2. **The grounded corpus is 31-of-34 unreadable** against the current
   knowledge schema, so the authority axis cannot discriminate until a
   funded re-observe repopulates it.
3. **The 35 / 60 / 75 thresholds have no defensible meaning against a
   coverage fraction.** They were fitted to a confidence blend with a
   67–92 live range. Re-using them silently would be a policy change
   presented as a refactor; setting new ones is a policy decision.
4. **`evidence` is one of the five score families**, so a
   participation-derived evidence measure is partly self-referential.
   Which family set a coverage measure may read needs deciding.
5. **Sparse coverage must cap progression without redirecting the
   course away from research.** UDMY's `research → watch` demotion under
   contract 1 shows the cap and the course are two decisions, and only
   the first belongs to a coverage measure.

**Recommended next slice, pending ruling**: persist the knowledge
outcome state at acquisition so the read-only door can return it, then
re-measure. That is a prerequisite for contracts 2 and 3 and is
independently correct — the platform currently discards, at every
acquisition, the one fact that distinguishes a refusal from a gap.

Nothing here is implemented. No provider or model call was made, no
funded cycle run, and no quality, valuation, safety, portfolio-fit,
allocation or capital-envelope policy was touched.

---

## Owner ruling — 2026-08-24

Recorded on PR #249, against the measurement above.

1. **Conclusion B accepted** — typed coverage ready, decision mapping
   not ready.
2. **`QualityCoverage.earned / available` is rejected as a coverage
   measure**, because `earned` measures *performance*. It is not a
   weaker coverage signal; it is a different quantity.
3. **`available / expected` is accepted** as the existing honest
   breadth pair.
4. **No numeric score and no thresholds are approved.**
5. **The existing 35 / 60 / 75 evidence thresholds have no authority
   over a coverage fraction.** They were fitted to a confidence blend
   and do not transfer.
6. **Breadth, source authority, refusal state and business performance
   must remain separate.** None may be averaged into another.
7. **Missing information may constrain progression and never lowers
   company quality.**
8. **The next prerequisite is durable acquisition-outcome
   persistence.**
9. **No backfill, re-observation or decision change is authorized by
   this ruling.**

---

## Implementation status — the Company Knowledge Outcome Journal

**Built, and it persists facts only.** It replaces no score, moves no
decision, and the slice after it decides how typed breadth and
persisted outcome authority relate to `evidence_score`.

### What the measurement said, and what now exists

The blocker was **not** that the vocabulary was missing. `KnowledgeState`
already carried all six outcomes and already separated a retryable
failure from a structural refusal. The blocker was that four of the six
were computed at acquisition and **thrown away**, so at the point of
decision *a filing whose section was structurally refused* and *a
company nobody had ever looked at* were the same fact.

`KnowledgeAcquisitionEvent` (`app/domain/knowledge_acquisition.py`) and
`KnowledgeOutcomeStore`
(`app/infrastructure/evidence/knowledge_outcome_store.py`) persist it:
append-only JSON Lines, one file per canonical symbol, schema on every
line, following the intelligence journal (#111) by way of the identity
stream (#216).

### Two dimensions, never collapsed

`knowledge_usable` and `state` are separate fields because one boolean
cannot hold both halves. Pinned: a **provider error with last year's
knowledge** and a **document refusal with older knowledge** both record
`knowledge_usable=True` beside a non-available state, and
`had_prior_knowledge` names that pair.

### `KnowledgeState` is not overloaded

`observe()` legitimately ends `AVAILABLE_ACQUIRED` when some
observations were taken and a later extraction was refused — the
knowledge is real *and* the run ended in a refusal. No single state can
say both, so `ended_in_refusal` carries the second half beside the
state rather than inventing a seventh member that would be a lie in the
other direction. This is why the attempt is a separate typed object.

### Ordering and durability

The knowledge write lands first; the event appends last. There is **no
`try/finally`** on the acquisition path, deliberately: a hard kill must
produce *no* terminal event rather than a manufactured one. Pinned by a
test that kills the process between the two writes and asserts the
knowledge survives usable while the journal stays empty.

### Who owns persistence, and who merely reaches it

**Persistence is owned by the two service doors** —
`CompanyKnowledgeService.knowledge()` and `.observe()` append exactly
one terminal event each, inside the door itself. The callers below are
the production paths that currently *reach* those doors; they own
nothing, and a future caller cannot bypass persistence except by
deliberately calling the service's private internals:

| current caller | command |
|---|---|
| `app/commands/knowledge.py:35` | `movrvest knowledge SYMBOL` |
| `app/commands/understanding.py:24` | `movrvest understanding SYMBOL` |
| `app/commands/archetype.py:26` | `movrvest archetype SYMBOL` |
| `app/commands/observe.py:25,27` | `movrvest observe SYMBOL` |
| `app/services/playbook_selection_service.py:57` | `movrvest playbook SYMBOL` |

**`established()` remains the non-appending read-only door. A page
view is not an attempt:**

| call site | surface |
|---|---|
| `app/services/company_understanding_service.py:107` | the per-security dossier |
| `app/services/company_research_service.py:135` | Research |
| `app/services/stored_playbook_selection.py:58` | the grounded playbook selector |

Pinned by a test that calls `established()` three times and asserts the
journal, the source resolver, the document fetch and the model are all
untouched.

### Safety

**No raw provider or extraction message is ever persisted** — only the
exception *class*. Those strings are composed by libraries this platform
does not control and have carried API keys, signed URLs, account
identifiers and document fragments. A document refusal is the one
retained wording, and it is not an exception: it comes from
`business_refusal.stated()`, a typed carrier this platform composed.

Pinned with a seeded failure carrying an API key, a URL query, an
account identifier and a document fragment, asserted absent from disk on
both the provider and the extraction path, plus a test that the
document's own words never enter the journal.

### Read contract

`KnowledgeOutcomeHistory` returns decoded events, an unreadable count,
an unsupported-schema tally and `is_complete`. **`latest` returns `None`
where the history is incomplete** — with a line missing, the newest
readable event may not be the newest event. Unknown schemas and
malformed records are counted apart and never pooled.

**A corrupt outcome history does not erase usable company knowledge.**
It prevents a complete claim about the acquisition lifecycle, not a
claim about the company; the two live in different stores, and a test
ruins the journal and asserts the knowledge still serves.

### The fail-closed amendments (owner, 2026-08-24)

Corrected before merge, each with its own pin:

- **Provenance**: the canonical field is `PrimarySource.published_on`.
  The first cut probed a nonexistent `.published` through `getattr`, so
  every event recorded an empty date; the helper is now typed against
  `PrimarySource`, a production-shaped control asserts the exact ISO
  date, and an AST test bans any `.published` access on the path.
- **Strict decoding**: a current-schema malformed record is unreadable,
  never repaired. No `bool()`/`int()`/`str()` coercion — the decisive
  case is `"knowledge_usable": "false"`, which a coercing reader
  inverts to `True`. Twelve bends pinned, each against an unbent
  control line; a boolean schema value is never schema 1.
- **Construction invariants**: available ⇒ usable; usable ⇒ positive
  observations *and* a usable source key; unusable ⇒ neither; a
  refusal-ended attempt and a document refusal each carry a non-empty
  safe reason. No measured path contradicted any of them.
- **Symbol and path identity**: the event normalizes its symbol once at
  construction and validates it against `SAFE_SYMBOL`; a decoded row
  whose symbol is not the requested canonical symbol counts as
  unreadable, never pooled; `../DIS`, `A/B`, NUL and whitespace-only
  are refused before any path exists, with a containment assertion,
  while `NESN.ZU`, `VOW3.DE` and `NOVO-B.CO` round-trip; nothing is
  encoded, so two symbols cannot collide on one file.
- **Prior knowledge on every non-available path**: the no-reader
  `observe()` and the observe-path `INVALID_EXTRACTION` now record
  last-known knowledge exactly as every other non-available terminal
  does, at zero provider and model cost.
- **`attempted_at` means attempted-at**: the clock is injected and read
  before the funded body begins; the append still happens only after
  the outcome is known, so a killed attempt carries its captured time
  nowhere.

### Boundaries held

No backfill — a fresh installation starts empty, and an old-schema
knowledge document that cannot be restored is **not** recorded as a
document refusal. The company-knowledge observation schema is unchanged
and the 31 stale grounded documents were not re-read. No scheduler, no
retry policy, no funded cycle, and no provider or model call in
acceptance. `KnowledgeState` moved to `app/domain/knowledge_state.py`
to break an import cycle and is re-exported unchanged, so every existing
import keeps working.

Guarded at the import graph: nothing in the decision path references the
journal, and the journal references no decision object.
