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
| How does the pipeline work? | [`docs/architecture.md`](docs/architecture.md) — **v5.0 section only** |
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

python -m pytest -q            # ~1500 tests, fast
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
(accepted). The store holds `CompanyKnowledgeObservation`s (schema 11,
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
