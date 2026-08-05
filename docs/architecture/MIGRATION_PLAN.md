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
- [ ] Holdings absent from every watchlist cannot be analysed. Naming is
      handled (the broker's own symbol, else a `#id` placeholder), and an
      unresolved holding now reaches the brief with the honest "no
      security-level analysis" line rather than a misleading one. What
      remains is evidencing it: `SecurityPerception` still needs a
      `WatchlistItem` for the asset type, so a held instrument no watchlist
      names is drawn without a signal. Rare in practice — eToro's
      "RecentlyInvested" watchlist carries held instruments
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
