# eToro MCP — Read-Only Acceptance Measurement

Status: **research, conclusion C (NOT READY)**. No implementation. No
production data written. No trade tool called, prepared or inspected for
execution.

Measured 2026-08-20 against `https://mcp.public-api.etoro.com`,
skill `1.17.0`, API `v1.352.0`. (`docs/ETORO_API.md` was generated from
`v1.326.0` on 2026-08-03 — the catalogue has moved 26 minor versions and
now reports **184 routes**.)

---

## 0. The blocker that shaped this measurement

**The authenticated half could not be executed.** The eToro connector is
enabled on the owner's claude.ai account — it appears in Connectors as
`eToro · Web · Custom · connected` — but its tools were **not present in
this session's tool registry**. Three separate searches (by name, by
account vocabulary, by market vocabulary) returned no eToro tool. Local
configuration confirms it: `~/.claude.json` carries no `mcpServers` key
and nothing under `~/.claude/` had changed. Connectors are enumerated when
a session starts; this session started before the connector existed.

So the required order in the brief — profile-and-scopes first, then
portfolio summary, balances, instruments overview — **was not run at all**.

| Authenticated calls budgeted | Authenticated calls made |
|---|---|
| 8 | **0** |

What *was* run is the half the brief permits without credentials: route
and tool contract inspection. **Discovery needs no credentials** (stated
in `docs/ETORO_API.md` and confirmed here), so the tool catalogue, the
route catalogue and full OpenAPI specifications were readable.

**Six unauthenticated discovery calls**, all HTTP 200, all
`0.09–0.14 s`:

| # | Tool | Argument | Bytes |
|---|---|---|---|
| 1 | `tools/list` (protocol) | — | 39,333 |
| 2 | `get-all-routes` | query `portfolio pnl` | 1,585 |
| 3 | `get-route-spec` | `getTradingInfoRealPnl` | 58,146 |
| 4 | `get-all-routes` | tag `Balances` | — |
| 5 | `get-route-spec` | `getBalances` | 20,802 |
| 6 | `get-all-routes` | tag `Market Data` | — |

Mode: not applicable — no connection was authenticated, so no demo/real
determination was made. Rate-limit metadata: **not exposed on any
discovery response**; the specifications *document* the limits (below),
which is a different thing from a live header.

No account data of any kind was received, so nothing in this document
could disclose a balance, a holding or a value. Raw responses live in an
isolated scratch area outside the repository and outside `data/`.

**This is the load-bearing finding: the replacement blocker does not
depend on the missing calls.** It is a property of the route schema,
established below, and it would survive a fully successful authenticated
run.

---

## 1. What MOVRvest does today

Five components, read on `main` `3043f06`.

`EtoroAccountBroker.snapshot()` (`app/brokers/etoro_account.py`) issues
**one** request — `/api/v1/trading/info/{demo|real}/pnl` — and builds
`AccountSnapshot`. `AccountService` is a pass-through.
`PortfolioService.analyze()` turns that into `PortfolioSnapshot`.
`PortfolioPerception.execute()` then resolves symbols through
`InstrumentSymbolResolver` (watchlists → instrument catalogue →
`#<id>` placeholder) and adds drawdown from a separate balance-history
request.

Nine eToro REST endpoints are live in the codebase:

```
/api/v1/me                                        identity + granted scopes
/api/v1/trading/info/{demo,real}/pnl              the account snapshot
/api/v1/watchlists                                symbol resolution
/api/v1/market-data/instruments                   catalogue fallback
/api/v1/balances/history                          drawdown
/api/v1/trading/info/trade/history                trade history
/api/v1/trading/info/trade/demo/history           trade history (demo)
/api/v1/money/accounts/cash/{account_id}/transactions
```

### Provider-native versus MOVRvest-derived

The distinction the brief asks for, and it is stark. From the `pnl`
route MOVRvest receives, per position: `instrumentID`, `units`,
`amount`, `unrealizedPnL.pnL`, `exposureInAccountCurrency`. At account
level it receives `credit`, `unrealizedPnL`, `accountCurrencyId`, and
the order/mirror arrays.

Everything else on the dashboard is **arithmetic MOVRvest performs**:

| Field | Origin |
|---|---|
| available cash | **derived** — `credit − Σ pending order amounts` |
| invested | **derived** — `Σ position amounts + pending + external costs + mirror terms` |
| equity / total value | **derived** — `cash + invested + unrealized` |
| market value per holding | **derived where `exposureInAccountCurrency` is absent** — `invested + unrealized` |
| unrealized P&L | provider-native per position, **summed** by MOVRvest |
| positions count | count of **trade rows**, not securities |
| symbol | **not from this route at all** — resolved later, from watchlists |
| asset class | **not from this route** — from the watchlist item's `asset_type_id` |

### Two defects found in the existing path, independent of MCP

**(a) `last_sync` is a response-receipt time, not an observation time.**
`EtoroAccountBroker.snapshot()` sets `timestamp=datetime.now(UTC)` after
the fetch returns; `PortfolioService.analyze()` copies it to
`PortfolioSnapshot.last_sync`. PR #221 corrected the capital gate from
ageing the *Brain assembly* stamp to ageing `last_sync` — a real
improvement, and it moved the clock one hop closer to the broker without
reaching it. `last_sync` still says *when MOVRvest received bytes*, never
*when eToro observed the account*. The 15-minute portfolio gate is
therefore measuring this platform's own latency, not the account's age.

**(b) An unavailable cash figure becomes a measured zero.**
`EtoroAccountBroker` is careful: `cash = None if credit is None`, so
absence is preserved in `AccountSnapshot.cash_usd: float | None`. Then
`PortfolioService._non_negative(None) → 0.0` collapses it, and
`Allocation.cash` becomes `0.0`. Downstream in #221, `capacity_for`
reads that zero, computes `funding_room = max(0, 0 − 40) = 0`, and the
envelope states *"the portfolio currently has no additional capacity
because the cash floor (funding room) leaves no room."* The refusal
shape is safe, but the **sentence asserts a measured fact about the
account when the true state is that cash is unknown** — Invariant 1,
in the one place the capital envelope speaks to the investor.

Both are recorded, not fixed: this is a research slice.

---

## 2. What the MCP exposes

Thirteen tools. Eight are outside this measurement's permitted set and
were neither called nor inspected for execution: `execute-write`,
`prepare-trade`, `place-trade`, `get-trader-profile-summary`, `get-tags`,
`execute-read`, plus the two trade paths named in their own descriptions.

### `get-my-portfolio-summary`

Returns, per its contract: account totals (**total value, available
cash, frozen cash, balance, unrealized P&L, used margin**), **one
condensed row per held instrument** sorted by value — symbol, display
name, logo, invested, current value, P&L, P&L %, units, current rate,
average open rate, leverage, exposure and **position count** — plus
copied traders and pending orders. Per-position detail is opt-in
(`includePositions`, default false). `account` argument selects
`real` (default) or `demo`.

Three contract statements matter:

- *"All prices and P&L come from the SAME portfolio snapshot, so the
  numbers are mutually consistent — do NOT re-price rows against live
  market-data quotes."* Internal consistency is asserted; **no
  observation time is named anywhere in the description.**
- `warnings` lists enrichment that was unavailable (symbols, display
  names, copied-trader usernames) — *"the money numbers remain
  authoritative"*. **Partial-response semantics exist and are typed.**
- `error` + `statusCode`, where *"0 = timeout/unreachable"*, and 429
  carries `retryAfterSeconds`. **Degradation semantics exist.**

Totals here cover the **Trading account only**.

### `get-my-balances`

Covers **every** account — Trading and its sub-accounts, Cash, Crypto,
Options, MoneyFarm, Spaceship. Relayed *verbatim*: *"this tool converts
nothing, sums nothing and subtotals nothing."*

The contract carries four warnings that read like this repository's own
invariants:

- A `fieldGuide` names the spendable field **per account type**, because
  it differs: `equityDetails.available` for Trading/Cash/Options/
  MoneyFarm, `equityDetails.spendableBalanceInFiat` for Crypto, and
  **nothing at all** for Spaceship. *"Never assume 'available' exists."*
- *"`totalBalance` and each row's `balance`/`displayBalance` are
  PORTFOLIO VALUE, not spendable cash"* — one exception, Cash accounts.
- Every `equityDetails` amount is in that account's **own native
  currency**, and *"the equityDetails object carries no currency marker
  of its own"* — the row's `currency` and `exchangeRate` must be used.
  A GBP available sits beside a USD displayBalance.
- **`"A 502 or a statusCode 0 means the balance COULD NOT BE READ: it is
  never a zero balance and must never be reported as one."`**

That last sentence is Invariant 1, stated by the provider. It is the
strongest single argument in favour of this integration — and, as §1(b)
records, it is a rule MOVRvest's own `PortfolioService` currently breaks.

**Scope**: requires `etoro-public:money.balance:read`, *"a SEPARATE grant
NOT implied by `etoro-public:real:read` or any account umbrella."*

### `get-instruments-overview`

Batch of 1–100 instruments in **one** call, addressable by `symbols`
and/or `instrumentIds` (or a free-text `query`). Returns per instrument:

- market identity — symbol, name, logos;
- a live quote — **`ask`, `bid`, `spread`, `asOf`**;
- performance — `previousClose`, daily/weekly/monthly change %;
- **the user's trading eligibility summary** — `allowOpenPosition`,
  **min position exposure**, **max units per order**, allowed long/short
  leverages, MIT/entry-order/trailing-stop-loss support, W-8BEN
  requirement, fractional-vs-whole units.

*"Eligibility reflects the CONNECTION's account — there is no account
argument."* Unknown inputs come back in `notFoundSymbols` /
`notFoundInstrumentIds`, *"never as an error while at least one
instrument resolved"*; `warnings` names degraded sections and *"the
matching fields are null"*.

### `get-my-profile-and-scopes`

Returns `gcid`, `realCid`, `demoCid`, username, personal fields, and
**`scopes` — the OAuth scopes actually granted** — plus `authChannel`
(`bearer` or `keys`). Two documented rules: `etoro-public:real:read` /
`:write` are umbrellas that include the matching `trade.real`
permissions, while `money.balance:read` and `market-data:read` are
separate grants. *"Scopes reflect what the CONNECTION was granted, not
user-level account state."*

Note for the objective's item 8: **the connection is not inherently demo
or real.** Both `realCid` and `demoCid` come back, and mode is a
*per-call argument*. MOVRvest's `Settings.trading_mode` picks a path
(`/demo/pnl` vs `/real/pnl`) and raises without one; the MCP defaults to
`real`. A migration would move that choice from configuration into every
call site — a real behavioural difference, not a detail.

---

## 3. The provenance blocker, established from the schema

The question the brief poses as architecture question 4 is answerable
without any authenticated call, because `get-route-spec` returns the
full OpenAPI document.

`get-my-portfolio-summary` is built on **`getTradingInfoRealPnl` —
`GET /api/v1/trading/info/real/pnl`**. That is byte-for-byte the route
`EtoroAccountBroker` already calls.

Its 200 response is `PortfolioResponseWithPnl`, whose single property is
`clientPortfolio` → schema `ClientPortfolio`, which has **thirteen
top-level properties**:

```
positions  credit  mirrors  orders  ordersForOpen  ordersForClose
ordersForCloseMultiple  bonusCredit  unrealizedPnL  accountCurrencyId
stockOrders  entryOrders  exitOrders
```

**None of them is temporal.** The route states no account observation
time.

Temporal fields do exist in the document, and every one belongs to a
child object, not the account:

| Field | Where it lives | What it dates |
|---|---|---|
| `timestamp` | closed-position / mirror-position objects | *"Timestamp of the PnL calculation"* for **that position** |
| `openDateTime` | orders, positions | when the order was placed |
| `lastUpdate` | orders | last update **to that order** |
| `startedCopyDate` | mirrors | when copying began |

A closed position's PnL-calculation time is not the account's
observation time, and reading it as one would be exactly the
substitution this platform has ruled against repeatedly.

`getBalances` is worse for this purpose: a scan of its complete
specification returns **zero** keys matching time/date/update/asOf/
sync/stamp. There is no observation time on the balances route either.

So: **on the evidence available, no eToro route this measurement
inspected states when the account was observed.** The MCP tool layer
could in principle stamp its own `asOf` on the portfolio summary — its
description does not mention one, and only a live call would settle it.
That single unanswered question is the difference between conclusion C
and a possible future B, and it cannot be closed from documentation.

By contrast the **quote** side does carry `asOf` on every instrument in
`get-instruments-overview`. Account provenance is missing; quote
provenance is present.

---

## 4. The eight objectives

| # | Responsibility | Contract-level finding | Live-verified |
|---|---|---|---|
| 1 | Portfolio snapshot | Supplied, richer than today's, **one call**, aggregated per instrument | ✗ |
| 2 | Current balances | Supplied verbatim across **all** account types; separate scope; per-type spendable field | ✗ |
| 3 | Holding aggregation + identity | **Provider-side aggregation**; symbol travels with the row; `instrumentIds` addressable | ✗ |
| 4 | Snapshot freshness / provenance | **Absent at route level** (§3) — the blocker | ✗ |
| 5 | Quote + market status | `ask`/`bid`/`spread`/`asOf` per instrument; market-open status **not named** in the contract | ✗ |
| 6 | Spread + executability | `allowOpenPosition`, min position exposure, max units/order — **account-specific** | ✗ |
| 7 | Symbol + asset-class resolution | Symbol yes, both directions; **asset class not named** in either contract | ✗ |
| 8 | Account mode + scopes | Scopes yes, explicitly; **mode is per-call, not a connection property** | ✗ |

Two omissions worth naming, because they are the kind that get assumed:
**market-open status** and **asset class** appear in no inspected
contract. MOVRvest derives asset class from the watchlist item's
`asset_type_id` — the very field #133 found misclassifying SPCX. Nothing
here replaces it.

---

## 5. Required controls

Seven were specified. **Six could not be executed**; one was settled
from documentation. Reporting them as unexecuted rather than inferring
them is the point.

| Control | Status | What is known |
|---|---|---|
| **A** Portfolio totals vs balances | **NOT EXECUTED** | Contract shows the comparison is only well-defined for the **Trading** row: portfolio summary is Trading-only, balances spans every account, and `balance` is portfolio value rather than spendable cash. A naive total-to-total comparison would be a category error, and any tolerance must be stated per currency because `equityDetails` is in native currency |
| **B** Aggregation | **SETTLED (documentation)** | *"one condensed row per held instrument"* plus a `position count`; per-trade rows opt-in via `includePositions`. Aggregation is **provider-side** |
| **C** Freshness | **NOT EXECUTED**, but §3 stands | No account observation time in either route schema. Quote `asOf` documented per instrument. Whether the MCP layer adds an account stamp is unresolved |
| **D** Absence vs zero | **NOT EXECUTED** | Contract evidence is strong in both directions: `notFoundSymbols`/`notFoundInstrumentIds` preserve absence; degraded sections go **null** with a named warning; a 502/statusCode-0 balance *"must never be reported as"* zero. **Counter-evidence**: `includeZeroBalances` defaults **false**, so a genuinely zero account is **omitted from the response entirely** — absence and zero are conflated at the *membership* level unless the flag is set |
| **E** Identity | **NOT EXECUTED** | Contract names symbol, display name and eToro instrument id. **No ISIN, CIK or FIGI is mentioned in any inspected contract.** Nothing here establishes temporal issuer identity — the PARA lesson (#212/#215) is untouched by this integration |
| **F** Executability | **NOT EXECUTED** | Contract separates the two cleanly: `spread`, `previousClose` and performance are descriptive; `allowOpenPosition`, min position exposure, max units per order, leverage bands, W-8BEN and fractional-unit support are **account-specific constraints** |
| **G** Repeatability | **NOT EXECUTED** | Requires two authenticated calls |

A further hazard found in the `getBalances` specification and worth
carrying forward: unrecognised `accountTypes` values are **silently
ignored**, and *"if none of the supplied values are recognised the
filter is dropped and all account types are returned"*. A filter that
silently does not apply is a refusal that never happens.

---

## 6. Architecture questions

**1. Can MCP replace the existing account snapshot request?**
Not yet, and the reason is provenance, not capability. It supplies more
than today's path and in one call, but it cannot supply the account
observation time (§3), and the replacement would inherit that gap while
appearing more authoritative. It would also be adopted unverified — zero
authenticated calls were made.

**2. Can it replace watchlist-based symbol resolution?**
At contract level, yes, and this is the strongest candidate.
`get-my-portfolio-summary` carries the symbol on each holding row, and
`get-instruments-overview` resolves up to 100 `instrumentIds` to symbols
in one call. That would retire `InstrumentSymbolResolver`'s two-step
watchlist→catalogue path. Two caveats: `warnings` can report symbols
unavailable, so the `#<id>` placeholder path must remain; and **asset
class is not offered**, so the watchlist `asset_type_id` join survives
regardless.

**3. Can it remove MOVRvest's manual aggregation of one row per trade?**
Yes at contract level — rows arrive aggregated per instrument. But
MOVRvest's aggregation exists because of a specific defect: two BTC buys
of 20.0% and 0.5% read as a compliant 20.0% against a 20% limit. Moving
that responsibility to the provider means trusting a boundary this
measurement never observed. `#221`'s `_portfolio_weights` should keep
aggregating until an authenticated run proves the rows are what the
description says.

**4. Can it provide the actual `last_sync` the 15-minute gate needs?**
**No, on current evidence.** §3. And the finding cuts deeper than the
question: MOVRvest does not have a real `last_sync` *today* either —
§1(a) — so the gate is currently ageing this platform's own receipt
clock. MCP does not fix that; it also does not worsen it.

**5. Can it distinguish an unavailable cash figure from measured zero?**
At the response level, **yes, and better than MOVRvest does today** —
the balances contract states the rule explicitly. But `includeZeroBalances`
defaulting false means an account holding nothing simply disappears, so
the distinction must be read as *account present with unreadable figure*
versus *account absent*, which is a third state. The genuine defect here
is on our side (§1(b)) and can be fixed without any MCP work.

**6. Can instrument overview close part of the executability gap?**
Part of it, and it is important to say which part. Min position
exposure, max units per order and `allowOpenPosition` are real
account-specific constraints and would populate fields #221 currently
has no source for. They do **not** close the *liquidity* gap:
`LIQUIDITY_UNMEASURED` is about depth and traded volume, and a spread is
not depth. A bid/ask spread must never be rendered as a liquidity
ceiling — that substitution would be exactly the kind Invariant 10
forbids.

**7. Which existing custom calls become redundant?**
Candidates, on contract evidence alone: `/trading/info/{mode}/pnl`
(wrapped verbatim), `/api/v1/me` (wrapped by
`get-my-profile-and-scopes`; MOVRvest's `EtoroIdentityBroker` and
`ApiGrant` already read it with correct absence semantics),
`/api/v1/watchlists` and `/market-data/instruments` for the resolution
path only.

**8. Which capabilities remain necessary?**
Balance **history** for drawdown — and this is decisive: there is **no
dedicated MCP tool** for `/api/v1/balances/history`. Reaching it means
`execute-read`, the generic route executor, which is a thinner guarantee
than a purpose-built tool. Also unreplaced: trade history, cash
transactions, asset-class classification, and every non-eToro evidence
family.

**9. Does MCP reduce calls and failure surfaces, or wrap the same
fragmented routes?** Both, honestly. It genuinely reduces **calls** —
today's portfolio + symbols is `pnl` + `watchlists` (+ catalogue
fallback); MCP is one call carrying symbols already. It does **not**
reduce **failure surfaces**: `get-my-portfolio-summary` executes the
identical upstream route, so every upstream failure remains, and the MCP
relay is one additional hop and one additional dependency. The `pnl`
route's own budget is *"SHARED across 3 endpoints"*, and `getBalances`
sits in the 60-req/60-s default shared pool — the rate-limit arithmetic
does not improve either.

**10. What is the narrowest valuable production adoption?**
`get-instruments-overview`, used for nothing but **quote provenance and
account-specific executability on securities already under
consideration** — leaving the account snapshot, aggregation, balances
and symbol resolution exactly where they are. It is one read-only call,
it is batched, it touches no account-state path, it needs only
`market-data:read`, and it feeds two fields #221 currently cannot
source: a quote `asOf` per exact symbol, and a minimum position size.
It is also the only candidate whose value does not depend on the
unresolved provenance question.

---

## 7. Conclusion — C, NOT READY

**Two independent blockers, one procedural and one structural.**

**Authentication was never exercised.** Zero of eight budgeted calls
were made, because the connector is not present in this session. Every
live control (A, C, D, E, F, G, and B's live half) is unexecuted. No
integration should be adopted on documentation alone, however good the
documentation — and this documentation is unusually good.

**Account observation time is absent from the route schema.**
`ClientPortfolio` has thirteen top-level properties and none is
temporal; `getBalances` has no temporal key at all. Every timestamp in
the portfolio document belongs to a position or an order. This blocker
is established from the specification and would survive a completely
successful authenticated run, which is why it is reported as structural
rather than provisional.

The contract evidence points toward **B (corroboration ready,
replacement not ready)** as the likely outcome once authentication is
available — the provider's own absence-versus-zero rule, its typed
`warnings`/`error`/`statusCode` degradation vocabulary, provider-side
aggregation and account-specific eligibility are all genuinely stronger
than what MOVRvest holds today. But B is a claim about live behaviour,
and this measurement observed none.

### Re-entry conditions

1. A session that actually carries the connector — the tools must appear
   in the registry before anything else is attempted.
2. The eight-call sequence in the brief's required order, unchanged.
3. One question answered first, because it decides everything else:
   **does `get-my-portfolio-summary` return an account observation
   timestamp that the underlying route does not carry?** If yes, its
   provenance must be established — computed by the relay, or passed
   through from somewhere this measurement did not find. If no,
   replacement stays blocked and corroboration is the ceiling.

### Recorded, not fixed — and not dependent on any of the above

- `last_sync` is a response-receipt time, not a broker observation time
  (§1a). #221's capital gate ages it.
- `PortfolioService._non_negative` converts an unavailable cash figure
  into a measured zero (§1b), and #221's envelope then states that the
  portfolio has no room — a claim about the account, from an absence.
- `docs/ETORO_API.md` is 26 minor versions stale (`v1.326.0` against a
  live `v1.352.0`).

Neither defect is an MCP question. Both are ours, both are in the path
the Capital Action Envelope reads, and both can be fixed with no
integration at all.
