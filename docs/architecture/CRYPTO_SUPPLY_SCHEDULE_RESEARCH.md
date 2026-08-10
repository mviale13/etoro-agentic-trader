# Supply schedule and future issuance — research

**Status: research only, measured 2026-08-10. Nothing built, nothing
scored, no standing changed.** Supply Structure remains
`VISIBLE_NOT_SCORED` and the quality quorum remains 2.

The investor question this slice went looking for:

> **What future increase in economically available supply can current
> holders reasonably expect, over what time horizon, and how predictable
> is it?**

---

## The finding, first

**The corpus splits by monetary design, and the split runs the opposite
way to expectation.**

Assets whose supply arrives by a *mechanical rule* — Bitcoin, Cardano,
Solana — publish that rule as primary chain state, free and keyless, and
their future issuance paths reproduce. Assets whose supply arrives by
*allocation release* — Arbitrum, Hyperliquid, 1inch — publish no schedule
anywhere this platform can reach, at any price it is willing to pay.

That is the wrong way round for a quality factor. The three assets whose
supply is least contentious are the three that can be measured, and
Arbitrum — with 33.9–87.2% of its maximum outside the market — is
unmeasurable. A score built on this question would be silent exactly
where supply risk concentrates.

---

## A. Source matrix

Measured 2026-08-10 by direct request, no keys beyond the operator's
existing registrations.

| Desired fact | Primary / protocol | DefiLlama | CoinGecko (free) | CoinMarketCap | Other specialist |
|---|---|---|---|---|---|
| Protocol maximum | **PRIMARY_COMPUTABLE** (ADA, HYPE) | — | FREE_API (all 8) | PAID_API | — |
| *Positive* "no maximum exists" | — | — | **FREE_API** (`max_supply_infinite`) | PAID_API | — |
| Emitted supply | **PRIMARY_COMPUTABLE** (ADA, HYPE, ARB, TAO, BTC) | — | FREE_API, semantics unreliable | PAID_API | — |
| Issuance *rule* | **PRIMARY_DOCUMENTED** (BTC, ADA, SOL) | — | NOT_AVAILABLE | PAID_API | — |
| Emission schedule over time | **PRIMARY_COMPUTABLE** (BTC, ADA, SOL) | **PAID_API** (402) | NOT_AVAILABLE | PAID_API | 401 everywhere |
| Token unlock calendar | NOT_AVAILABLE | **PAID_API** (402) | NOT_AVAILABLE | PAID_API | 401 / web-only |
| Vesting buckets, cliffs | NOT_AVAILABLE | **PAID_API** | NOT_AVAILABLE | PAID_API | 401 / web-only |
| Genesis allocation | **PRIMARY_OBSERVATION** (HYPE) | — | NOT_AVAILABLE | — | — |
| Net issuance (uncapped) | PRIMARY_COMPUTABLE (SOL); partial (ETH) | fees/burn only, FREE | NOT_AVAILABLE | — | ultrasound.money, burn only, secondary |

### What every specialist source actually returned

| Source | Endpoint | Result |
|---|---|---|
| DefiLlama | `/emissions`, `/emission/{p}` | **HTTP 402** — *"Upgrade to the paid API plan"* |
| CryptoRank | `/v1/currencies`, `/v2/currencies/vesting` | **HTTP 401** — API key required |
| CoinMarketCap | `/v1/cryptocurrency/listings/latest` | **HTTP 401** — API key required; unlocks are a paid product |
| Messari | `/v1/assets/{id}/profile` | HTTP 404 — endpoint no longer served |
| Token Unlocks | `token.unlocks.app/api/unlocks` | **HTTP 200, 337 KB of HTML** — a Figma Sites web page, not an API |
| Mobula | `/api/1/market/data` | HTTP 429 — *"You need to create an API key"* |

**Token Unlocks is the ruling's own warning, demonstrated.** It returns
200 and a third of a megabyte, and none of it is data — it is a rendered
marketing page. Data visible on a webpage is not a free production API.

DefiLlama's fee and protocol endpoints, which this platform already
depends on, remain free and were re-checked: both HTTP 200.

**Conclusion: no free production API publishes token unlock schedules for
this corpus.** Every specialist route is paid or key-gated. The
ruling forbids paid accounts, so the specialist route is closed.

---

## B. Eight-asset supply path

| Asset | Monetary design | Emitted | Future issuance evidence | Horizon | Standing / authority |
|---|---|---|---|---|---|
| **BTC** | Capped 21m, mechanical halving | 20,068,365 (chain) | **Rule reproduces to 0.0000654%** | terminal 20,999,999.98 | primary computable, uncorroborated only because the surface is unacquired |
| **ETH** | **Uncapped, dynamic** | 120,682,058 (1 vendor) | burn only (secondary); validator issuance not read | — | `max_supply_infinite=True` — a *positive* statement |
| **SOL** | **Uncapped, rule-governed** | 631,882,479 (1 vendor) | **Full inflation governor from chain**: initial 8%, taper 15%/yr, terminal 1.5%; current 3.705% | rate path to the 1.5% floor | primary documented, unacquired |
| **ADA** | Capped 45bn, mechanical reserve draw | 38,803,572,882 **established** | **ρ=0.003, τ=0.2, epoch=432,000s — all read from chain** | 1y 1.22bn, 4y 3.62bn, 10y 5.51bn | primary computable |
| **ARB** | Capped 10bn, **allocation release** | 9,999,998,978 (chain, fails identity) | **none at any reachable source** | — | vendors 419% apart on circulating |
| **HYPE** | Capped 1bn, **allocation release** | 586,532,752 **established** | amount only: 412.5m future emissions; **genesis allocation complete, schedule absent** | — | primary amount, no cadence |
| **1INCH** | Capped 1.5bn, allocation release | 1,499,999,999.997 (1 vendor) | none | — | no primary surface |
| **TAO** | Capped 21m, mechanical halving | 11,218,394 (chain, fails semantics) | rule not located in chain storage | — | storage keys tried and not found |

*Emitted figures and standings are S5.1's; nothing here changed one.*

---

## C. The four deep reads

### BTC — the clean mechanical case

Two keyless sources agree on height (mempool.space and blockchain.info,
both **961,880**). Reproducing emitted supply from the consensus rule —
50 BTC initial subsidy, halving every 210,000 blocks:

```
computed        2,006,837,812,500,000 sat
chain totalbc   2,006,836,500,000,000 sat
difference                 13.125 BTC   (0.0000654%)
```

The computation is **higher** than the chain's own total, which is the
direction consistent with blocks that claimed less than the full subsidy.
This platform has not established the cause and does not assert one.

The two constants are remembered, and **the reproduction is itself the
cross-check**: a wrong subsidy or interval would miss by orders of
magnitude, not by thirteen coins. That satisfies Model C gate 3 by the
same argument Cardano's denomination does.

The rule then yields a schedule: era 4, subsidy 3.125 BTC, next halving at
block 1,050,000 (~612 days), **164,362 BTC over one year (0.82% of
emitted)**, 466,411 over four, 774,529 over ten, terminal 20,999,999.98.

**Bitcoin currently has no primary surface at all.** Acquiring height
would also give it an emitted-supply reading independent of CoinGecko's —
the only vendor reporting it today.

### ADA — the mechanical reserve draw

Every input is read, none remembered:

| Parameter | Value | Source |
|---|---|---|
| ρ monetary expansion | 0.003 | `epoch_params.monetary_expand_rate` |
| τ treasury growth | 0.2 | `epoch_params.treasury_growth_rate` |
| epoch length | 432,000 s = 5 days exactly | `epoch_info.end_time − start_time` |
| reserves | 6,196,427,118 ADA | `totals.reserves` |

Each epoch draws ρ of the remaining reserves; τ of the draw goes to the
treasury and the rest to staking rewards. **That separates all three of
the ruling's supply concepts cleanly**, which no other asset in the corpus
does:

- *remaining protocol supply* = reserves, 6.20bn
- *scheduled future issuance* = the ρ draw, decaying geometrically
- *future circulating supply* = 80% of the draw; the treasury 20% moves to
  a pot that is itself excluded from circulating

Over one year the rule releases 1.22bn ADA (3.1% of emitted); four years
3.62bn; ten years 5.51bn, leaving 691m in reserves.

**Vendor unlock concepts do not apply here.** There are no cliffs, no
vesting and no counterparties — there is an arithmetic rule and a pot.

### ARB — why 100% emitted means nothing on its own

The chain's `totalSupply()` counts tokens **minted**, and Arbitrum minted
its full 10bn at genesis. Lock state is not a property an ERC-20 total
knows about. So "100% emitted" and "large economically unavailable
balances" are not in tension — they are answers to different questions,
and the ratio conflates them.

What this platform can establish: the two vendors' circulating estimates
are **1.275bn and 6.614bn — 419% apart, a gap of 5.34bn ARB, 53.4% of the
maximum**. What it cannot establish: which buckets, which cliffs, which
dates. Every source that would say is paid or key-gated.

The honest position is that ARB's overhang is *measured as a range and
unexplained*, and that this platform cannot distinguish "the schedule is
opaque" from "we could not reach the schedule" — a 401 is a statement
about access, not about disclosure.

### HYPE — a complete allocation with no cadence

`tokenDetails.genesis.userBalances` holds **94,023 addresses summing to
exactly 1,000,000,000 HYPE** — the entire maximum, allocated at genesis
(deployed 2024-11-29). So:

- remaining protocol supply is **zero**: nothing is left to allocate
- future emissions are **412.5m**, allocated at genesis and not yet emitted
- the excluded balances are four *named* addresses, 287.5m

The protocol therefore publishes *who* and *how much*, and **nothing about
when**. No cadence, no cliff, no vesting term is reachable. A schedule
cannot be inferred from balances, and this slice does not try.

On the Assistance Fund: it appears in the non-circulating set as a balance
and its release semantics are not published. Its value-accrual role is a
separate question and stays in S5's protocol economics, untouched.

---

## D. Candidate investor question

The ruling's hypothesis was one question. The measurement says it has to
be two, split by monetary design — which is what the S3 capability
architecture exists to express.

**For mechanically-issued assets** (monetary network, smart-contract
network):

> Is the issuance rule published by the protocol, and does it reproduce?

Answerable from primary evidence for BTC, ADA and SOL. Partially for ETH.

**For allocation-release assets** (scaling network, exchange network,
application protocol):

> When does allocated-but-unemitted supply become economically available,
> and to whom?

Answerable for **none of them**, and not for want of trying.

The narrowest durable single question that spans both — *is future supply
rule-governed and reproducible?* — is answerable for 3½ of 8, and the 4½
it cannot answer are the assets with the largest overhang. It would score
Bitcoin and Cardano well and stay silent about Arbitrum, which is the S5.1
inversion returning in a new costume.

---

## E. Scoring readiness

**`NOT_READY`.**

Not because the evidence is thin — three assets have fully reproducible
issuance paths from primary, keyless sources, which is more than S5.1
expected. Because:

1. **It is answerable only where supply is already uncontentious.** The
   assets it cannot answer for are the ones a holder most needs answered.
2. **Opacity and unreachability are indistinguishable.** A 401 from a
   paid vendor is not evidence that a protocol failed to disclose, and
   marking ARB down would assert exactly that.
3. **The two subquestions are not commensurable.** Bitcoin's "the rule
   reproduces to 0.0000654%" and Hyperliquid's "412.5m allocated, cadence
   unknown" cannot share a band without pretending they answer the same
   thing.

`VISIBLE_NOT_SCORED` is available today for the three mechanical assets
and would be worth having as evidence. It does not reach quorum and is
not proposed as a factor.

---

## F. JsonCache risk report

Eleven stores use `JsonCache`. Measured:

| | Count |
|---|---|
| Stores with a schema marker | **1** (`primary_supply`, added by S5.1) |
| Stores without one | **10** |
| Decoders that tolerate a missing key (`.get(`) | **all of them** |
| Decoders that reject an unrecognised record | **none** |

**Is correctness at risk today? No.** Checked directly rather than
assumed: for every store, each key its cache decoder reads is present in
the records currently held. The keys that look absent in a crude scan are
read from *provider responses*, not from cached rows. The exposure fires
only when a reader begins needing a field older records do not carry —
which is precisely what happened in S5.1 and was fixed there.

**Is another evidence-integrity slice required before scoring? No — but
it is required before the next slice that changes a stored shape.** The
failure mode is silent and time-boxed: the store keeps serving the old
shape until the daily expiry, and the reader sees an honest-looking
absence rather than an error. S5.1's instance made a real measurement
look like an evidence gap for the length of one debugging session.

**A central fix is preferable to per-store patches.** The marker belongs
in `JsonCache.write`/`read`, taking a version from the caller, so a
provider cannot forget it. Eleven repetitions of four lines means the
eleventh is the one that gets missed — which is how this one arose.

---

## G. Recommendation

**Acquire the three mechanical issuance rules as evidence, unscored.**

One slice, all primary, all keyless, no new vendor and no new cost:

| Asset | What is read | Cross-check available |
|---|---|---|
| BTC | block height → emitted supply and the halving path | two independent height sources; the rule reproduces the chain's own total to 0.0000654% |
| ADA | ρ, τ, epoch length, reserves → the reserve-draw path | already established; the parameters are read, not remembered |
| SOL | inflation governor and current rate → the taper path | the implied elapsed time is consistent with the published rate |

Why this and not something larger:

- **It gives Bitcoin a primary surface for the first time.** BTC's emitted
  supply is one vendor's figure today; two keyless sources and a
  reproducing rule would make it the best-evidenced supply figure in the
  corpus.
- **It is the acceptance case the eventual question needs.** Whether
  "rule-governed and reproducible" can carry a score is decidable only
  once three assets have the evidence side by side.
- **It scores nothing**, so it cannot move a verdict, and quorum stays 2.

Do the `JsonCache` central fix first if that slice changes any stored
shape — and it will, since the issuance rule is new evidence to store.

Not recommended: paying for unlock data. The specialist sources are the
only route to ARB's and HYPE's schedules, all of them are paid, and the
ruling forbids it. That gap should be recorded as a standing acquisition
demand rather than closed with a subscription.
