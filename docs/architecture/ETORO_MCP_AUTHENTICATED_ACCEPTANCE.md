# eToro MCP — Authenticated Read-Only Acceptance

Status: **research**. Two conclusions, reached separately:

| Question | Conclusion | Owner ruling (§9) |
|---|---|---|
| Portfolio / account **replacement** | **NOT READY** | **rejected** |
| Quote and executability **enrichment** | **READY** | **approved as a capability**, production blocked on credential scope |

No production implementation. No trade tool called, prepared, or loaded
into this session. Measured 2026-08-20 against the connector's
authenticated MCP connection.

---

## 0. What was spent, and what was refused

**Five authenticated calls of a budget of eight. No retries.** Every one
returned HTTP 200; none needed a second attempt.

| # | Tool | Argument | Outcome |
|---|---|---|---|
| 1 | `get-my-profile-and-scopes` | — | 200 |
| 2 | `get-my-portfolio-summary` | `account=demo` | 200 |
| 3 | `get-my-balances` | `includeZeroBalances=true` | 200 |
| 4 | `get-instruments-overview` | 4 symbols, one batch | 200 |
| 5 | `get-my-portfolio-summary` | `account=demo`, repeat | 200 |

Three calls were left unspent because the remaining questions were
answered by schema or by the responses already held. The `demo` account
was chosen because it is the repository's declared `TRADING_MODE`.

The instrument batch was one held equity (selected in memory and not
named here), plus three controls that are **not** account holdings and
are named so the measurement is reproducible: `KO` (stable large-cap
equity), `ADA` (crypto) and `ZZZZNOTASYMBOL` (deliberately invalid).

**Only read-only tool schemas were loaded into this session.**
`prepare-trade`, `place-trade` and `execute-write` were deliberately not
fetched, so no write-capable tool was callable at any point.

Nothing in this document contains an account identifier, a username, a
profile field, a balance, a portfolio value, a P&L figure, a holding
symbol, a quantity or an allocation percentage. Comparisons were
performed in memory; only field availability, record counts, timestamp
ages and difference classes are reported. No raw response was written to
disk, and `data/` was not touched.

### The safety finding that outranks the rest

The connection's granted scopes include **`etoro-public:trade.real:write`**
and `etoro-public:trade.demo:write`, alongside eleven other `:write`
grants. **The read-only discipline observed here is entirely
self-imposed.** Nothing in the credential prevents this connection from
placing a real-money order; the only thing standing between the MCP and
a live trade is the operator's restraint and, on our side, the fact that
MOVRvest has no write path at all.

That is worth stating plainly before any adoption discussion: adopting
this connector for *reading* brings a credential that can *write* into
the same process.

---

## 1. Scopes actually granted

26 scopes. Grouped by what they permit:

| Family | Read | Write |
|---|---|---|
| `trade.real` | ✅ | ✅ |
| `trade.demo` | ✅ | ✅ |
| `market-data` | ✅ | — |
| `money.balance` | ✅ | — |
| `money.cash-transactions` | ✅ | — |
| `watchlist` | ✅ | ✅ |
| `agent-portfolio` | ✅ | ✅ |
| `sub-accounts` | ✅ | ✅ |
| `user-info`, `club`, `pi-data` | ✅ | — |
| `feed`, `notifications`, `pnl-alerts`, `sso-applications` | ✅ | ✅ |
| `price-alerts` | — | ✅ |

Both scopes #222 flagged as separate grants — `market-data:read` and
`money.balance:read` — **are present**, so neither tool was scope-blocked.

Two observations on shape. There is **no `etoro-public:real:read` /
`real:write` umbrella**; the account permissions arrive as explicit
`trade.real:*` and `trade.demo:*` pairs. And `price-alerts` carries
`:write` with no matching `:read`, which is an asymmetry in the grant
rather than in the tool surface.

`authChannel` reported `bearer`, so this connection is OAuth-based rather
than key-pair based.

---

## 2. Does the account side supply a broker observation timestamp?

**No.** This was the single question #222 could not close from
documentation, and it is now closed by measurement.

### The portfolio summary does return a timestamp the route does not have

`get-my-portfolio-summary` carries a **top-level `timestamp`**. The
underlying route it wraps — `GET /api/v1/trading/info/{mode}/pnl`,
byte-for-byte the route `EtoroAccountBroker` already calls — returns
`ClientPortfolio`, whose thirteen top-level properties contain nothing
temporal (#222, from the OpenAPI document). So the MCP layer is adding
this field.

### It is a composition clock, not an observation time

Two independent measurements say so.

**It tracks the moment of the call.** The first response's timestamp sat
**31 s** before wall-clock at the moment it was read — consistent with
transit and reading delay, not with an account observed at some earlier
event.

**It moves by exactly the call separation.** Calls 2 and 5 requested the
same account with the same arguments. Their timestamps differ by
**503 seconds**, which is the wall-clock gap between the two calls. An
account observation time would have moved only when the account moved;
this moved because the clock did.

The control that sharpens it: **the available-cash figure was byte-identical
across both calls** while the instrument rates beneath it moved. So the
account's cash state demonstrably did *not* change, and the timestamp
advanced anyway. It is stamped when the response is built.

### It is also naive

`2026-08-20T09:28:42.29` carries **no timezone marker** — no `Z`, no
offset. MOVRvest's own `portfolio_observation_for` refuses a naive
timestamp outright (#223), and correctly: a receipt clock whose zone is
unstated cannot be aged safely.

Contrast the quote side, which is timezone-aware to seven decimal places
(§4). The two clocks in the same API are not built to the same standard.

### The balances tool has no clock at all

`get-my-balances` returned **zero temporal fields** — not an observation
time, not even a composition stamp like the portfolio summary's. #222
predicted this from the specification; the live response confirms it.

**Consequence.** MCP does not supply the `last_sync` the 15-minute
capital gate wants. It supplies a *second* receipt-class clock, one
strictly worse than the one MOVRvest already has (naive rather than
aware, and produced a network hop further away). #223's ruling — that a
receipt clock may gate operationally and may never be named an
observation time — applies to this field unchanged.

---

## 3. Is missing cash still distinguishable from measured zero?

**Partly, and the live corpus could not settle it.**

What was observed: the Trading account returned a spendable figure of
**measured zero** — a real `0.0` in `equityDetails.available`, not a
null. That is a genuine reading, and MOVRvest's repaired path (#223)
would treat it correctly as a measured zero rather than an absence.

What was **not** observed: any absent or null cash figure. No account in
the response omitted its spendable field, and no degraded call occurred.
Per the standing instruction, **no absence was manufactured**, so the
absent branch remains contract-stated rather than live-verified. The
contract's own rule is strong — *"a 502 or a statusCode 0 means the
balance COULD NOT BE READ: it is never a zero balance and must never be
reported as one"* — but a rule read in documentation is not a behaviour
observed in a response.

Two structural hazards do stand, both confirmed live:

- **`includeZeroBalances` defaults false.** A genuinely zero account is
  omitted from the response entirely, so absence and zero are conflated
  at the level of *row membership* unless the flag is set. This
  measurement set it to `true` deliberately.
- **The spendable field is per account type.** The response's own
  `fieldGuide` names `equityDetails.available` for Trading and states
  that `balance` is total account value and **not** spendable cash. A
  consumer reading `balance` as cash would be reading the wrong number
  with no error to warn it.

---

## 4. Quote provenance, tradability and account-specific eligibility

This is where the MCP is unambiguously stronger than what MOVRvest holds.

### Per-symbol quote provenance, timezone-aware

Every instrument carries its own `quote.asOf`, and they genuinely differ:
across the three resolved instruments in one batch the stamps spanned
**70.5 seconds**. One instrument's quote was over a minute older than
another's *in the same response*.

That matters more than it looks. A single response-level timestamp would
have licensed exactly the substitution #221 forbade — one security's
freshness standing in for another's. Here each symbol's price carries its
own reading time, timezone-aware (`Z`), which is precisely the shape
`price_observation_for` already consumes.

`ask`, `bid` and `spread` are supplied per instrument alongside `asOf`.

### Typed absence for an unknown symbol

A deliberately invalid symbol came back in **`notFoundSymbols`** with
HTTP 200 and no error, while the three valid symbols resolved normally in
the same call. Absence is typed, attributable to the specific input, and
does not poison the batch — the behaviour the contract described, now
observed.

### Account-specific eligibility

Per instrument: `allowOpenPosition`, **`minPositionExposure`**,
**`maxUnitsPerOrder`**, `allowedLeveragesLong` / `allowedLeveragesShort`,
`allowMitOrders`, `allowEntryOrders`, `allowTrailingStopLoss`,
`requiresW8Ben`, `unitsQuantityType`.

These are not generic market facts. `maxUnitsPerOrder` differed by three
orders of magnitude across the three instruments, the crypto instrument
refused entry orders where both equities allowed them, its leverage band
was narrower, and `requiresW8Ben` was true for the US-listed equities and
false for the crypto. The contract states eligibility reflects the
connection's own account, and the variation observed is consistent with
that.

**`minPositionExposure` is the one field that would close a real gap**:
it is a genuine minimum ticket size, which the Capital Action Envelope
currently has no source for at all.

### What it does *not* supply

**No depth, no traded volume, no ADV.** A spread is not depth. #222's
ruling stands: spread must never become a liquidity ceiling, and
`LIQUIDITY_UNMEASURED` remains honest after this measurement.

---

## 5. Aggregation, identity and response stability

**Aggregation is provider-side, confirmed live.** The portfolio returned
**14 instrument rows**, each with a `positionCount`: three rows reported
2 and eleven reported 1, so **17 underlying trade rows arrived as 14
instrument rows**. That is exactly the aggregation
`_portfolio_weights` performs by hand today, and it is the defect-prone
step — the 20.0% + 0.5% split that once read as a compliant 20.0%.

**Identity** travels as `instrumentId` **and** `symbol` **and** a display
name on every row, in both the portfolio and the instrument overview, and
the two agree. No ISIN, CIK or FIGI appears anywhere. Nothing here
establishes *temporal* issuer identity, so the reassigned-ticker class
of problem measured in #212 and #215 is untouched by this integration.

**Row order is not stable.** Holdings are sorted by value, so two calls
minutes apart returned the same 14 instruments in a different order as
values moved. Any consumer diffing these responses must key on
`instrumentId`, never on position in the list.

**Cross-check between the two surfaces.** A held equity's portfolio
`currentRate` fell between that same instrument's `bid` and `ask` in the
overview taken eight minutes later — consistent, and confirming the
contract's instruction not to re-price portfolio rows against live
market-data quotes. They are two different readings taken at two
different times, and the portfolio's is the older one.

---

## 6. Errors, refusals, latency and rate limits

**Typed and attributable.** Every response carried `statusCode` and an
`xRequestId` — a per-call identifier that makes an individual response
attributable in a support conversation, which the current REST path does
not surface. The one refusal encountered (`notFoundSymbols`) was typed,
scoped to the offending input, and non-fatal to the rest of the batch.

**No error or degraded branch was exercised**, because none occurred: 5
of 5 calls returned 200. The `warnings` array the contract describes for
degraded sections never appeared, so its live behaviour is unverified.

**Rate-limit metadata: none exposed.** No response carried
`retryAfterSeconds`, and no `RateLimit-*` field surfaced through the tool
layer. The specifications document the limits (the `pnl` budget is shared
across three endpoints; `getBalances` sits in the 60-requests/60-seconds
default pool), but **a documented limit is not an observable one** — a
consumer cannot pace itself from what came back here.

**Latency was not separately observable.** The MCP tool layer reports no
timing field, and the call boundary is not instrumented from this side.
The only timing evidence available is indirect: the composition timestamp
sat 31 s behind wall-clock at read time, which bounds transit-plus-read
rather than measuring the call.

---

## 7. Would this improve the Capital Action Envelope?

Taking the envelope's inputs one at a time.

| Envelope input | Today | With MCP |
|---|---|---|
| Portfolio observation time | receipt clock, tz-aware | **worse** — naive composition clock |
| Held weight per security | aggregated by us from trade rows | **provider-side**, with `positionCount` |
| Cash | derived (`credit − pending`) | provider-native `available`, per-type field |
| Price + provenance | Yahoo quote, own `asOf` | **per-symbol tz-aware `asOf`**, plus bid/ask |
| Minimum ticket | **no source** | **`minPositionExposure`** |
| Max order size | no source | `maxUnitsPerOrder` |
| Tradability | no source | `allowOpenPosition` |
| Liquidity depth | unmeasured | **still unmeasured** |

So the enrichment side is real and the replacement side is not — and the
two do not have to move together.

**On the second-decision-engine risk.** The eligibility fields are
*constraints*, not verdicts: they say what the account may do, not what
it should. Consumed as inputs to an envelope MOVRvest already computes,
they add no opinion. The risk is not in these fields but in the tool
descriptions' framing — `get-instruments-overview` is described as the
first tool for "whether and how the user can trade it", and
`prepare-trade` sits one call away in the same surface. **Adoption must
take the fields and leave the workflow.** A guard of the kind #94 and
#128 already use — an import-graph test proving no decision module
reaches the MCP client — would be the mechanism, in the slice that
eventually does it.

---

## 8. Conclusions

### Portfolio / account replacement — **NOT READY**

The blocker is provenance, and it is now measured rather than inferred.
The account side of this API states **no observation time**: the
balances tool has no temporal field at all, and the portfolio summary's
`timestamp` is a composition clock — it moved 503 s between two calls
503 s apart, while the cash figure beneath it did not move at all, and it
carries no timezone. Replacing `EtoroAccountBroker` would therefore
inherit the same freshness question MOVRvest already has, one hop further
from the source, in a weaker format, while *appearing* more
authoritative because the field is called `timestamp`.

Two further gaps, both smaller but real: the absent-cash branch was never
exercised live, so absence-versus-zero remains contract-stated on this
path; and `get-my-balances` **takes no account argument**, so it cannot
be pointed at the demo account the repository's `TRADING_MODE` declares
— the two tools address different perimeters, and only one of them can
be aimed.

What *is* established: provider-side aggregation works and matches what
we compute by hand, identity travels on every row, and the field set is
richer than the one we derive.

### Quote and executability enrichment — **READY**

Per-symbol, timezone-aware `asOf`; bid, ask and spread; typed
not-found; and genuine account-specific constraints in
`minPositionExposure`, `maxUnitsPerOrder` and `allowOpenPosition`. Every
one of those is a fact MOVRvest either lacks entirely or holds in a
weaker form, and none of them is a verdict.

The narrowest valuable adoption is unchanged from #222's guess and now
has evidence behind it: **`get-instruments-overview`, for quote
provenance and executability only**, touching no account-state path and
needing only `market-data:read`. Ready in the sense that the evidence
supports it — **not** proposed for implementation here, and not approved.

### Recorded, not solved

- The connection can place real trades. Read-only use is self-imposed.
- Degraded-path behaviour (`warnings`, `error`, non-200, 429) is
  unverified: nothing failed during this measurement.
- No rate-limit metadata reaches the caller, so self-pacing is not
  possible from the response.
- No ISIN, CIK or FIGI anywhere; temporal issuer identity is untouched.
- Row order is value-sorted and unstable between calls.
- Latency is not measurable from this side.

---

## 9. Owner ruling — 2026-08-20

1. **Portfolio / account replacement is REJECTED.** The existing
   MOVRvest account reader stays, together with its explicitly labelled
   receipt-time semantics (#223).

2. **Quote and executability enrichment is APPROVED as a capability** —
   exact-symbol timezone-aware `asOf`; `bid`, `ask` and `spread`; typed
   `notFoundSymbols`; account-specific eligibility and minimum-position
   constraints.

3. **Production integration is NOT yet authorized**, because the
   measured MCP credential carries real-money write scopes.
   **Self-imposed avoidance of write tools is defence in depth, not
   least privilege.**

4. **Re-entry requires a credential limited to the minimum read
   scopes.** If the MCP connection cannot be restricted, the production
   path must use a **separate read-only eToro API credential**.

5. **Any future adapter imports facts only**:
   - never trade preparation or execution workflows;
   - key results by `instrumentId`, **never** row position;
   - preserve **each security's own `asOf`**;
   - treat `allowOpenPosition` and `minPositionExposure` as **broker
     constraints**, never investment judgments or sizing
     recommendations;
   - **never let eligibility affect company quality**;
   - keep `LIQUIDITY_UNMEASURED`, because **spread is not market depth
     or volume**.

6. **Do not adopt MCP portfolio timestamps, balances or account
   aggregation.**

7. **No further authenticated calls are needed for this ruling.**

### Consequences

§2's composition-clock finding and §5's provider-side aggregation are
both **recorded and not consumed**: the aggregation works and is
deliberately not adopted, because adopting it would mean trusting a
boundary this measurement observed only once. The enrichment capability
of §4 is approved in principle and **blocked on credential scope**, not
on evidence — the measurement that would unblock it is an administrative
one, not another call against this API.

Ruling 5 is the standing contract for whichever slice eventually builds
the adapter. Three of its clauses restate rules this repository already
holds — instrument-keyed identity, per-security provenance, and the
depth-versus-spread boundary — and the two that are new say that a
broker's permission is not an opinion about a business.
