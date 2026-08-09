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
observes; `--model` is inspection and never changes what governs).

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

The per-security dossier (`/executive/{symbol}/dossier`, rendered at
`apps/web/movrvest-web/app/dossiers/[symbol]`) is the surface that
consumes it:

- **Both understandings are on it** — `CompanyUnderstandingService`
  composes `BusinessUnderstanding` and `FinancialUnderstanding` beside
  the case. No analyst consumes them and the recommendation is identical
  without them.
- **The conclusion is `DecisionSynthesis`** — *because / despite /
  review if*, deterministic, from canonical objects only, complete with
  the Executive Writer disabled.

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

## Before you build

**Answer this first, out loud, before any work starts:**

> **Which investor-facing decision becomes better because of this change?**

Name the decision, the mechanism, and what an investor could see afterwards
that they could not before. *"The recommendation is more trustworthy because
the Quality Committee now reasons from established business understanding"*
is an answer. *"None, but the architecture is cleaner"* is not — push back,
and say so.

A decision currently getting a **wrong** answer counts: a defect, a seam that
could spend money in tests, a dependency that fails only in CI. That is the
same question answered in the negative, not an exception to it.

**The core architecture is frozen** — deliberately, not forever. Enough
exists to build several investor-facing capabilities. No new layers,
canonical objects, taxonomies or re-factored seams, and no completing a
designed step merely because it is designed. Structural work a passing slice
genuinely needs travels *inside* that slice. Constitution §23–24 carries the
full rule; only the owner lifts the freeze.

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
