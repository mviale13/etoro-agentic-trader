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

| Area | Status |
|------|--------|
| Ruff | 🟢 Clean |
| Mypy | 🟢 Clean |
| Pytest | 🟢 569 passing |
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
- Every decision is recorded, and the next cycle says what changed
- Every market observation is recorded, and the next cycle says what the
  market did — the mood, the volatility band and the sentiment reading,
  each stated with the figures behind it
- The dashboard change feed reports the decisions the CIO actually changed
  and the market movements that were actually recorded
- The research page runs the CIO over the investor's own watchlists

## Recently completed

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
what the market did. Why a given movement matters to *this* investor — which
holding it touches, and how much — is still open, and needs a measure of
which moves matter before it can be answered honestly.

---

# Long-Term Vision

MOVRvest is an Artificial Chief Investment Officer.

Its purpose is not to predict markets. It is to help investors consistently
make better investment decisions by transforming verified evidence into
transparent, explainable and trustworthy executive recommendations.

Trust is the product. Everything else exists to support it.
