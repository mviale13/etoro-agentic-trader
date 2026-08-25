# Fresh Quote Ribbon — Stage 0 record (2026-08-25)

Budget: max 5 authenticated provider calls, no retries. **Used 4.**

| # | call | receipt (UTC) | outcome |
|---|---|---|---|
| 1 | eToro MCP `get-instruments-overview`, one batch: DIS, MSFT, BNP.PA, HYPE, TAO, ZZZZNOTASYMBOL | 14:12:58 | 200; 5 resolved + typed `notFoundSymbols`; per-instrument tz-aware `asOf` 14:13:04.87–05.72 |
| 2 | identical, 95 s later | 14:14:40 | 200; **every `asOf` advanced** (~14:14:42–48); prices and spreads moved, BNP.PA included |
| 3 | REST `/api/v1/market-data/instruments/rates` via urllib | 14:15:36 | **403 Cloudflare 1010 at the edge** (`cfOrigin;dur=0` — never reached eToro); urllib UA is bot-filtered. Harness defect, not entitlement |
| 4 | same route via httpx (the production client), ids 1016,1004,1238,100446,100418,999999999 | 14:15:52 | **200 on the repo's own credential**; ratelimit-limit 120/60s, remaining 119 |

## Findings

- **Coverage**: US (DIS, MSFT), non-US (BNP.PA, Euronext-listed), crypto
  (HYPE, TAO) — all in one batched call on either surface.
- **Identity**: stable `instrumentId`; HYPE → 100446 "Hyperliquid", TAO →
  100418 "Bittensor" — no ticker collision (the Yahoo "Supreme Finance USD"
  trap does not exist here). Ids cross-verified between the MCP overview and
  the platform's stored watchlist evidence (75 symbols mapped from one
  capture; BNP.PA 1238 from the instruments capture).
- **Price**: REST route carries `lastExecution` (a traded price) plus
  `bid`/`ask`; the MCP layer exposes only ask/bid.
- **Source clock**: per-instrument, tz-aware, sub-second `date`
  (`asOf` on the MCP) — SOURCE_STATED, and it advances between calls.
- **Receipt clock**: ours, recorded separately. Never conflated.
- **NOT stated by the provider**: quote **currency** (BNP.PA's
  `conversionRateAsk` 1.16725 shows the native quote is not account-currency,
  but nothing names EUR) → `currency: null`, never inferred. **Delay status**
  → UNKNOWN. **Market status** → UNKNOWN.
- **Invalid identifier**: MCP → typed `notFoundSymbols`; **REST rates route
  drops the unknown id silently** (5 rows back, no marker) — the adapter must
  key by `instrumentID` and treat an absent asked-for row as unavailable.
- **Entitlement**: proven for the production path — the repo's own
  ETORO_API_KEY/ETORO_USER_KEY got 200 on the rates route. Rate limit stated
  in headers (120 req/60 s shared pool); a 60 s TTL uses ≤1 of 120.
- **Caching/display**: read-only market-data route on the account's own key;
  the MCP contract says "quotes move, so re-call rather than cache" — a 60 s
  display TTL honours that (it re-calls) while bounding load. Personal,
  single-user display use.
- **CoinGecko fallback: NOT NEEDED** — eToro quoted both crypto specimens
  with correct identity. Per the ruling, alternatives were not tested.
  (Existing integration already maps HYPE→`hyperliquid`, TAO→`bittensor` by
  permanent id if ever needed.)
- **Evidence-write hazard**: `EtoroClient.get` records every response to the
  evidence store unconditionally — the fresh-quote adapter therefore issues
  the same authenticated GET directly (httpx, same headers, same base URL)
  **without** the snapshot store, honouring "no persistence".

## Production contract established

- Route: `GET /api/v1/market-data/instruments/rates?instrumentIds=…`, one
  batch; httpx; repo credential; no retry; no evidence write.
- Identity: symbol → (instrumentId, display name) from the platform's own
  stored eToro captures (watchlists + marketdatainstruments), latest-first,
  under `MOVRVEST_EVIDENCE_ROOT` — zero extra calls, hermetic, same broker
  as the quotes. Unknown symbol → IDENTITY_REFUSED, stated.
- `clock_kind: SOURCE_STATED` (the route states `date` per instrument);
  CURRENT iff source age ≤ 120 s at receipt, else STALE.
- `delay_status: UNKNOWN`, `market_status: UNKNOWN`, `currency: null` —
  the provider states none of them.


## The supported claim, and its limits (owner ruling, point 7)

The provider states **neither a delay nor a market status**. So the only
claim this platform may make about a displayed quote is:

> Source-clock current within MOVRvest's two-minute display window;
> provider delay not stated.

*"Live"*, *"real-time"* and *"quoted live"* are **not** supported by
anything measured here and appear nowhere in the code, the UI or this
record. A quote whose source clock has advanced is a quote whose source
clock has advanced — it is not evidence of an undelayed feed.

## Credential privilege — unresolved, and why the ribbon defaults off
(owner ruling, point 6)

Stage 0 proves the repository's `ETORO_API_KEY` / `ETORO_USER_KEY` are
**entitled** to read the rates route. It does **not** establish their
**privilege boundary**. Two facts, kept apart:

- **Mechanically separate.** These are REST header credentials read from
  the repository `.env`; the MCP connection measured in #224 is a
  distinct OAuth grant. Nothing in this codebase reads one to obtain the
  other.
- **Privilege unknown.** #224 measured the *MCP* connection carrying
  `trade.real:write` among twelve write grants. Whether these REST keys
  are restricted to read-only use is an **administrative fact about how
  they were issued**, and no call this codebase can make would settle
  it — an entitlement to read proves nothing about the absence of write
  entitlement. No additional authenticated call is authorized to
  investigate it.

The structural absence of POST/order methods in the adapter is required
and holds, and it is **not** a proof of least privilege.

So, per the ruling's contingency: the implementation merges, and
**fresh quotes default off behind `MOVRVEST_FRESH_QUOTES=on`**, an
explicit operator action. With the flag unset the service contacts no
provider and every symbol answers UNAVAILABLE naming the enabling
action. **Production activation remains scope-unresolved** pending
either a least-privilege read-only credential determination or a
separate read-only eToro REST credential.
