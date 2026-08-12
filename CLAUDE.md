# MOVRvest

An Artificial Chief Investment Officer. It turns verified evidence into
transparent investment recommendations. **MOVRvest recommends; the investor
decides.**

This file is loaded automatically at the start of every session. Keep it
short, and keep it true — everything here is checkable.

---

## Read these first

| Question | Document |
|---|---|
| How do we work? | [`docs/ENGINEERING_CONSTITUTION.md`](docs/ENGINEERING_CONSTITUTION.md) — **§23–24 first** |
| Which package owns what? | [`docs/architecture/REPOSITORY_INVENTORY.md`](docs/architecture/REPOSITORY_INVENTORY.md) |
| What is built, what is missing? | [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md) |
| What is next, and what is open? | [`docs/architecture/MIGRATION_PLAN.md`](docs/architecture/MIGRATION_PLAN.md) |
| How does the pipeline work? | [`docs/architecture.md`](docs/architecture.md) — **v5.0 section onward** (everything before it is v4.0 history) |
| What state is the frontend in? | [`docs/frontend/UX_UI_INVENTORY.md`](docs/frontend/UX_UI_INVENTORY.md) — audit + slice-by-slice execution log |

[`docs/README.md`](docs/README.md) indexes the above and names the one
reference doc ([`docs/ETORO_API.md`](docs/ETORO_API.md)). The ~20 older
documents that predated the current architecture — several contradicting each
other and the code — now live under [`docs/archive/`](docs/archive/). Treat
anything not listed above as historical unless you verify it against the code.

---

## Commands

```bash
source .venv/bin/activate      # required; the tooling is not on the system PATH

python -m pytest -q            # ~2100 tests, fast
python -m ruff check .
python -m mypy app             # must be clean

cd apps/web/movrvest-web && npm run build     # frontend gate
```

CLI: `movrvest evaluate SYMBOL`, `movrvest brain`, `movrvest today`,
`movrvest knowledge SYMBOL` (the consensus over stored observations of a
filing, every claim with its width and cell),
`movrvest observe SYMBOL` (read the current filing again up to the quorum
of 5 — the explicit spend that fills a consensus; stops on the count,
never the content),
`movrvest archetype SYMBOL` (what kind of business the consensus facts
make it, and which rule decided — or why none could),
`movrvest understanding SYMBOL` (how the business creates value, derived
deterministically from consensus — engine, mechanisms with support,
what could change the conclusion),
`movrvest playbook SYMBOL` (which playbook analyses the business:
grounded from quorate understanding where the mapping has earned the
conclusion, otherwise the industry route as recorded fallback — the two
never blend),
`movrvest playbook-coverage` (measure the grounded selector over the
book, read-only: leads with the investor-visible funnel — companies →
read → decided → mapped → quorate, portfolio first — then per security
the width, the outcome, and exactly one blocking claim; the blocker
distribution is the roadmap),
`movrvest reader-stability SYMBOL --readings N` (one document read N times,
and how far the readings agreed — a measurement of this platform, storing
nothing),
`movrvest reader-defects` (every absent claim in the store classified
against the knowledge layer's own reason templates, counted by
structural cause — the measurement that decides whether reader work is
earned: patterns earn architecture, individual failures earn backlog
entries),
`movrvest decide SYMBOL QUESTION` (ask one investment question — entry,
increase, decrease, research_spend — and get a canonical decision: a
constitutional verdict or a worded refusal, its clauses with their
edges, and the implications weighed with the losers preserved; appends
one event to the append-only (subject, question) stream, and the
current stance is always the latest answer; see
[`docs/architecture/INVESTMENT_DECISION.md`](docs/architecture/INVESTMENT_DECISION.md),
accepted),
`movrvest statements SYMBOL [--statement income_statement|balance_sheet|cash_flow_statement]`
(the consensus over stored statement observations of the current
filing: every concept with its width, cell, printed figure and caption
— the filer's figures at checked addresses, nothing derived; three
statements are three quorums and are asked for one at a time),
`movrvest observe-statements SYMBOL [--statement KIND]` (the statement
stream's explicit spend, to the quorum of 5; stops on the count, never
the content),
`movrvest statement-shape SYMBOL` (which figures the filer prints a line
for, which it prints under a label this platform cannot read, and which
statement was never located — the distinction a consensus's "no figure
located" hides. Deterministic, no model, stores nothing; an absence
counts as the filer's only where the statement was also *read*, which
MUFG's 20-F earned),
`movrvest financials SYMBOL [--model generic|bank]` (what those
statements *measure* — margins, growth, ratios and cash flow computed
by this platform from two checked cells apiece, each with the narrowest
agreement beneath it — and then the governing financial model's
questions over exactly those facts: answered, not yet answerable, or
not applicable with the evidence that would answer it. Read-only, never
observes; `--model` is inspection and never changes what governs),
`movrvest supply [SYMBOL]` (what each of a token's supply numbers
actually counts — which quantity, whose definition, and whether two
figures are a real disagreement or two different facts. Read-only, and
it interprets nothing: dilution is not a word it knows),
`movrvest primary [BTC|ETH|ADA|HYPE]` (read canonical chain state
directly and report what it can settle: each figure with its evidence
authority, window, formula, rule version, inputs and both
reproducibility verdicts. A measurement of this platform, not of an
asset — it costs a fetch, asks no model, stores nothing and decides
nothing),
`movrvest crypto-market [SYMBOL]` (the crypto environment as the last
cycle read it — capitalisation, volume, dominance, breadth — and, with a
symbol, that asset's place in it: its returns, its peer group and why
that group, and the arithmetic between them at the one interval every
side is published at. Read-only, and no band, traffic light or regime
label appears),
`movrvest crypto-playbook [SYMBOL]` (which investment questions a
digital asset is asked *at all*, and which are the wrong instrument for
it: with a symbol, the archetype and its grounded basis, every question
with its applicability and the evidence held against it, the declines
each with its reason, and every mapped entity's value chain from use to
the token; without one, the corpus as a matrix. Read-only, decides
nothing — see below),
`movrvest issuance [SYMBOL]` (how new supply enters a system: the
mechanism, every parameter with the surface it was read from, what could
change the rule, and what the rule implies from here — MOVRvest's
arithmetic *under the currently observed policy*, never a forecast. An
allocation-release asset gets the specific missing evidence named
instead. Read-only, scores nothing),
`movrvest crypto-quality [SYMBOL]` (which durable qualities of a digital
asset this platform can actually judge: the band or the honest absence
of one, the coverage and confidence beneath it, and every applicable
question with how it participated — scored against a named rule, shown
with its standing and counted by nothing, or not yet answerable with
what would answer it. Without a symbol, the readiness table and the
corpus. Read-only),
`movrvest crypto-events [SYMBOL] [--evidence]` (every current
development held for an asset, deduplicated across the surfaces that
reported it: what each account asserts, what it merely reads into
things, which figures a second source independently carries, and how
close to the event the reporting gets. Read-only, and it introduces no
event from the press),
`movrvest intelligence-journal [SYMBOL] [--evidence]` (the append-only
record and the deterministic reading of it: how often this platform
looked, the longest it went without looking, and per finding whether it
is new, unchanged, changed, no longer produced or unreadable. Read-only,
no model, and a count of captures is never presented as a duration of
monitoring),
`movrvest judge [SYMBOL]` (convene the committee and **record** what it
concluded — the explicit spend that writes judgment history, kept apart
from every read-only surface so that opening a page can never
manufacture a judgment event),
`movrvest judgment-history [SYMBOL] [--evidence]` (what this committee
concluded, when, and what changed since — the answer, the observation
beneath it and the evidence itself as three separate facts, with a
previous verdict never restated as today's. Read-only, no model, and a
count of judgments is never presented as a duration of review),
`movrvest assessment [SYMBOL]` (the strongest statement the evidence
supports, per subject: a figure it settles, a bound across estimates, a
structural fact, something true within a stated limit, or an honest
uncertainty. A difference between sources becomes an uncertainty only
where the difference changes what can responsibly be said, and no figure
is ever averaged into one nobody published. Read-only, no model, and no
recommendation, score or ranking),
`movrvest committees [SYMBOL] [--evidence]` (what every registered
committee has concluded: per committee the question it owns, its
conclusion in its own words, why, the confidence it expresses and the
evidence beneath it — one block per committee with a symbol, the corpus
as a grid without one. Read-only, no model, no fetch, and **nothing is
combined**: no overall verdict, no agreement, no score, no ranking, and
confidence is never compared across committees),
`movrvest acquire [--candidates N]` (read the market for every holding,
the research candidates and the market strip **in one batch**, and fill
the store the surfaces serve from — the provider half of the same
explicit spend `observe` is for filings).

**A page view reads what has been acquired, and acquires nothing.** Not
a preference: it is why a dossier took 21 seconds and Research 60. Both
halves now hold — `CompanyResearchService` opens
`CompanyKnowledgeService.established`, and `CompanyFactsService` and
`MarketPerception` open the providers' `stored()` doors — so no surface
resolves a filing, prices a security or asks a model. A stored price is
served with the moment it was taken ("Yahoo Finance, 3 hours ago"), and
a security never acquired has no price rather than a stale-looking one.
Acquisition is `movrvest acquire` and `movrvest observe`; a fresh clone
shows absences until one of them is run, which is what it is.

Knowledge is observations plus a derived consensus, never a single
reading presented as the account: see
[`docs/architecture/KNOWLEDGE_CONSENSUS.md`](docs/architecture/KNOWLEDGE_CONSENSUS.md)
(accepted). The store holds `CompanyKnowledgeObservation`s (schema 12
since E1 — a wordless named segment is asked against the package's
untagged report prose, so readings shown different text never pool;
the corpus re-reads on the owner's next observe cycle —
append-only); `consensus_of` derives on read; the decision path consumes
`CompanyKnowledgeConsensus` only. Financial statement facts are their
own observation stream (schema 3, `data/statements`, never pooled with
segment readings), one quorum per statement, with
`FinancialUnderstanding` above them as the arithmetic layer
`BusinessUnderstanding` is above narrative consensus: see
[`docs/architecture/FINANCIAL_STATEMENT_ACQUISITION.md`](docs/architecture/FINANCIAL_STATEMENT_ACQUISITION.md).

The financial analysts have **two routes that never blend**: the
filing-grade route (reading established facts, absence stated in the
filing's own words) and the provider-fed route
(`app/analysts/*_analyst.py`, reading `CompanyFacts`). The first
outgrows the second one authoritative case at a time — never by
wrapping it, which is the Yahoo boundary in
[`docs/architecture/INVESTMENT_ASSESSMENT.md`](docs/architecture/INVESTMENT_ASSESSMENT.md).

**What a company is and how it is read financially are two
classifications.** `PlaybookKind` answers the first from business
understanding; `FinancialModel` (`app/domain/financial_question.py`)
answers the second and owns the financial question set — which
questions are meaningful, which facts answer them, and which generic
questions are refused. They are coupled today by `model_for`, which
says it is a coupling. **Never change a playbook route to fix a
financial interpretation**: see
[`docs/architecture/PLAYBOOK_SELECTION.md`](docs/architecture/PLAYBOOK_SELECTION.md).

**The Financial Statement Domain ends at financial language.** Accepted
boundary, on three measurements
([`FINANCIAL_DOMAIN_BOUNDARY.md`](docs/architecture/FINANCIAL_DOMAIN_BOUNDARY.md)):
statements establish *language* — generic, interest-based,
insurance-based — and never prudential regulatory *status*. Prudential
concepts (CET1, LCR, NSFR…) belong to a separate evidence domain sourced
from a filing's regulatory sections, never to `StatementConcept`. So
`FinancialModel.BANK` cannot be selected from statement evidence at all,
and stays derived from business understanding until a **Prudential
Understanding** layer exists. Connecting `StatementLanguage` to
`FinancialModel` — even as one term of a larger rule — is forbidden.

The three measurements beneath that ruling, each load-bearing:

- **Statement shape identifies a financial-institution family and
  cannot select `BANK`** — 8 banks and 5 insurers match the JPMorgan
  triad identically, and so does a filing this platform failed to read
  ([`FINANCIAL_LANGUAGE_CORPUS.md`](docs/architecture/FINANCIAL_LANGUAGE_CORPUS.md)).
- **Bank behaviour needs positive evidence of bank financial language,
  never the absence of generic industrial concepts.** `StatementLanguage`
  (`app/domain/statement_language.py`) supplies it from two printed
  lines — a net interest subtotal, a premium revenue line — at 5/5 over
  24 companies with no false positive either way
  ([`FINANCIAL_LANGUAGE_EVIDENCE.md`](docs/architecture/FINANCIAL_LANGUAGE_EVIDENCE.md)).
  It is acquired and **connected to nothing**; `model_for` is untouched.

- **`BANK`'s own demands cannot be grounded yet** — CET1 and the LCR
  discriminate perfectly (10/10 banks, 0/9 non-banks, including three
  interest-based lenders that are *not* deposit-funded), and are printed
  in a capital/liquidity region this platform does not locate: CET1 is
  reachable for 2 of 10 banks, the LCR for none
  ([`BANK_PRUDENTIAL_EVIDENCE.md`](docs/architecture/BANK_PRUDENTIAL_EVIDENCE.md)).
  None of them appears on the face of a primary statement, so none
  belongs in `StatementConcept`.

The standing guard on all three: **a concept's absence is evidence only
where the section that would carry it was located *and* read.** A
statement establishing nothing looks identical to a bank's, an insurer's
and an ordinary company's — and a prudential fact missing from every
region this platform acquires is missing from places it never looked.

---

## Where the work is now: consuming the graph, not growing it

**The Financial Statement Domain and its dossier consumption are
complete for now.** The owner's standing direction is to stop expanding
the knowledge graph and make what is known usable. Do not extend
acquisition, add financial concepts, or alter model selection without a
new ruling.

**A token's questions are chosen before its evidence is read** (S3,
[`CRYPTO_ARCHETYPES.md`](docs/architecture/CRYPTO_ARCHETYPES.md)). A
`TokenArchetype` is a *name for a set of `AnalyticalCapability` lenses*,
and a question is owned by a lens — which is what lets HYPE compose the
venue's questions and the chain's without a bespoke playbook, and what
keeps Bitcoin from ever being asked what it pays its holders. Three
vocabularies stay apart: **applicability** (from the archetype alone —
`applicability_for` has no parameter a figure could arrive through),
**evidence standing**, and **verdict** (nothing yet). The same fee
figure means the security budget on Bitcoin, a burn on Ethereum and a
buyback on Hyperliquid, and the mechanism is recognised from the
provider's own sentence rather than declared. Consumed by nothing:
guarded by an import-graph test over fifteen reasoning paths.

**Where a fact came from is a second axis, never a second standing**
(S4.5, [`CRYPTO_EVIDENCE_AUTHORITY.md`](docs/architecture/CRYPTO_EVIDENCE_AUTHORITY.md)).
`EvidenceAuthority` — primary observation, primary derived, secondary
computation, secondary aggregate, provider-scoped aggregate, attributed
opinion — explains *why* a standing rule applies and what would move it;
`ESTABLISHED` keeps meaning what it meant. **Primary is not a synonym
for true**: computed with the protocol constant this platform knew,
Ethereum's blob base fee came out wrong by a factor of 850 million from
canonical inputs, and Hyperliquid's own `totalSupply` includes 412m
tokens that do not exist yet. **Circulating supply is not a chain
primitive** — Cardano's ledger publishes four quantities and the three
vendors S1 called CONFLICTED were each reporting a different one, the
rejected reading matching `circulation` exactly. A provider-scoped
aggregate (total market cap, rankings, breadth) **can never be
corroborated** and its honest ceiling is permanent attribution.

**Two numbers only conflict if they claim to represent the same thing**
(S4.6, [`CRYPTO_SUPPLY_SEMANTICS.md`](docs/architecture/CRYPTO_SUPPLY_SEMANTICS.md)).
Crypto supply is an accounting vocabulary: five concepts (max, emitted,
future emissions, excluded balance, circulating estimate), each carrying
a `SupplyMethodology` whose `disclosed` flag decides everything —
**an undisclosed methodology is not a different methodology**, or any two
numbers could avoid conflicting by being equally unexplained. ADA's
three-way conflict dissolved (TokenInsight was reporting the ledger's
`supply`, Yahoo its `circulation`); HYPE's stands because two vendors
publish no exclusion set. **The re-judgment is reported, not written into
`judge()`** — `CompanyFactsService` reads those standings and a score
would move.

**Market context is not Asset Quality** (S4,
[`CRYPTO_MARKET_CONTEXT.md`](docs/architecture/CRYPTO_MARKET_CONTEXT.md)).
`CryptoMarketSnapshot` is a third crypto evidence family, unreachable
from the other two in both directions. Two rules it carries: **an
interval is part of a figure** — a level is INSTANT, a change names its
window, and `relative_return` refuses unless both sides match — and **a
capitalisation change is not a return**, so the comparator is MOVRvest's
own cap-weighted return over a *named* universe (the provider's
aggregate moved +0.05% where its top 250 returned +0.11%). A
`MarketPeerGroup` is a vendor's category and **never** an
`AnalyticalArchetype`: ETH is read as a smart-contract network and
compared against a Layer 1 group containing Bitcoin, and the two modules
cannot import each other.

**One question of nineteen can carry a score** (S5,
[`CRYPTO_ASSET_QUALITY.md`](docs/architecture/CRYPTO_ASSET_QUALITY.md)).
The four-factor crypto signal is deleted, not repaired. A fourth
vocabulary joins S3's three — **readiness**, a property of the *question*
alone, so `readiness_for` has no parameter an asset could arrive through
and no well-covered security can make a question scorable that stays
unscorable elsewhere. Three measurements decided it: **volume over market
cap is not liquidity** (it ranks BTC 158th of 233 and 1inch 52nd, while
BTC trades $14.8bn a day and 1inch $7m), **a vendor's `total_supply` is
the protocol maximum for 83 of 145 capped assets** in the top 250 — the
chain impeached it for ADA and TAO — and **two sources agreeing to the
last bit are one source** (TokenInsight's ADA figure is a bit-identical
copy of the Cardano ledger's, so it cannot corroborate it; a *declared
constant* matching exactly is the expected shape and a *measured*
quantity matching exactly is replication). Only market robustness scores,
on `market-significance-floor@1` ($10bn / $500m, measured against the 250
largest); the quorum of 2 is inherited, so **every crypto asset now reads
UNKNOWN** and stops at INVESTIGATE. Age is gone, market context and
valuation are unreachable by construction, and HYPE's economics are
`VISIBLE_NOT_SCORED` — mechanism settled, amount claimed.

**A chain reading may settle a figure alone, behind six gates** (S5.1,
[`CRYPTO_SUPPLY_ESTABLISHMENT.md`](docs/architecture/CRYPTO_SUPPLY_ESTABLISHMENT.md)).
Model C, and **not** *deterministic primary computation → ESTABLISHED*:
identity, semantics, constants, reproducibility, perimeter, versioning —
and **a gate that cannot be evaluated fails**, because "we did not check"
is the state the blob fee was in. Two readings clear all six: Cardano's
ledger reconciles to *zero lovelace* across seven published quantities,
and its 45bn maximum falls out of `supply + reserves` exactly, so the cap
stops being a vendor claim; Hyperliquid reproduces its own
`circulatingSupply` and needs no denomination constant. Arbitrum fails
**identity** (a hard-coded address returns a number and no name) and
Bittensor fails **semantics** (one figure, nothing to reconcile).
Supply structure still does not score, and the reason changed: **Arbitrum
is 100% emitted with 33.9–87.2% of its maximum outside the market** while
Cardano is 86.2% emitted with 18.8% all named by the ledger — the ratio
and the holder's exposure come apart, so a band would reward the larger
overhang. Quorum stays 2, every asset stays UNKNOWN.

**A mechanical issuance rule and a vesting schedule are two different
economic objects** (S5.2,
[`CRYPTO_MECHANICAL_ISSUANCE.md`](docs/architecture/CRYPTO_MECHANICAL_ISSUANCE.md)).
`JsonCache` now owns a schema contract — five compatibility states,
sequential migrations, and **no backward migration from a newer record**
— because eleven per-store copies means the eleventh is forgotten.
`MechanicalIssuance` then acquires the three rules primary state
supports: **ADA reads all four parameters including the epoch length**
(432,000 s, from the chain's own timestamps), **SOL is uncapped and
publishes its entire schedule in one call** — uncapped is not unruled —
and BTC's rule is consensus but its *total* stays CLAIMED: the residual
against a precise independent figure is **constant to the satoshi at
28.95844904 BTC**, so the rule is right and the composition is still
unitemised. Allocation-release tokens (ARB, HYPE, 1INCH) get **no entry
at all** rather than an empty one. Everything is CLAIMED, consumed by
nothing, quorum still 2.

**Predictability does not discriminate; magnitude does — and magnitude
is not quality** (S5.3,
[`CRYPTO_SUPPLY_POLICY_MEANING.md`](docs/architecture/CRYPTO_SUPPLY_POLICY_MEANING.md)).
Measured, then declined. BTC, ADA and SOL are *equally* explicit and
*equally* projectable — every one of eleven parameters read from a chain
— so a predictability factor would give all three the same answer; only
mutability separates them, and one protocol-fixed asset is not a corpus.
Their five-year expansion runs **2.73% / 10.64% / 14.51%**, a factor of
five. But **the same issuance figure is a security budget or a transfer
depending on where it goes** — the S3 fee lesson mirrored — so magnitude
is parked `OUTSIDE_ASSET_QUALITY` for a future tokenomics layer, not
scored. **Factor #2 was not earned; crypto stays UNKNOWN.** BTC's flow
rule is separately confirmed (89 of 89 daily intervals within the
consensus bound, never once exceeded) while its historical stock stays
unresolved — a stock residual does not block a flow rule.
`movrvest issuance [SYMBOL]` renders all of it without scoring it.

**Asset Quality is not the product** (Crypto Intelligence,
[`CRYPTO_INTELLIGENCE.md`](docs/architecture/CRYPTO_INTELLIGENCE.md)).
A separate layer answering *what changed, what is driving it, why it
matters, what to watch* — and **structurally unable to reach Asset
Quality**, because every crypto asset reads UNKNOWN and an investor
asking about Bitcoin is not served by silence. Four epistemic types
travel with every claim (**measured / reported / attributed /
inferred**), so a provider's *"inflows are supporting BTC"* decomposes
into a reported flow, a measured price state, an inferred holdings
reading and an attributed causal link. **A driver references claims and
cannot be constructed without them** — `snapshot.grounded` is a checked
property. Claims carry a relevance window and go stale. ETF flows and
disclosed holdings are acquired free and keyless (SoSoValue,
CoinGecko treasuries); **HYPE gets no ETF concepts and nothing says it
is missing one**. Deterministic — no model is wired — and
decision-neutral, guarded by an import test.
`movrvest crypto-intelligence [SYMBOL] [--evidence]`.

**A hedge separates a fact from a reading; a number makes a fact
*checkable*** (Crypto Intelligence slice 2,
[`CRYPTO_EVENTS.md`](docs/architecture/CRYPTO_EVENTS.md)). Two different
properties, and conflating them filed *"AUSTRAC suspended Cryptolink's
VASP registration"* as an opinion. So a sentence that hedges, grades
(*dominates*, *significant*) or claims a cause is an `Interpretation`
carrying its author's name; everything else is an `EventFact`; and
`anchors` — its normalised figures — are what make two accounts
recognisable as one event. **An event's identity is its shared figure,
not its words**: eight accounts of one MicroStrategy sale collapse into
one development, matched on `1690`, because outlets never choose the
same words and almost always quote the same number. Nine families, each
observed in the live corpus before it was declared; **`GOVERNANCE`
measured and declined**. **The press corroborates and may never
introduce an event** — a keyword gate over headlines is a relevance
model, and a bad one, and it produces the news feed the ruling forbids.
Two guards the corpus forced: a press item must **name the asset** (four
*bitcoin* ETF stories attached themselves to *Ethereum's* ETF event on
four shared words and no shared subject), and a **small number is not an
identity** (*"August 3-9"* yields `3` and `9`). **Price commentary is
not an event** and is declined with a count — it is a worse reading of
what S4 already measures. Stale events **leave** the brief rather than
ranking last, and the empty state is a stated absence.
`movrvest crypto-events [SYMBOL] [--evidence]`.

**A net total is not a rate of demand.** Slice 1's handoff flagged that
a 30-day flow sum without dispersion overstates persistence; the
measurement was worse than the flag. **BTC's largest single day of
selling was −$445m — 3.5× the whole month's +$128m net** — while ETH's
+$540m arrived on 21 of 30 sessions with no day above $92m:
`concentrated` against `persistent`. Fixing the *sentence* alone left
the brief contradicting itself, the claim saying "offsetting flows
rather than accumulation" beside a driver still calling it "a net source
of demand", so **the driver changed too** and BTC now has no flow
tailwind. Cache schema 2, with the migration leaving the new figures
**absent rather than zero**.

**The LLM prioritises, connects and explains; it produces no evidence**
(Crypto Intelligence slice 3,
[`CRYPTO_INTELLIGENCE_SYNTHESIS.md`](docs/architecture/CRYPTO_INTELLIGENCE_SYNTHESIS.md),
built and **off by default**). One call per asset over the findings
already held — no tools, no web, no retrieval — returning *what matters
/ why it matters / watch next*, **each item carrying its own refs**.
`MOVRVEST_INTELLIGENCE_SYNTHESIS=on`; the provider and model are the
Executive Writer's, the on switch is separate, and the seam, the
`NarrativeFinding`, the fail-closed validation and the worded absence
are all reused — **a different prompt and schema were expected; a second
trust architecture was not.**

**The validator is the slice, and calibrating it against live drafts was
the work.** Six rules: unknown refs, unsupported figures (including a
**rounded** one — the model wrote `5.61m` where evidence said
`5,610,842`), unsupported names, guarded domain concepts (*proof of
stake*, *21 million*, *the merge*), causal verbs without an attributed
cause, and verdicts aimed at the reader. It was wrong in **both**
directions against real output: it refused *"these funds already hold
1,223,634 BTC"* because `hold` is also a verdict — **a verb is not a
verdict** — and refused *"Operational signals are cautious"* because
capitalised is not the same as a proper noun. Exempting the first word
then let **"Coinbase led the buying."** through, which the failure
demonstration caught. The resolution is measured, not argued: across
nine live drafts every sentence-initial rejection was ordinary English
and fabricated names appeared **zero** times, so the first word is
challenged only when *shaped* like a name. **The residual limit is
stated rather than hidden.** Also caught: `sent ` matches inside
*absent* and *present*; `staking` must stem to *staked*; `AI's` must
strip its possessive. **Acceptance 9 of 12 live drafts**, and a rejected
draft renders the deterministic brief with one line saying why.

**This platform now has a memory, and it is observations rather than
conclusions** (the Intelligence Journal,
[`INTELLIGENCE_JOURNAL.md`](docs/architecture/INTELLIGENCE_JOURNAL.md)).
Append-only JSON Lines per asset, written by `movrvest acquire`, read by
a deterministic projection — **no model, ever**: *code establishes
history; the model explains grounded history*. It answers *what did
MOVRvest know about BTC on 1 August*, not *what would today's pipeline
say about evidence dated 1 August*, so a later run appends and a
correction is a **new entry naming what it corrects**. Schema rides on
the line rather than the file, because a file that is never rewritten
cannot be migrated.

**Three things can change and conflating them would be the worst defect
here**: the world moved (the source's own date advanced), the source
revised itself (its date did not), or **our reading changed** — and the
third is never an economic event. An `UNAVAILABLE` observation is never
compared with a value, including with another `UNAVAILABLE`, which is
what stops a provider outage arriving as *"holdings fell to zero"*.

**And the hardest rule, which is honesty rather than correctness: three
captures across three weeks are not three weeks of monitoring.** Every
temporal sentence is worded from `ObservationSpan` — count, first, last
and **largest gap** — so a run reads *"unchanged across the last 3
capture(s)"* and never *"for three weeks"*. The surface leads with
Coverage before any finding. Temporal facts reach the synthesis as `H`
findings carrying their journal entry ids; delete the observations and
the claim becomes **unavailable rather than reconstructable**.
`movrvest intelligence-journal [SYMBOL] [--evidence]`.

**The first layer permitted to interpret evidence, and the fence around
it** (the Value Capture Committee,
[`VALUE_CAPTURE_COMMITTEE.md`](docs/architecture/VALUE_CAPTURE_COMMITTEE.md),
built and **off by default**). One committee, one remit chosen by
measurement — fees are the widest non-price evidence at 8/8, and the
holder-revenue sibling is *established-and-empty* for three assets,
which under S2's sibling rule is evidence of absence rather than absent
evidence. **Eligibility is structural**: only `MEASURED`/`REPORTED`
reach it, and `EligibleFinding` raises on anything else, so an
`ATTRIBUTED` claim cannot be *constructed* as committee evidence.
Synthesis prose is unreachable — *the synthesis is communication, not
evidence*.

**Three questions, never collapsed: applicability, evidence, judgment.**
Applicability is decided *before* any evidence is read, and **the
committee owns that rule rather than delegating to `applicability_for`**
— forwarding to `TokenArchetype` would make this a generic
crypto-quality judgment wearing a narrow remit, and it produced a
concrete defect: BTC and TAO came out identical. They are not. BTC's
role is established and the question is the wrong instrument
(`NOT_ECONOMICALLY_APPLICABLE`, and **never adverse**); TAO's role is not
established at all (`APPLICABILITY_UNESTABLISHED`).

**Neither verdict is a grade and no share is banded.**
`MECHANISM_EVIDENCED` is a structural fact, not "favourable" — 64%, 18%
and 9% are contrast, and six observations do not establish a floor
(S5.3's ruling, applied again). **Confidence is counted by code and the
verdict chosen by the judge**, so more evidence raises confidence and
cannot move the answer. The schema has three fields and no room for a
score, a recommendation or a conviction.
`movrvest committee-judgment [SYMBOL] [--evidence]`.

**A number moving is not a conclusion moving** (Judgment History,
[`JUDGMENT_HISTORY.md`](docs/architecture/JUDGMENT_HISTORY.md), accepted
and built). The journal remembers evidence; this remembers *judgment*,
and every transition carries **three axes, never one field** — what
happened to the answer, to the count of observation beneath it, and to
the evidence itself. **Evidence moving under a steady answer is the
ordinary case** and renders as a sentence saying so, because a layer
that collapsed them would announce a reversal roughly daily out of true
parts. The first live run demonstrated the separation unprompted:
HYPE's four eligible findings were **byte-identical across three
judgments** while the answer moved from unanswered to
`mechanism_evidenced` and back.

**A historical verdict is never today's verdict.** `JudgmentStanding`
enforces §5 structurally — `verdict` returns `None` unless today's
committee answered, and the earlier record is reachable only through
`previously` — so this platform says *"the previous judgment was that a
mechanism is evidenced; today the committee did not run"* and can never
say *"the mechanism remains evidenced"*. The transition beneath it is
`BECAME_UNANSWERABLE`, worded *"unrefreshed rather than contradicted"*:
**an unavailable today is not a reversal.**

**Six postures, and four of them produce no verdict** — the owner's PR
#112 catch carried into history, because BTC (wrong instrument) and TAO
(applicability unestablished) both answer nothing and their problems are
opposite. **Committee identity is a fingerprint derived from the live
contract** (question, applicability rule, eligible claim types, verdict
vocabulary), so a contract change makes old records visibly incomparable
— and incomparability *short-circuits* the other two axes rather than
hedging them. **No transition may inflate**: the schema has no field for
a score or a stance, and because every sentence is built only from this
layer's own enumerations the producible vocabulary is finite and a test
enumerates all of it. The synthesist may explain a transition code
established and cannot discover one.

**The framework may know that Committee X answered question Y with
verdict Z; it may never know what Z means** (the Crypto Committee
Protocol,
[`CRYPTO_COMMITTEE_PROTOCOL.md`](docs/architecture/CRYPTO_COMMITTEE_PROTOCOL.md),
accepted and built). Extracted from #112 and #113 rather than designed
ahead of them, and the extraction was a **relocation, not an
invention**: every decision Judgment History makes runs on *did it
speak*, *is this the same answer*, *does the question still apply* and
*one contract or two* — so the framework's logic was already generic and
only its vocabulary was not. **One line proved it**: `posture_of` read
`Verdict.MECHANISM_EVIDENCED` and decided it meant presence. That split
was used for wording only, so `JudgmentPosture` lost a member and lost
no information — a record carries the verdict token and the committee's
own sentence, and quoting is not interpreting.

A committee now owns its **verdict vocabulary, question, applicability
rule and economic semantics**; the framework owns identity/versioning,
the three applicability *states*, the answered/abstained/unavailable
trichotomy, evidence eligibility, support counting and the lifecycle.
`CommitteeJudgment` carries its own `CommitteeContract` — #113 passed
identity alongside, which let a caller file a judgment under a committee
that did not produce it. **`abstained_because` was measured redundant**
(a total bijection with applicability) and **kept anyway**: those are
Fee Capture's three reasons, and a second committee's fourth would not
be derivable. Proven by a test-only committee with **three verdicts**,
which is what catches a framework that quietly assumed a binary. Live
outcomes unchanged (HYPE/ETH/SOL evidenced, ARB/ADA/1INCH not, BTC wrong
instrument, TAO unestablished); store schema 2 reads schema 1 by
fallback, never migration.

**Two committees now coexist, and the matrix is the deliverable**
(Committee #2,
[`SUPPLY_GOVERNANCE_COMMITTEE.md`](docs/architecture/SUPPLY_GOVERNANCE_COMMITTEE.md),
accepted and built). Selected by measuring nineteen discovered questions
against the corpus, not chosen: `capital_committed` had the evidence but
failed on **independence** (same provider and path as fees) and on
**magnitude** ($70m against $42bn needs a threshold); `liquidity` and
`market_robustness` were already refused by S5. Supply governance won —
applicable to all eight, primary chain evidence, unrelated to fees, and
a structural answer S5.3 had already proved cannot be read as a grade.

**Both its verdicts are positive findings** (`CONSENSUS_BOUND` /
`GOVERNANCE_SET` — who can change the issuance rule), which is what
makes it unlike Fee Capture rather than a second view of it; Fee
Capture's pair is a presence and its negation. **BTC and 1INCH swap
sides**: Fee Capture declines BTC and asks 1INCH, this committee asks
BTC and declines 1INCH — the clearest evidence the two are not one
question twice. And **no model is asked anything**: the protocol
accommodates a committee with no model seam.

**The measurement that changed the design: every issuance rule stands at
`CLAIMED`**, so requiring `EvidenceStanding.ESTABLISHED` made the
committee silent about all three answerable assets. S1's corroboration
vocabulary was built for vendor claims and a chain's own parameters have
no second source — *where a fact came from is a second axis, never a
second standing* (S4.5). The gate is S5.1's Model C asked of a rule, and
a test asserts `EvidenceStanding` appears nowhere in the committee.

**Findings recorded, not solved**: `Confidence` saturates (8, 9 and 11
findings all read `MULTIPLE_OBSERVATIONS`); the model seam is
per-committee and nothing says so; `execution_unavailable` and
`evidence_insufficient` are not comparable across committees; and
`INSUFFICIENT_EVIDENCE` covers both *no such rule* (ARB) and *the rule
exists and we cannot read it* (ETH). The registry is a tuple and a
lookup, earned by a concrete failure and given no ordering that means
anything.

**Everything beside, nothing combined** (the Committee Assessment
Matrix,
[`COMMITTEE_ASSESSMENT_MATRIX.md`](docs/architecture/COMMITTEE_ASSESSMENT_MATRIX.md),
accepted and built). A projection of independent judgments and **not a
new judge**: for each registered committee the question, the conclusion
in its own words, the reason, the confidence and the evidence — with no
score, vote, agreement, weight, rank or common verdict scale, because
two committees answering different structural questions are not two
votes on one proposition. **Committee N+1 appears without touching the
layer**, proved with #114's three-verdict specimen; three guards search
the *source* of every matrix module, since the next aggregate would
arrive as a helper rather than a field.

**The cell shape was measured, not designed.** `evidence_count` is
syntactically shared and semantically incomparable (Fee Capture's 11 for
HYPE counts fee readings; Supply Governance's 11 for ADA counts rule
parameters), and `confidence` is **demonstrably** incomparable — so both
are carried per committee and neither is ever combined.

**Two defects the measurement found.** `judged_at` meant two different
moments — Supply Governance stamped the *chain reading* time, so two
convenings from one cached rule produced one record id and history said
the committee met once when it met twice, breaking #113's count. And
`because` was not persisted, leaving two genuinely different abstentions
indistinguishable; store schema 3 carries it. **PR #113's prose ban is
on a *model's reading of a judgment*, not on a committee's account of
its own outcome.**

**Recorded and deliberately unsolved**: there is no shared notion of
*acquired for committee N*, and the matrix is not the place to fix it —
it reads and must never acquire. `GET /committees/{symbol}` serves the
projection; it is **not** a dossier section, because placing it there
would decide where a collection of independent judgments belongs in the
investor's narrative, which is the deferred layer.

**The strongest useful statement, and never stronger** (Investor
Assessment,
[`INVESTOR_ASSESSMENT.md`](docs/architecture/INVESTOR_ASSESSMENT.md),
accepted and built). The layer between committee judgment and eventual
recommendation, earned because #116 showed internal vocabulary leaking
to the surface as though it were a conclusion: **`CONFLICTED` is a fact
about two readings; *we cannot tell you anything* is a fact about the
investor's question.** Six shapes, each observed in the corpus before it
was declared — precise / range / structural / qualified / uncertain /
insufficient — and **not ordered**, because a precise answer to a
question nobody asked is worth less than an honest bound on one they
did. `DIRECTIONAL` was specified and **not built**: nothing produces one
yet.

**A difference is not a failure.** TAO's two circulating estimates are
9.9% apart and bound a real answer — *"approximately 8.64 to 9.60
million across 2 available estimates"* — while HYPE's span 78% and one
exceeds the maximum, so the spread is the story. **No midpoint is ever
computed**, and a test asserts it appears nowhere.

**Two boundary fixes.** A prose failure is a **presentation** failure:
the validator is untouched and the refused sentence still reaches no
reader, but the refusal is recorded in `wording_refused` and the
structural answer survives — HYPE's Fee Capture answers
`mechanism_evidenced` where the word *buy* previously erased it. And a
vendor total exactly equal to the maximum is **qualified rather than
stated**, because S5 measured that substitution across 83 of 145 capped
assets.

**Recorded, unsolved**: `max_supply: null` and *field absent* are
indistinguishable in the provider, so *ETH has no cap* is **not**
currently supportable and is reported as unknown rather than asserted;
`MATERIAL_SPREAD` is one constant doing work across every quantity; and
Asset Quality's absolute bands still force a value across a threshold
this layer would express as a range.

**A token is not a company with different labels** (the Crypto Dossier,
[`CRYPTO_DOSSIER_UI.md`](docs/architecture/CRYPTO_DOSSIER_UI.md), built).
The first investor-usable crypto surface, and the audit that earned it:
`/executive/BTC/dossier` led with **conviction 46, agreement 0.5, safety
35 and the Investment and Risk Committees** — none of it from crypto
evidence — while Fee Capture, Supply Governance, the investor
assessment, Asset Quality, the intelligence layer and the journal
appeared nowhere. Six layers had reached the CLI and stopped.

**Its own endpoint, because the measurement said so**: the equity
dossier runs the brain pipeline and takes ~12s; the whole crypto
composition is **~19ms** of stored doors. One composes a *decision*, the
other composes what is *known*. `GET /crypto/{symbol}/dossier` reuses
the five existing adapters plus the two domain objects that already
serialise themselves, and adds four small ones.

**The frontend calculates nothing analytical** — no value, score,
applicability, interpretation, classification or verdict is recreated in
TypeScript, and **no fallback prose turns a measurement into economic
meaning**. Enforced three times: adapters carry the domain's sentence
beside every state, the parser *requires* it, and the page renders the
refusal where the backend declines to interpret. A test walks every key
at every depth for an aggregate.

**And it does change with the asset** — 9/12/15/9/4 questions asked, HYPE
alone with two entities, TAO with 15 undetermined and nothing refused,
and the two committees swapping sides between BTC and 1INCH. **The
finding the test produced: BTC and 1INCH have identical counts (9 asked,
10 refused) and are not remotely the same asset**, so a count is never
the differentiator — questions are named, grouped by applicability, and
the three groups are separated rather than sorted. `UNKNOWN` is never a
zero, `NOT_APPLICABLE` is never adverse, and no state is colour-coded.
Five deficiencies recorded and not solved, including that asset class
still cannot be resolved without the brain pipeline.

**A fund cannot receive evaluative meaning from a company question its
playbook does not ask** (the Fund Analytical Boundary, F1,
[`FUND_EVIDENCE_RESEARCH.md`](docs/architecture/FUND_EVIDENCE_RESEARCH.md) §9,
built). The measured defect: IB01.L — an accumulating US Treasury ETF —
rendered *"Business quality LOW (40)"* from Yahoo's `dividend_yield:
0.0`, the only readable company field, on a share class that cannot
distribute by design. The structural fix was **membership, not
machinery**: six consumers already keyed the boundary on
`AssetClass.has_no_company`, and ETF simply predated the property.
Around that one change: `CompanyFactsService` split the conflated
`is_token` flag (company fields key on the capability boundary,
token-shaped fields keep their exact membership — a fund is not a token
either); the quality signal refuses the whole company factor set for a
no-company asset, so no future provider field can score a fund; every
absence is worded as this platform's limit (*"company filing knowledge
is not part of the fund playbook"*) and never as a claim about what
funds publish; and the fund's expense ratio — already in the `.info`
response and previously discarded — is retained as a dated fact
(`fund_cost` on the dossier, composed at the route like the token
rating, reaching no score). The fund dossier remains a named future
specialization; F2 (*"what am I actually buying when I own this
fund?"*) is not started.

**A grounded fact may travel upward without its economic interpretation
travelling with it** (Zero Fake Meaning, `INVESTOR_ASSESSMENT.md` §6,
accepted and built). Invariant 10, and the semantic form of Invariant 1.
The defect was one sentence keyed by *quantity* rather than by asset —
*"it bounds how far the holder's share can be diluted"*, attached to
every maximum supply held — which is true of a network asset and
**inverted for a claim on a reserve**. Classified across all eight
assets first: the figures, the spreads, the S5 substitution guard and
the four judgment postures are economically invariant; a committee's
answer was **already licensed**, because a committee decides
applicability in its own economic terms and records the role it read it
from; and `_WHY` was the entire defect surface, licensed by nobody.

**The licensor was derivable, not invented.** `EvidenceDemand.token_fact`
already names which questions read which quantity, so a meaning is now
the question's own `matters_because` quoted verbatim, carried with the
applicability sentence for *this* asset. **BTC gained a reading it should
always have had** — two questions demand `max_supply`, and monetary
scarcity's own sentence warns that a stated cap is not the claim.

**And the pressure it found: `DECLINED` had never worked.** Consuming
`applicability_for` did not block the stablecoin, because
`applicability_for` returned `ASK` as soon as a composed lens asked —
so the refusal table was reached only for questions the lens union had
already dropped, and **13 of 13 entries were unreachable**. A stablecoin
trades, so it composes the market lens, and only the *composition* knows
that a claim on a reserve has no eventual supply to be diluted against.
A precedence reorder plus one decline; `capabilities`, the archetype set
and entity identity untouched, and no `EconomicRole` invented. A test
asserts the reorder changes exactly one answer corpus-wide. **Nothing
was solved by deletion**: every live asset keeps every reading, and only
a synthetic stablecoin — never added to the corpus — abstains. Its
reserve, redemption and peg questions stay named as `unmodelled`.

**Caches may accelerate acquisition; they may never become undeclared
analytical inputs** (Hermetic Evidence,
[`HERMETIC_EVIDENCE.md`](docs/architecture/HERMETIC_EVIDENCE.md),
accepted and built). The gitignored-cache trap fired **five times**, and
the common shape was never caching: **an analytical call declared a
*subject* and never an *evidence set*** — `judge("ADA")` — so the
service resolved its own evidence from one of **seventeen path
literals** relative to the process CWD. Measured: editing one field of
`data/cache/issuance_rules` flips ADA from `governance_set` to
`consensus_bound` with the caller declaring nothing. And the suite was
*writing* too — it created `data/cache/fx` in the developer's tree.

`app/infrastructure/evidence_root.py` owns the root
(`MOVRVEST_EVIDENCE_ROOT`, default `data`); every store builds its
default from `evidence_path(...)`, **resolved at construction and never
in a signature** — ruff caught three stores freezing it at import, which
is the same bug again. `tests/conftest.py` gained the third dimension it
was missing beside credentials and the wire: the root points at a temp
directory, so a test that forgets fixtures reads an **empty** store
rather than a machine. Four behavioural tests poison a *genuinely
readable* cache and prove the declared input wins — plus the inverse,
because the guarantee is *declared wins*, not *nothing works*.

**Historical judgments are auditable, not reproducible.** A record
carries the evidence digest, count and refs — enough to say *the
evidence changed* (#113's `EvidenceMovement`, cache-independent) and not
enough to reconstruct what the committee saw. Recorded, not fixed;
history stays append-only. **`MATERIAL_SPREAD` stays provisional** and is
not a definition of investor materiality.

**The CoinGecko narrative surface is web-only** — `/api/v3/news` is 401
PRO-only and `status_updates` is 404 — so the parse reads `data-`
attributes rather than layout, and reports `EventFeedHealth` when it
breaks: **a surface returning nothing and a surface returning nothing
*because it changed* must not look the same.**

The per-security dossier (`/executive/{symbol}/dossier`, rendered at
`apps/web/movrvest-web/app/dossiers/[symbol]`) is the surface that
consumes it:

- **Both understandings are on it** — `CompanyUnderstandingService`
  composes `BusinessUnderstanding` and `FinancialUnderstanding` beside
  the case. No analyst consumes them and the recommendation is identical
  without them.
- **The conclusion is `DecisionSynthesis`** — *because / despite /
  review if / uncertainty / decision*, deterministic, from canonical
  objects only, complete with the Executive Writer disabled.
- **The committees state positions, not actions** — `CommitteeOpinion`
  (`app/domain/committee/`) carries a stance over *referenced* findings,
  the rule that produced it, and what it could not settle. It is the
  reference implementation of the future Assessment layer; see
  [`docs/architecture/ASSESSMENT_CONVERGENCE.md`](docs/architecture/ASSESSMENT_CONVERGENCE.md).

Two rules this phase established, both worth applying to any new surface:

1. **A page view never fetches or asks a model.** Both knowledge
   services expose a read-only `established()` door that asks the store
   and stops; `knowledge()` and `statements()` acquire and must not sit
   behind a page. Guarded by stubs in
   `tests/test_company_understanding_service.py` that raise on any
   resolve or extract — a change that reintroduces the spend fails
   rather than bills.
2. **A fact's origin travels with it.** `FactOrigin.ESTABLISHED` (read
   from the filing and checked) versus `ASSESSED` (an analyst reading
   market data). Printed side by side without it, the weaker claim
   borrows the stronger's authority.

And one defect shape to watch for: **when a field reads identically
under every symbol, check whether it is built from portfolio or market
facts rather than the security's.** It has now been found and fixed
three times — in `context_strengths`, in `catalysts`, and in
`invalidation_conditions`, which answered "what would invalidate this
thesis?" with the account's own weaknesses under every company.

Two model seams, configured apart because they are different jobs: the
Executive Writer (`MOVRVEST_WRITER_*`, small model, opt-in behind a flag)
and the knowledge reader (`MOVRVEST_READER_*`, no flag — reading is how
the platform knows anything structural, and an unconfigured reader is
already an honest worded absence). Tests silence both; see
`tests/conftest.py`, and add any new settings-reading module to it.
API: `python -m uvicorn app.api.main:app --port 8000 --reload`.

---

## Verify the commit, not the working tree

Pre-commit stashes unstaged changes but **leaves untracked files in place**,
so hooks can pass on a tree the commit does not contain. This has already
shipped a commit that imported two files it did not include.

```bash
git archive HEAD | tar -x -C /tmp/headcheck && cd /tmp/headcheck \
  && source /path/to/.venv/bin/activate && python -m mypy app && python -m pytest -q
```

Run it before trusting any commit that adds files.

The pre-commit hooks need the venv on PATH:
`export PATH="$PWD/.venv/bin:$PATH"` before `git commit`.

---

## Invariants

These are not style preferences. Breaking them damages the product.

1. **Absent evidence is reported as absent, never estimated.** A plausible
   number on an investment dashboard reads as a measurement. If the platform
   cannot evidence a figure, it says so.
2. **Identity, grounding and applicability are independent invariants.**
   Grounding proves that cited content exists in the source. Identity
   proves that the source belongs to the intended security. Applicability
   proves that the cited content supports the fact it was cited *for*.
   None substitutes for another, and identity is enforced *before* the
   reading — a perfectly grounded, exactly cited reading of a genuine
   filing is still wrong when the filing is another company's, and
   nothing downstream can see that it happened. Learned twice, from `BTC`
   resolving against the SEC to a Bitcoin trust and from a ticker-to-ISIN
   lookup returning an Argentine CEDEAR for `ASML.AS`.
3. **A citation carries the relationship it was read from, or it is
   absent.** A span proves words exist; it cannot prove they support the
   claim beside them, and prompting cannot close that. So a quantitative
   citation is an address into a table this platform parsed, checked
   against the cell it names, and a share is arithmetic the platform
   performs over two checked figures. A narrative citation must
   establish **unambiguous ownership** between the cited text and the
   claim it supports. Two mechanisms serve that and neither is the
   invariant: the section the filer printed the words under, and — where
   the document offers no structure — position under the segment's own
   naming. Learned from one reading that cited a *column header* and got
   the shares right anyway, another that cited one sentence about
   restated figures as three segments' business, and a filing that named
   its segments only *after* describing them, inverting the positional
   partition rather than merely straining it.
4. **A segment is three claims, evidenced apart.** Identity, size and
   description fail independently: an inapplicable description leaves
   the segment named and measured, and says nothing about what it does.
   One span once proved all three, so a bad citation destroyed facts
   that something else had established.
5. **The Brain stores facts, never conclusions.**
6. **Analysts assess; only the Artificial CIO decides.**
7. **Communication explains decisions; it never makes them.**
8. **The dashboard presents; it never calculates.**
9. **One business concept, one implementation.**
10. **Zero Fake Meaning — Invariant 1's sibling, for semantics rather
    than arithmetic.** *An established number is authority to report the
    number, not authority to invent what the number means.* Evidence
    establishes facts; question contracts establish what a fact means
    for an applicable analytical question; committees establish their
    own economic judgments; the executive layer communicates licensed
    meaning and never authors it. A grounded fact may travel
    upward without its economic interpretation travelling with it, and
    the layer receiving it must not invent the missing half. An
    established supply number is not authority to say *dilution*;
    established fees are not authority to say *holder economics*; a
    market capitalisation is not authority to claim robustness where the
    question does not apply. Where the measurement is established and its
    investor meaning is not, show the measurement and **say that the
    interpretation is not established** — abstention is a sentence, not
    silence.

The UI labels its own honesty: every page declares its data provenance via
`<PageIntegrity>`, and cards carry a live / partial / placeholder pill. If
you make something real, update its pill.

---

## No new architecture without a product story

Every PR answers one question:

> **What becomes better for the investor?**

> *"Nothing, but the domain is cleaner."* → **the PR waits.**
>
> *"Recommendations become easier to trust."* → **ship it.**

A PR that waits is not a PR that is wrong. It is one whose product story has
not arrived. When a slice finally needs that ground, it is built inside that
slice — where the benefit is visible and the cost is charged against it.

Name the mechanism where you can: *"recommendations become easier to trust,
because the Quality Committee now reasons from established business
understanding"* is checkable, and *"it improves quality"* is not.

A decision **currently getting a wrong answer** is the same question answered
in the negative, and it ships: a defect, a seam that could spend money in
tests, a dependency that fails only in CI.

**The core architecture is frozen** — deliberately, not forever. Enough
exists to build several investor-facing capabilities. No new layers,
canonical objects, taxonomies or re-factored seams, and no completing a
designed step merely because it is designed. Constitution §23–24 carries the
full rule; only the owner lifts the freeze.

---

## Before you build

**Verify the import graph before believing any document, including this one.**

```bash
grep -rln "app.services.committees" app --include="*.py" | grep -v __pycache__
```

The repository previously carried four parallel "committee" implementations
while the docs labelled a dead one canonical and the live one legacy. That
cost real time. Check what actually imports a package before building on it
or deleting it.

**Reuse before creating.** The Communication layer, the per-security
analysis, and the investment-case aggregate all already existed and were
simply unwired. Search before writing something new.

---

## Working rhythm

Ship one vertical slice at a time: a complete capability from Brain to a
surface the investor sees, fully tested, gates green, then commit.

**Start a new session at slice boundaries**, not mid-slice. Each slice ends
green and committed, so the repository fully describes the state and a fresh
window loses nothing.

---

## Environment notes

- The repository lives on the local SSD at
  `/Users/movr/AI Projects/etoro-agentic-trader`, moved 2026-08-07 after an
  iCloud `fileproviderd` sync storm throttled the old path to ~3 file
  reads/second — the identical suite that "hung" there runs in 4s here. A
  stale copy may linger in iCloud Drive
  (`…/com~apple~CloudDocs/AI Agents/etoro-agentic-trader`); do not work in
  it. If a file appears with a ` 2.py`-style suffix it is an iCloud
  conflict-copy remnant; `.gitignore` covers `* [0-9].*`.
- The preview-server tooling cannot access the iCloud path — run dev servers
  with plain background shell commands instead.
- Yahoo Finance rate-limits (401s). Per-security signals can flip between
  runs, which can flip a decision. Do not treat a single run as truth.
