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
| Pytest | 🟢 348 passing |
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

- Yahoo fundamentals are rate-limited and uncached; signals can flip between
  runs, and a flipped signal can flip a decision
- Crypto tickers do not resolve (`SOL` needs `SOL-USD`)
- A holding absent from every watchlist cannot be named or analysed
- Research covers a capped number of candidates per cycle, because
  fundamentals are uncached and the provider rate-limits. The page reports
  how many it could not reach
- Holdings are not classified by asset type, which blocks allocation-drift
  scoring and the crypto policy limit

## Reasoning

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
