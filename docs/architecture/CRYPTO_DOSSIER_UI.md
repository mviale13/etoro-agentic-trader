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
