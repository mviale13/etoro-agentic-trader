# S4 — CryptoMarketSnapshot: the market an asset trades inside

**Status: built and merged, 2026-08-10. No score, threshold, band or
decision rule changed. Every S1 conflict, S2 claim and S3 applicability
stands untouched.**

The question S4 exists to make answerable:

> Is this asset moving because of itself, its peer group, or crypto
> broadly?

And the boundary it exists to protect: **market context is not Asset
Quality.** A token that fell less than its peers is not thereby a better
asset, and nothing built here says it is.

---

## The measurement that shaped the design

Two figures from the same provider, on the same day, that look
interchangeable and are not:

| | 24h | what it is |
|---|---|---|
| Change in total market capitalisation | **+0.05%** | the aggregate moved — and it also moves with issuance and with assets entering the vendor's universe |
| Market return (MOVRvest, cap-weighted over the top 250) | **+0.11%** | the price return of a named set of assets |

Same story one level down, and larger:

| | 24h | |
|---|---|---|
| Layer 1 category capitalisation change | **+0.05%** | the provider's aggregate |
| Layer 1 members' cap-weighted return | **+0.15%** | MOVRvest's, over the 100 members read |

**A factor of three.** Only the second of each pair is a *return*, and
only a return may be subtracted from an asset's return. So the platform
computes its own comparator over a universe it can name, and carries the
provider's aggregate change beside it as a different fact with a
different definition. A test asserts the two never swap places.

---

## A. `CryptoMarketSnapshot` — the schema

A dated observation of the environment, shared by every token in the
book. Its own canonical family: `app/domain/crypto_market.py`, importing
nothing from token facts or protocol fundamentals, and imported by
neither.

**Every observation carries `metric × interval × standing × universe`.**
An interval is part of a figure — a level carries `INSTANT`, a change
carries its window, and a test asserts a level can never acquire a
window nor a change lose one. No metric is named for a *trend*,
*momentum* or a *regime*: those are interpretations.

### Market state — read from the provider

| metric | unit | interval | semantics |
|---|---|---|---|
| `total_market_cap` | USD | instant | summed value of the provider's universe. **Not independently reproducible** — the universe is the vendor's |
| `total_volume` | USD | instant | value traded across tracked venues over the preceding day |
| `market_cap_change` | % change | 24h | the aggregate's move. **Never subtracted from a price return** |
| `volume_change` | % change | 24h | the traded value's move |
| `btc_dominance` | % share | instant | Bitcoin's share of tracked capitalisation |
| `eth_dominance` | % share | instant | Ethereum's share |
| `stablecoin_share` | % share | instant | **a floor, not a total** — summed from the dominance table, which lists only the largest assets |
| `tracked_assets` | count | instant | how many assets the universe contains |

### Derived by MOVRvest — each naming its universe and its inputs

| metric | unit | interval | computed from |
|---|---|---|---|
| `market_return` | % change | 24h | the 24h return and market value of each of the 250 largest assets |
| `advancing` / `declining` | count | 24h | the same page — breadth |
| `peer_return` | % change | 24h | the same arithmetic over a peer group's membership page |
| `peer_advancing` / `peer_declining` | count | 24h | the same page |

### Per asset, and per peer group

`asset_return` at **1h / 24h / 7d / 30d**; `peer_market_cap`,
`peer_market_cap_change`, `peer_volume` from the provider's category
row.

### The two derived measurements that matter

**`RelativeReturn`** — subject minus comparator, in percentage points,
**refusing unless the intervals match**. Not a check the callers
remember: the function returns `None` on a mismatch, because an asset's
7-day return minus a market's 24-hour move is a number with no meaning
that would look exactly as authoritative as a real one.

**`Concentration`** — how much of the comparator the subject itself is,
with the denominator named. No vendor supplies it and every relative
figure needs it: Bitcoin is 57.2% of the universe its own comparison is
computed over, and Hyperliquid is 73.5% of its peer group. It is stated
as a plain measurement — **no threshold decides when a comparison stops
being informative**, because that is a judgment and S4 makes none.

---

## B. Provider coverage — CoinGecko, free tier, measured

| endpoint | gives | interval |
|---|---|---|
| `/global` | total cap, total volume, cap change, **volume change**, dominance table, tracked count | 24h only |
| `/coins/categories` | all **749** categories: market cap, cap change, volume — in one call | 24h only |
| `/coins/markets?ids=` | the corpus's returns at **1h / 24h / 7d / 30d**, and market cap | four |
| `/coins/markets?per_page=250` | the page the market return and breadth are computed from | 24h |
| `/coins/markets?category=` | one group's membership: breadth and its cap-weighted return | 24h |

**Breadth is not published anywhere.** `/coins/categories` has no
advancing/declining field, and `/global` has none either. It is computed
from membership pages — which is also where the peer *return* comes
from, so the call buys both.

**The interval finding, and it is load-bearing:** the provider publishes
asset returns at four intervals and market and category figures at
**one**. So 24 hours is the only window where a difference between them
means anything, and the other three intervals are carried and reported
as `uncompared` rather than silently omitted.

**Rate limit and the daily batch.** The keyless tier was measured at
roughly six calls a minute. The batch is deterministic:

```text
1  /global
1  /coins/categories          all 749 in one answer — never one call per group
1  /coins/markets?ids=…       all eight corpus assets in one answer
1  /coins/markets?per_page=250
4  /coins/markets?category=…  one per peer group in use, deduplicated
──
8  calls, paced at 11s, measured end to end at 90 seconds
```

Four securities share the Layer 1 group and it costs **one** call — the
count is a property of the peer-group table, not of the corpus size. A
partial batch is stored as partial; a rate limit on the fourth call
leaves the first three read. **Nothing depends on a key**: an operator's
demo key (never created by this platform) lifts the limit and is read
from `COINGECKO_API_KEY` if present.

Reported by `movrvest acquire` as `Crypto market 8 of 8 calls answered,
4 peer groups`.

---

## C. Corpus market-context matrix

Read 2026-08-10 10:20 UTC. Market return **+0.11%** over 24 hours;
breadth **98 advancing / 97 declining** of the top 250.

| | 24h return | peer group | peer return | vs market | vs peers | share of peer group |
|---|---|---|---|---|---|---|
| **BTC** | +0.20% | **none** — measured | — | **+0.09 pp** | — | 57.2% *of the market* |
| **ETH** | 0.00% | Layer 1 (L1) | +0.15% | −0.11 pp | −0.15 pp | 10.1% |
| **SOL** | +0.30% | Layer 1 (L1) | +0.15% | +0.19 pp | +0.15 pp | 2.4% |
| **ADA** | −1.30% | Layer 1 (L1) | +0.15% | −1.41 pp | −1.45 pp | 0.4% |
| **ARB** | +3.30% | Rollup | +1.50% | **+3.19 pp** | **+1.80 pp** | 38.0% |
| **HYPE** | −0.20% | Perpetuals | +0.00% | −0.31 pp | −0.20 pp | **73.5%** |
| **1INCH** | +0.40% | Dex Aggregator | −0.29% | +0.29 pp | +0.69 pp | 13.6% |
| **TAO** | −1.80% | **none** — measured | — | **−1.91 pp** | — | 0.09% *of the market* |

Read ARB's row as the deliverable: it rose 3.3% on a day the market
returned 0.11% and rollups returned 1.50%. It outpaced **both**, and by
different amounts — which is precisely the sentence that was
unavailable before S4.

Read HYPE's beside it: down 0.20%, its peer group flat, the market up
0.11%. It moved with its sector rather than against it — and 73.5% of
that sector *is* HYPE, which the page states rather than leaving the
reader to discover.

---

## D. Peer-group methodology

**`MarketPeerGroup` is not `AnalyticalArchetype`, and the two modules
cannot see each other** — enforced by test in both directions.

```text
ETH   archetype: SMART_CONTRACT_NETWORK   peer group: Layer 1 (L1)
```

Both statements are true. The archetype is what MOVRvest believes the
asset is, from evidence it re-checks; the peer group is who the market
prices it alongside, from a vendor's taxonomy. **A provider category
never changes a playbook.**

Every group was chosen by reading its *membership*, because a category's
name is not evidence of what is in it. Two were rejected on that reading:

- **`smart-contract-platform` — the ruling's own acceptance case,
  measured.** Its membership is led by **Bitcoin at rank 1**, with
  Dogecoin, XRP and Tron in the top ten. Neither Bitcoin nor Dogecoin
  runs smart contracts. Choosing on the name would have compared
  Ethereum against assets the name excludes.
- **`layer-2`** holds **WETH** — wrapped ether, which has no economics
  of its own and simply tracks Ethereum — plus the exchange tokens OKB
  and MNT. A group containing a wrapper of another asset is not a
  scaling peer set. `rollup` (30 members: ARB, IMX, OP, STRK) was taken
  instead.

| security | group | why | flagged |
|---|---|---|---|
| BTC | **none** | every group containing Bitcoin is dominated by it; Layer 1 is 80.2% of the tracked market | market comparison kept, with the 57.2% share stated |
| ETH / SOL / ADA | Layer 1 (L1) | base layers are what the market prices them alongside, and the membership *is* base layers | Bitcoin leads it; the category is 80.2% of the market |
| ARB | Rollup | ARB, Immutable, Optimism, Starknet — rollup tokens | ARB is among the largest members |
| HYPE | Perpetuals | the venues it competes with for the same flow — Aster, Jupiter, dYdX. Layer 1 also contains it and would compare an exchange with settlement layers | **HYPE is 73.5% of it** |
| 1INCH | Dex Aggregator | 31 routing protocols; the one group whose members share its *economics* rather than its theme | — |
| TAO | **none** | see below | — |

**TAO is the acceptance case for a refused comparison.** CoinGecko's
Artificial Intelligence category is led by Chainlink (an oracle
network), then two general-purpose layer-1s and a rendering marketplace.
Those share a *theme*, not a business, and a return computed over them
would measure a narrative. S3 already declined to classify TAO from an
AI label; comparing it against one would be the same mistake with a
number attached. TAO gets the broad market comparison and an explicit
absence — **not a fake peer figure.**

---

## E. Evidence standing

| | standing | count |
|---|---|---|
| Market state, breadth, returns, peer figures | **CLAIMED** | all |
| Anything | ESTABLISHED | **0** |
| Anything | CONFLICTED | 0 |
| Metrics absent in the cycle read | ABSENT | 0 |

There is one market source, so nothing is corroborated — the S1 rule
applied uniformly. Derived figures inherit the weakest standing of their
inputs; arithmetic does not improve evidence.

**The epistemic issue §14 asked me to report rather than silently
resolve.** A total market capitalisation is not merely uncorroborated —
it is **not independently reproducible at all**. The universe is the
vendor's own, so a second vendor computing "the total" would be
computing a *different total* over a different membership, not
corroborating this one. The same applies to every dominance figure and
every category aggregate.

Three ways this could be treated, for the owner to rule on:

1. leave it as it is — attributed, dated, `CLAIMED`, consumed by
   nothing, which is what shipped;
2. rule that a **vendor-scoped aggregate** is a distinct evidence kind
   whose standing question is *whose universe*, not *how many sources* —
   in which case the honest word is neither established nor claimed;
3. corroborate the *components* instead: BTC dominance can be checked
   against this platform's own BTC market cap over the same vendor's
   total, which is an internal-coherence check rather than corroboration.

I took none of the three unilaterally.

---

## F. Investor-facing rendering

A section of its own on the token dossier — **Crypto market context** —
below the asset's own evidence and outside every score on the page.
Three cards: the market, the asset's own returns, the peer group with
why it was chosen and what was rejected. Then the arithmetic, and the
concentration beneath it.

**No traffic lights.** A delta is rendered in plain type with no colour,
because shading it green or red would be the verdict this platform has
not earned.

- **BTC** — market card, its four returns, *"Peer group — none"* with
  the measured reason, one relative figure (+0.09 pp), and *"BTC is
  57.2% of the crypto market by market value (the 250 largest assets…)"*.
- **HYPE** — Perpetuals with its selection reason, the amber caveat that
  HYPE is the largest member, six peer figures, two relative figures, and
  both concentrations.
- **ARB** — Rollup, with *Layer 2* shown under **Considered and not
  used** and the WETH reason printed.
- **TAO** — *"Peer group — none"*, the Chainlink reason in full, the
  Artificial Intelligence category listed as considered-and-rejected,
  and the market comparison standing alone. **No fake peer number
  appears.**

Verified rendered in the browser for all four, plus AAPL to confirm an
equity is sent no market section at all rather than an empty one.

Also `movrvest crypto-market` (the environment plus a corpus table of
both deltas) and `movrvest crypto-market SYMBOL`.

---

## G. S5 readiness

Coverage over the corpus, by the platform's own consumption rule:
**`established_value` returns nothing for a CLAIMED figure**, so a
question whose best evidence is a claim cannot feed a score today
without changing the epistemic rule.

| investment question | applies | established | claimed | absent | readiness |
|---|---|---|---|---|---|
| Market robustness | 8/8 | **6** | 2 | 0 | **READY_TO_MEASURE** — 2 conflicted (ARB, HYPE) |
| Liquidity | 8/8 | 0 | 8 | 0 | **NOT_READY** — volume is vendor-scoped; S4 changed nothing here |
| Supply / dilution | 8/8 | 8 | 0 | 0 | **PARTIAL** — the *question* is answerable on an established cap, but the dilution arithmetic needs circulating **and** max established, and circulating is CONFLICTED for HYPE, ARB, ADA, TAO |
| Monetary scarcity | 1/8 | 1 | 0 | 0 | **PARTIAL** — BTC's cap is established; the issuance schedule and who could change it are absent |
| Network adoption (usage, ecosystem) | 7/8 | 0 | 1 | 6 | **NOT_READY** — no source publishes transactions or active users |
| Network security | 6/8 | 0 | 6 | 0 | **NOT_READY** — fees are claimed; issuance to block producers and cost-to-attack are absent |
| Decentralisation | 6/8 | 0 | 0 | 6 | **NOT_READY** — entirely unread |
| Protocol usage | 2/8 | 0 | 1 | 1 | **NOT_READY** |
| Economic activity | 6/8 | 0 | 6 | 0 | **NOT_READY** — claimed only |
| Protocol capture | 2/8 | 0 | 2 | 0 | **NOT_READY** — claimed only |
| Token-holder value accrual | 6/8 | 0 | 3 | 3 | **NOT_READY** — claimed only; **NOT_APPLICABLE_BY_ARCHETYPE for BTC** |
| Resilience / evidence maturity | 8/8 | 0 | 0 | 8 | **NOT_READY**, and S3 ruled it belongs outside Asset Quality |

### The finding

**Only two of twelve have any established evidence, and both are market
facts.** Every economic question about a network or a protocol reads
*claimed* — not because the figures are thin, but because there is one
source and the establishment rule requires two.

**So the binding constraint on S5 is not the model. It is
corroboration.** One decision unlocks six questions at once: *is a
primary computation over public chain data, with published methodology,
a different epistemic class from a secondary market aggregate?* If yes,
network security, economic activity, protocol capture, capital committed
and value accrual all become measurable in the same week. If no, S5 can
honestly score two questions.

### Recommended S5 scope

**Sequence the ruling before the model.** Concretely:

1. **Rule on the epistemic class of primary chain data** (or add a
   second protocol source — the pool seam exists and is tested). This is
   the highest-value decision available and it is not a code change.
2. **Then** design Asset Quality over whatever that ruling admits,
   consuming `QuestionCoverage` per archetype — so a score is
   composed of the questions that *apply* rather than of the metrics
   that happen to exist. BTC scored without a value-accrual term and
   HYPE scored with one is the whole point of S3.
3. **Keep the two conflicts visible in the output rather than resolving
   them**: HYPE's and ARB's circulating supply are still contested, and a
   score that silently picked a side would undo S1.

What S5 should **not** do: score market context. S4's figures are
context for timing, risk and conviction — they say nothing about what an
asset *is*, and folding a 24-hour relative return into Asset Quality
would make the quality of Bitcoin change every morning.

---

## What did not move

Verified by test, not asserted.

- **Three evidence families, mutually unreachable.** Market ↮ token facts
  ↮ protocol fundamentals, checked on the imports in both directions.
- **No provider type in a canonical object**, and a second market source
  joins by writing an adapter — exercised in test with a source nobody
  wrote a line for.
- **Category never touches archetype.** `market_peer_group` cannot see
  `crypto_archetype` and vice versa, checked on identifiers rather than
  on prose so each module may still *state* the boundary.
- **Aligned intervals only.** `relative_return` returns `None` on a
  mismatch.
- **Asset liquidity and global volume never meet.** The market family
  holds no asset volume at all, so there is nothing to divide.
- **No regime, no sentiment.** No identifier or value in the family
  contains `risk_on`, `altseason`, `fear`, `greed` or `trending`.
- **Nothing consumes any of it** — the import-graph guard over fifteen
  reasoning paths, now covering the market modules too.
- **Equity behaviour unchanged**; the crypto quality bands asserted at
  their current values.

1717 tests, ruff, mypy and `npm run build` green.

## Circulating-supply drift — reported, not acted on

The cycle re-read the corpus and the S1 picture is unchanged: HYPE's two
vendors remain ~51% apart on circulating supply, ARB's TokenInsight
figure is still the round launch float, and ADA and TAO still differ by
methodology. No extra polling was created to force a conclusion, and no
rule was proposed.
