# The Crypto Dossier — the first investor-usable crypto surface

**Status: built, read-only, decision-neutral.** The surface that makes
eleven slices of crypto analysis usable by an investor, so that further
backend architecture can be driven by product feedback rather than by
design.

Not a redesign of the analytical backend, and not a visual-polish
exercise. It exists to be *used*, and to find out what is useful,
confusing, missing or wrongly emphasised.

---

## 1. The audit, and the failure it found

Five crypto sections already reached the equity dossier — the archetype
playbook, supply, protocol fundamentals, token facts and market context
— with adapters and strict parsers.

**And the page around them was answering crypto questions in equity
vocabulary.** `GET /executive/BTC/dossier` today leads with:

```text
decision_state  INVESTIGATE
conviction      46  "Low Conviction"
agreement       0.5
safety          35
portfolio_fit   36
committees      Investment Committee, Risk Committee
```

None of that comes from any crypto evidence. Meanwhile Fee Capture,
Supply Governance, the investor assessment, Asset Quality, the
intelligence layer and the journal appeared **nowhere**. A token was
being rendered as a company with different labels — the failure
`DossierDefinition` prevents one level up, recurring one level down.

Six layers had reached the CLI and stopped there: Investor Assessment
(#117/#119), the committee matrix (#115/#116), Asset Quality (S5),
Crypto Intelligence and events (#108–#110), the Intelligence Journal
(#111) and mechanical issuance (#106).

---

## 2. The measurement that decided the design

| composition | time |
|---|---:|
| `GET /executive/{symbol}/dossier` (runs the brain pipeline) | **~12 s** |
| every crypto layer, read-only, composed | **~19 ms** |

That is not a performance note; it is the shape of the thing. The equity
dossier composes a *decision*, and a decision needs the pipeline. The
crypto dossier composes what is *known*, and nothing in it decides
anything. So it is its own endpoint — `GET /crypto/{symbol}/dossier` —
reusing the five existing adapters and the two domain objects that
already serialise themselves, and adding four small adapters for the
layers that had no wire shape.

---

## 3. The one hard rule, and where it is enforced

> **The frontend calculates nothing analytical.**

No financial value, score, applicability, interpretation, classification
or verdict is recreated in TypeScript, and there is no fallback prose
that turns a measurement into economic meaning. Every sentence arrives
worded: applicability from the archetype, meaning from the licensing
contract, verdicts in each committee's own words, spans from the
journal's own `stated`.

Enforced in three places:

- **The adapters** carry the domain's sentence beside every state, so
  there is never raw material a client would have to interpret.
- **The parser** (`lib/api/crypto-dossier.ts`) requires those sentences.
  A missing one is an error, not a default — a page that quietly
  substituted a friendly string would be Zero Fake Meaning's frontend
  failure mode.
- **The page** renders the refusal where the backend declines to
  interpret. HYPE's supply figures carry a licensed reading; a
  stablecoin's would carry the refusal, and the page has no third
  branch.

**Three things the payload does not contain**, checked by a test that
walks every key at every depth: no aggregate, no agreement, no score, no
ranking, no conviction, no recommendation.

---

## 4. Does it actually change with the asset?

The owner's acceptance question. Measured across the forcing set:

| | archetype | entities | asked | refused | undetermined | issuance rule |
|---|---|---:|---:|---:|---:|---|
| BTC | Monetary network | 1 | 9 | 10 | 0 | yes |
| ETH | Smart-contract network | 1 | 12 | 7 | 0 | — |
| HYPE | Exchange network | **2** | 15 | 4 | 0 | — |
| 1INCH | Application protocol | 1 | 9 | 10 | 0 | — |
| TAO | **Not classified** | 1 | 4 | 0 | **15** | — |

And the committees swap sides, which is the clearest evidence they are
not one question twice:

```text
BTC     Supply Governance consensus_bound     Value Capture known_not_applicable
ETH     Supply Governance evidence_insuff.    Value Capture mechanism_evidenced
HYPE    Supply Governance evidence_insuff.    Value Capture mechanism_evidenced
1INCH   Supply Governance known_not_applic.   Value Capture no_mechanism_evidenced
TAO     Supply Governance applicability_unknown  Value Capture applicability_unknown
```

**TAO is a different kind of page**, not a thinner one: nothing is
refused for it and almost everything is undetermined, because not
knowing what an asset is cannot be a form of knowing about it.

### The finding the test produced

**BTC and 1INCH have identical counts — 9 asked, 10 refused — and are
not remotely the same asset.** BTC is asked about monetary scarcity and
adoption; 1INCH about protocol capture and holder accrual. The first
version of the differentiation test asserted on counts and passed four
of five; rewritten to assert on *which* questions, it holds.

The product consequence is now a design rule for this page: **a count is
never the differentiator.** The questions are listed by name, grouped by
applicability, and the three groups are separated rather than sorted —
*asked* is about the asset, *not applicable* is about the question being
the wrong instrument, and *undetermined* is about this platform.
Flattened into one list they read as degrees of coverage.

---

## 5. What the page refuses to imply

- **`UNKNOWN` is not a zero.** Asset Quality reads UNKNOWN for every
  crypto asset by design; the section prints the band with the
  backend's own reason and no number beside it.
- **`NOT_APPLICABLE` is not a negative result.** It gets its own group
  with a sentence saying it is a claim about the question.
- **No state is colour-coded.** Every tag is the same neutral grey,
  because none of these vocabularies is ordered and colour would invent
  a ranking the domain refuses.
- **An interpretation and a fact are two objects.** An event's facts and
  what sources read into it render separately, and every interpretation
  carries its author's name.
- **A count of captures is never a duration of monitoring.** The
  maturity section leads with coverage and renders the journal's own
  span sentence.

A final section — *What is not known* — collects the withheld
interpretations, the unanswered applicable questions, the abstaining
committees, the disagreeing readings and the unread surfaces, so that
*bad* and *we do not know* can be told apart at a glance.

---

## 6. Backend deficiencies exposed, recorded and not solved

1. **The equity dossier still serves a token an equity case.** Linked to
   the crypto dossier rather than redirected, because deciding which
   surface a token's investor narrative belongs to is the recommendation
   layer, and it does not exist.
2. **Asset class cannot be resolved without the brain pipeline.**
   `Brain.asset_class_for` reads the portfolio and candidates. This
   endpoint gates on `ASSIGNMENTS` membership instead — a declared,
   hand-verified list, and the same one `/crypto/corpus` serves, so the
   switcher and the gate cannot disagree. A cheap asset-class resolver
   is a real gap.
3. **`journal.captures` is 1 for every asset**, so every temporal
   sentence rests on a single capture. The coverage-first wording is
   honest about it, and the section stays thin until `movrvest acquire`
   has run repeatedly. Evidence maturity is an *acquisition cadence*
   question, not a UI one.
4. **There is still no shared notion of "acquired for committee N"**
   (recorded in #116). It is visible now: TAO shows both committees
   convened 3 times with 0 findings weighed.
5. **Asset Quality carries little per-asset signal.** Correct by design
   — one question of nineteen is scorable and the quorum is two — but
   the section is structurally identical across assets except for the
   question lists. Whether it earns its place on the page is exactly the
   kind of product feedback this slice exists to collect.

---

## 7. Surfaces

```text
GET /crypto/corpus            the assets this platform reads
GET /crypto/{symbol}/dossier  everything held about one, in one read
```

`/crypto/{symbol}` in the web app, with a switcher across the corpus.
404 for a security outside the corpus rather than a dossier of nine
absent sections: *we looked and found nothing* and *nobody looked* are
opposite claims about the same blank page.

Opening the page fetches nothing, asks no model and records no judgment.
`movrvest acquire` and `movrvest judge` remain the only two spends.

---

## Judged market facts reach the crypto dossier (2026-08-13)

The audit that earned this page found six crypto layers stopping at the
CLI. One layer was stopping *later than that* — served on this very
endpoint and dropped one line before the screen.

### The boundary that was dropping them

`GET /crypto/{symbol}/dossier` composes `"facts"` from
`asset_profile_response(TokenFactsService().established(...))` — the
same adapter, over the same stores, that the general dossier serves as
`asset_profile`. Thirteen judged rows in five groups, plus the rejection
ledger, for every asset in the corpus.

`parseDossier` in `lib/api/crypto-dossier.ts` had **no `facts` key**. Its
only occurrences of the word were nested inside events and journal. So
the payload arrived, was parsed into a view model with no place for it,
and vanished — while `/dossiers/HYPE`, the *general* case, rendered the
identical evidence. The surface built for tokens was the one hiding it.

Corpus-wide, what was invisible: **22 established, 50 claimed, 6
calculated, 6 conflicted, 20 absent** rows and 9 refused claims.

### HYPE, before and after

Before: nothing. After, on the token's own page:

- **Market value — Sources conflict.** No figure at all: *"credible
  sources disagree beyond observation-timing tolerance (10%):
  TokenInsight reports $18.3bn; CoinGecko reports $12.2bn. The sources
  appear to count the concept differently, and no methodology rule
  chooses between them."*
- **Circulating supply — Sources conflict**, three vendors 4.5× apart.
- **Claims this platform refused (2)** — *"Yahoo Finance's market value
  of $8,105 was not accepted: it disagrees with every arithmetically
  coherent claim by a factor of at least 1,504,321"*, and its project
  age claiming six years of history for a token that began trading in
  2024.

### Two rules the section keeps

**A conflict is never hidden behind a value.** Where sources disagree
the gate serves no figure, and the sentence explaining why is printed at
full size. The general dossier puts that sentence in a hover `title`;
a reader who never hovers never learns two sources disagree, so this
adaptation renders it always, for every row and every state.

**A refused claim is never a candidate value.** The ledger sits in its
own block, outside the groups, and says what it is: evidence about the
source that made it. Nothing in its shape — a bare `statement`, no
label, no standing, no source, no age — invites a surface to render it
as a row.

The presentation is adapted rather than imported: the crypto page's own
`Heading`, `Card` and deliberately-monochrome `Tag` are reused, so no
state is colour-ranked, and the equity `StandingMark` palette is not
carried across. The two dossiers share the backend adapter and share no
component.

### The unjudged-committee crash, and how reachable it was

`UnjudgedCommittee.as_dict()` emits `posture: None` and omits
`posture_stated`, `applicability` and `evidence_count` — correctly, since
*this committee has never run here* and *this committee ran and could
not answer* are different facts the domain keeps as separate types. The
parser required all four via `requireString`/`requireNumber`, threw on
the first, and `parseDossier`'s catch returned `dossier: null` — so one
unjudged committee blanked the entire page to "Nothing is held for this
asset".

**Not a ninth-asset hypothetical: the default state of a new checkout.**
`data/judgments/` is gitignored, so on a fresh clone every registered
committee is unjudged for every asset and every crypto dossier rendered
empty.

The guard is on the parser, which now reads those fields as absent and
renders the matrix's own sentence — *"this committee has recorded no
judgment for this asset, so nothing is known about what it would
conclude"*. `evidenceCount` becomes `null` rather than `0`, because a
committee that never ran did not weigh nothing. **No backend or domain
change was required**: what the domain says was already right.

### Deliberately not done

Judgment History stays off this page. The investigation that chose this
slice measured the store and found **zero verdict transitions across the
corpus** — 67 records, 26 judged, 26 abstained, 15 unavailable, and not
one (asset, committee) whose answer ever moved. Surfacing it today would
report when the committee was switched off, which is a fact about this
platform's configuration rather than about the asset. #113's
architecture is preserved; the presentation waits for a real change.

---

## Protocol economics reach the crypto dossier (2026-08-13)

The same boundary defect as the judged market facts, one layer over,
found by auditing the rendered page rather than the payload.

### What was dropping them

`protocol` is served on `/crypto/{symbol}/dossier` for all eight corpus
assets. The parser consumed it — entities arrived named, with `measures`
and `mapping_basis` — and `ProtocolEntityView` **had no `facts` field**,
so every figure those entities hold was discarded on the way. Then
`Sections` referenced `dossier.protocol` nowhere at all, so even the
names never rendered. The general dossier rendered all of it.

Held and invisible: **6 facts per asset, 12 for HYPE** — capital,
activity, value generation, holder accrual — each with source, age,
standing, availability and the provider's own methodology.

### The argument, not a table

The section orders the four families the way the argument runs — *what
the system earns* → *what reaches the token* → *how much flows through
it* → *what is committed to it*. On HYPE that reads:

> **Fees paid by users over 24 hours — $842.7k** *(Hyperliquid Perps:
> …excluding all spot fees…)*
> **Protocol revenue over 24 hours — $534.9k** *(99% of fees go to
> Assistance Fund for buying HYPE tokens…)*
> **Holder revenue over 24 hours — $534.9k**

**Entities are never collapsed.** HYPE carries two — the venue and the
layer-1 it settles on — because two DefiLlama entities once shared that
name 224× apart. Each states its own `mapping_basis`, which is the
provider's or filer's reason the economics belong to *this* token: the
venue's *"the provider records 99% of perp and spot fees going to an
Assistance Fund that buys the token… not inferred from the shared
name."*

### Magnitude beside the judgment, not a second record

The Value Capture cell gains **the two quantities its own question
names** — what users pay, and what reaches holders — per entity, tagged
with their standing and pointing back at the section that owns the full
record. Protocol revenue, the third quantity in the family, is left to
the section rather than repeated.

**It fires only where the committee answered.** Bitcoin's fee figure is
real — $139.0k over the observed day — and its Value Capture Committee
declines the question as the wrong instrument for a monetary asset, so
no magnitude appears beside that non-verdict. Measured across the
corpus: shown for ETH, SOL, HYPE, ARB and 1INCH; suppressed for BTC
(*known_not_applicable*), ADA (*execution_unavailable*) and TAO
(*applicability_unknown*).

### The three silences, rendered apart

Bitcoin shows all three in one card, which is why it is the control:

- **available** — fees $139.0k, with methodology and age;
- **unavailable_free** — protocol revenue: *"The source defines this for
  Bitcoin and reported no figure for the window. Whether that is a
  mechanism producing nothing or a reading that did not arrive, the
  source does not say."*
- **not_applicable** — holder revenue: *"it is not a mechanism this
  entity has, rather than a figure missing."*

TAO, the weakest asset, shows a third shape: `mapping unsettled` beside
the entity, and every value-generation figure *"Not available free"*.

### No multiple, and it is structural

No ratio, annualisation or per-market-cap figure appears in the adapter,
the composition or the page. That is not a promise about restraint: a
protocol figure crosses the wire as the backend's **worded** value, so
there is no number on this side to divide. HYPE is the case that makes
it matter — its market value is reported 50% apart by two credible
sources, so a fee yield would invent a denominator as well as a
conclusion.

### The regression is architectural

This class of defect has now been found twice in the same file, so the
guard is about the class rather than either section
(`tests/test_crypto_dossier_reaches_the_page.py`):

1. **every top-level key the route serves is read by `parseDossier`** —
   scoped to that function deliberately, because `record.facts` also
   appears in the journal parser and a file-wide search reported the
   dropped section as read;
2. **every field `CryptoDossier` parses is referenced by the page.**

Both halves were verified by re-creating the two historical defects and
watching the suite fail, then restoring.

No backend or domain change was required.

---

## The question taxonomy, grouped by what is held (2026-08-13)

The audit measured the question block at **32–35% of every crypto
dossier** — the largest thing on the page, and overwhelmingly the sound
of what the platform cannot say. Bitcoin asks nineteen questions: one is
scored, five are not yet answerable, ten are refused as the wrong
instrument. The single answered question sat among eight unanswered
ones, at identical visual weight.

### The duplication defect underneath it

For a question refused as the wrong instrument, `applicability_because`
and the quality answer's `because` are **byte-identical** — measured at
10 of 10 on Bitcoin — and the page rendered both. Ten doubled paragraphs
on BTC and 1INCH, seven on ETH, SOL and ADA. The answer's reason now
renders only where it differs from the applicability's.

### The regrouping

By the domain's own `participation`, never by a rule this side invents.
*Whether* a question is asked is applicability; *whether anything is
held to answer it* is participation, and those are the two questions an
investor is actually asking.

| group | rule | disclosure |
|---|---|---|
| **Asked, and something is held** | `scored`, `shown`, `outside` | open, full detail |
| **Asked, and not yet answerable** | asked and not held | **open**, one line each |
| **Not the right question for this kind of asset** | `not_applicable_for_archetype` | collapsed |
| **Undetermined** | `undetermined` | collapsed |

**The unanswered group is never folded away.** Collapsing it would let a
page with nothing held read exactly like a page with nothing missing.
Only the two groups that say *this question does not apply here* are
demoted, and every count stays in its heading so a collapsed group can
never be mistaken for an empty one.

### Measured, before → after

| | before | after |
|---|---|---|
| question block, BTC | 12,754 chars (31.8%) | **9,219 (24.1%)** |
| question block, HYPE | 13,081 (34.5%) | **10,097** |
| doubled reason, BTC | 2× per refused question | **1×** |
| BTC groups | Asked 9 · Not-right 10 | Held 4 · Unresolved 5 · Not-right 10 |
| HYPE groups | Asked 14 · Not-right 4 | Held 7 · Unresolved 8 · Not-right 4 |
| questions, every asset | 19 | **19** |

### Zero analytical semantics changed

Same question set, same applicability decisions, same participation
states, same backend-authored sentences. `held` and `unresolved`
*partition* the asked questions — `unresolved` is defined as
asked-and-not-held rather than filtered independently — so a question
cannot fall out of both, which is how a regrouping silently loses one.
Every reason stays in the page whether or not its group starts open,
which is what keeps the taxonomy inspectable.

No backend or domain change was required.

---

## One kind of information, one owner (2026-08-14)

**Status: accepted and built.**

A presentation-ownership audit of all eight `/crypto/{symbol}` dossiers,
implementation second. The question asked of every repeated item was not
*can this be deleted* but *which layer owns it* — because five of the six
findings turned out to be two correct layers each doing its job, composed
onto one page that had no way to tell their outputs apart.

### What was measured

Every asset's rendered page text, extracted from the SSR HTML with the
shell stripped, plus the payload behind it.

| finding | corpus before | class |
|---|---|---|
| committee conclusion rendered twice | 16/16 reasons byte-identical; 7/14 answers byte-identical | duplicate rendering of one semantic fact |
| lens explanation repeated | 111 renderings of ≤5 distinct sentences per asset | shared context at the wrong altitude |
| per-fact evidence maturity | 80 rows ending *"First observed on one capture."* | information the section already carried whole |
| `Times convened` | 16 counters; **0 verdict changes corpus-wide** | implementation execution history |
| `Evidence it weighed` | 16 counters; label untrue on every declined posture | implementation history mislabelled as evidence |

### Committee conclusion: the matrix owns it

`InvestorAssessment` is *supposed* to quote a committee — §14 of its own
module, *quoted, not translated* — and the Committee Assessment Matrix is
*supposed* to carry the same conclusion in the committee's own words with
its question, applicability, confidence and magnitudes. Neither is wrong.
The page rendered both at full length.

The matrix owns it, because it is the only one of the two that renders a
conclusion *with the question it answers*. So the repair is provenance
rather than deletion: `InvestorStatement.from_committee` carries the
committee key the statement quotes — a value the layer already held at
construction and discarded — and the page routes each statement to
exactly one section. `silent_committees` does the same for a silence a
committee owns, carried **beside** `silent_about` and never subtracted
from it, so `movrvest assessment` still sees every silence.

**Nothing was removed from any payload.** `GET /crypto/{symbol}/dossier`
serves the same assessment it always did.

### Evidence maturity: `shared_maturity`, and the unavailable case

`TemporalFact.stated` is unchanged — the synthesis cites it, and #111's
contract holds. What is new is `observed_stated`, the same reading
*without* the temporal clause, and `shared_maturity(facts)`, which
returns the maturity every fact shares or `None` where they differ.

The measurement that changed the design: a strict rule over *all* facts
fired for only three of eight assets, because five carry one or two
`UNAVAILABLE` readings. An unavailable fact's sentence **carries no
coverage clause at all** — §6, an unavailable reading is compared with
nothing, so there is no coverage claim on it to qualify — so it is not
consulted and not spoken for. It keeps its own status, its own span and
its own sentence, and the other thirteen stop repeating themselves.

The shared line is hedged rather than universal (*"Except where a finding
says otherwise below…"*) for exactly that reason: *"every finding below"*
would be false about the one finding a reader most needs to notice.

### The two counters, and why they are different removals

**`Times convened`** counts runs of `movrvest judge`. Across all sixteen
recorded series **no verdict has ever changed**; every variation is this
platform's own judging flag being toggled, plus one draft the prose
validator refused. It is execution history.

**`Evidence it weighed` did not measure what its label said.** The count
is captured beside the judgment by `app/commands/judge.py`, which calls
`committee.evidence(asset)` unconditionally — while `judge()` returns
*before* reading any evidence when the question does not apply. So
Bitcoin's Value Capture declined the question as the wrong instrument,
cited no refs, and reported weighing **3 findings**. Where a committee
did answer, the findings it cited are already rendered beneath it as *the
magnitudes it read*.

Both remain in the domain, in the store, in `CommitteeAssessment` and on
`movrvest committees`. **No domain history was deleted.** A test asserts
both fields still exist.

### Recorded and deliberately not fixed

**The recorded `evidence_count` is wrong for a declined judgment**, and
correcting it is a change to what future records *mean*: a count moving
3 → 0 is #113's `EvidenceMovement.EVIDENCE_LOST`, and a repair would make
every asset's history show a movement that never happened. It needs its
own slice with a migration story, not a presentation fix.

`Confidence` still saturates, and the Gaps section still restates
committee postures — by its own declared purpose, so that *unfavourable*
and *absent* can be told apart.

### Measured, before → after

Visible page characters, over `<main>` only.

| | BTC | HYPE | corpus (8) |
|---|---|---|---|
| visible characters | 37,781 → **34,732** | 38,699 → **35,999** | 267,974 → **245,302** (−8.5%) |
| committee conclusion renderings | 9 → **5** | 7 → **4** | 37 → **21** |
| lens-explanation renderings | 14 → **6** | 18 → **12** | 111 → **55** |
| repeated prose lines | 29 → **24** | 33 → **24** | 247 → **171** |
| evidence-maturity rows | 13 → **0** | 13 → **0** | 80 → **0** |
| `Times convened` | 2 → **0** | 2 → **0** | 16 → **0** |
| `Evidence it weighed` | 2 → **0** | 2 → **0** | 16 → **0** |

The residual lens renderings are the group headers themselves — one per
lens per question group — and the first explanation of each lens in the
assessment. The residual committee renderings are one card each plus the
Gaps collection and, on BTC, the issuance formula, which is the rule
rather than the conclusion.

### The regression is architectural

`tests/test_crypto_dossier_presentation_ownership.py`, built from domain
builders in a temporary store — nothing reads acquired evidence. It
asserts that every committee statement names the committee it quotes
across **all five postures**, that a statement the assessment section
owns can never repeat a committee's reason, that the page routes on the
backend's mark rather than on a subject name, that neither execution
counter reaches the surface while both stay in the domain, that an asked
question always names its lens and a lens has exactly one applicability
sentence **corpus-wide**, and the four maturity cases including the
all-unavailable one.

Each guard was mutation-checked: reverting any one of the five repairs
fails between two and five of them.

### Boundaries kept

No new analytical logic, no new metric, no acquisition, no network call.
No committee judgment, applicability, participation, evidence,
confidence or domain meaning changed — `movrvest committees`,
`movrvest assessment` and `movrvest judgment-history` render exactly what
they rendered before. The equity dossier consumes neither
`InvestorAssessment` nor the committee matrix and is untouched.
