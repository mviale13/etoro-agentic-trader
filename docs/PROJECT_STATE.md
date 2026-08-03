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
| Pytest | 🟢 430 passing |
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
- `GET /executive/portfolio` — every holding, ranked by conviction
- `GET /executive/{symbol}` — one investment case
- `GET /brain/` — portfolio facts, investor observation and DNA
- `GET /research/candidates` — the watched securities, judged and ranked
- The dashboard renders real account data and a real brief
- Every decision is recorded, and the next cycle says what changed
- The dashboard change feed reports the decisions the CIO actually changed
- The research page runs the CIO over the investor's own watchlists

## Recently completed

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

- Cached evidence carries its true observation date, but no surface shows
  it: an investor cannot yet see that a company's fundamentals are a day old
- `TAO` and `HYPE` have no plain `-USD` listing on Yahoo. Both are reported
  unpriceable rather than guessed at under a disambiguated ticker
- A holding absent from every watchlist cannot be named or analysed
- Research covers a capped number of candidates per cycle, because
  fundamentals are uncached and the provider rate-limits. The page reports
  how many it could not reach
- A crypto case cannot progress past INVESTIGATE, and now says why: the
  platform judges a case on business quality and valuation, and a token has
  neither. That is a limit of this platform, stated as one. Assessing crypto
  properly needs token fundamentals no provider here supplies

## Reasoning

- Every gate now clears on measured evidence, and RECOMMEND is reached.
  Valuation is what holds most candidates at PREPARE, which is the gate
  doing its job. Fit reads 99 for all of them — honestly, on an account
  that is 97% cash with no position above 0.5% — so nothing on live data
  yet demonstrates it separating one security from another
- Portfolio-level drawdown is still unmeasured: it needs position history,
  which nothing records. Security-level drawdown is measured

- `consistency_score` measures the investor's own consistency. The journal
  records what the CIO decided, not what the investor did about it, so the
  score still reports the neutral midpoint
- No decision is scored against its outcome; the journal is a record, not a
  track record
- `app/analysts` holds real per-security fundamental analysis the canonical
  reasoning layer does not yet own

## Delivery

- API routes construct services directly, so they cannot be tested without
  network access
- The change feed reports recorded decision changes only; market and macro
  movements are not recorded anywhere
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

The change feed reports what the Artificial CIO changed its mind about.
Extending it to what moved in the market and why it matters to this investor
needs those movements recorded first.

---

# Long-Term Vision

MOVRvest is an Artificial Chief Investment Officer.

Its purpose is not to predict markets. It is to help investors consistently
make better investment decisions by transforming verified evidence into
transparent, explainable and trustworthy executive recommendations.

Trust is the product. Everything else exists to support it.
