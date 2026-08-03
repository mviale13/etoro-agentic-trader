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

## Evidence quality

- [ ] Portfolio-level drawdown needs position history, which nothing
      records. Security-level risk is measured; the account's is not
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
- [ ] eToro identity carries no reading, because the watchlist fetch
      records no time. Plumbing that is the other half of two-source
      provenance
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
- [ ] Holdings absent from every watchlist cannot be named or analysed
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
- [ ] A security no watchlist names now draws no committee view at all, so
      `InvestmentThesis.confidence` is None and the brief says agreement was
      not measured. Correct, but it means `movrvest evaluate` on an unknown
      symbol reports less than it used to
- [ ] Signal evidence has no polarity, so favourable and adverse findings
      cannot be told apart. `InvestmentThesis.strengths` and `.risks`
- [x] Signal evidence carries polarity. `Finding` pairs each statement
      with the `Sense` the signal read it with, so `InvestmentThesis`
      states the security's own strengths and risks, and the portfolio and
      market keep `context_strengths` and `context_risks`
- [ ] `consistency_score` needs a record of the investor's own actions. The
      decision journal records the CIO's decisions, not what the investor did
      with them
- [ ] No decision is scored against its outcome; the journal is a record, not
      a track record
- [ ] `app/analysts` holds real per-security fundamental analysis that the
      canonical reasoning layer does not yet own

## Delivery

- [ ] API routes construct services directly, so they cannot be tested
      without network access
- [ ] The change feed covers recorded decision changes only. Market and macro
      movements are not recorded anywhere, so they are absent from it
- [ ] `ExecutivePipeline` recomputes symbol-independent reasoning per holding

## Structure

- [ ] `app/services` (66 modules) still mixes load-bearing and incidental
      code
- [ ] Analysts accept `Brain | BrainContext`; narrowing them retires the
      legacy `BrainContext`
- [ ] `ClaimEngine.test.ts` has pre-existing TypeScript errors (`vitest` is
      not installed); excluded from the Next build graph, so it does not
      break the gate
- [ ] `docs/` holds ~20 documents, several superseded and a few iCloud
      conflict copies. Consolidate or mark them, as was done for
      architecture v4.0

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
