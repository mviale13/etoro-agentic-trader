# Crypto Intelligence — the first vertical slice

**Status: built 2026-08-10. Decision-neutral.** No recommendation
threshold moved, no crypto-quality factor changed, equity untouched. The
layer is visible and nothing that decides can reach it.

> What changed in this asset, what appears to be driving it, why that
> matters, and what deserves attention next?

`movrvest crypto-intelligence [SYMBOL] [--evidence]`

---

## A. BTC / ETH completeness audit

The question the ruling asked: an information shortage, or a synthesis
shortage? **Both, and in different places.**

| | BTC | ETH | HYPE |
|---|---|---|---|
| Price, market cap, rank, volumes, 24h change, FDV | ✅ | ✅ | ✅ (cap conflicted) |
| Returns 1h / 24h / 7d / 30d | ✅ | ✅ | ✅ |
| Relative vs market, vs peer group | ✅ market | ✅ market + Layer 1 | ✅ market + Perpetuals |
| Market snapshot: cap, volume, dominance, breadth | ✅ | ✅ | ✅ |
| Protocol: TVL, fees | ✅ $3.56bn / $139k | ✅ $42bn / $175k | ✅ $6.26bn / $843k |
| Protocol: revenue, holder revenue | — (correctly declined) | ✅ $32k burn | ✅ $535k Assistance Fund |
| Venue: dex volume, open interest | n/a | n/a | ✅ $10.9bn OI |
| Supply concepts + issuance rule | ✅ | ✅ (uncapped) | ✅ |
| Archetype and applicable questions | ✅ 9 | ✅ 12 | ✅ 15 |
| **ETF / capital flows** | ❌ | ❌ | n/a |
| **Institutional holdings** | ❌ | ❌ | ❌ |
| **Current events, upgrades, incidents** | ❌ | ❌ | ❌ |
| **Provider narratives** | ❌ | ❌ | ❌ |

**The durable layer was rich and unsynthesised.** Everything above the
line already existed and no surface combined it into *what is happening
now*. That is a synthesis shortage, and this slice fixes it.

**The perishable layer was empty.** Flows, holdings, events and
narratives had no home at all. That is an information shortage, and this
slice fixes half of it — flows and holdings — and leaves events and
narratives named as the next acquisition.

---

## B. Source plan, measured before chosen

| Source | Result |
|---|---|
| **SoSoValue** | **free, keyless, POST** — daily net flow, cumulative flow, net assets, token holdings, share of supply, and **300 days of daily history** for `us-btc-spot` and `us-eth-spot` |
| **CoinGecko public treasury** | **free, keyless** — 179 companies holding 1,282,501 BTC; 33 holding 7,818,592 ETH |
| Farside | HTTP 200, **777 KB of HTML** — a webpage, not an API |
| CoinGlass | HTTP 500 on the public path; v4 needs a key |
| Mobula | HTTP 429, key required |
| CoinGecko free tier | no ETF field at all |

Two acquisitions, both free, both keyless, neither paid for. Nothing
else was integrated.

---

## C. The canonical model

```text
IntelligenceClaim   one thing worth telling an investor, with its
                    epistemic type, source, authority, standing,
                    relevance window, and what it does NOT establish
Driver              an assertion *about* claims — carries refs, never prose
Foundation          three lines of durable ground, plus what it could not settle
CryptoIntelligenceSnapshot
                    claims · drivers · relative context · foundation ·
                    conflicting · watch next
```

**Boundaries.** It consumes token facts, market context, protocol
fundamentals and supply, and rewrites none of them. It adds only what
they do not carry: flows, holdings, and a time-to-live.

**It cannot reach Asset Quality.** Not a convention — the modules do not
import it and a test asserts so, in both directions.

---

## D. Narrative epistemics

Four kinds of statement, kept apart:

| Type | Meaning | In the BTC brief |
|---|---|---|
| `MEASURED` | this platform's arithmetic | *"Over the last 30 published days those funds took $128m net, positive on 18 of them"* |
| `REPORTED` | a source's fact | *"US spot BTC ETFs took $99m net on 7 August"* — SoSoValue |
| `INFERRED` | this platform's reading | *"Identifiable institutional balance sheets hold a material share"* |
| `ATTRIBUTED` | a source's opinion, with its name | *(vocabulary built; no narrative source acquired — see below)* |

The ruling's own example decomposes into all four:

> *"ETF inflows are supporting Bitcoin while institutional interest
> remains high"*

- the flow → `REPORTED`, independently checkable
- the price state → `MEASURED`
- institutional interest → `INFERRED` from holdings
- **"supporting"** → `ATTRIBUTED`, and never this platform's

**Honest limit: no narrative source is wired.** The vocabulary exists
and is exercised by a test on that exact sentence, but no provider
summary is ingested, so no `ATTRIBUTED` claim appears in a live brief
today. Acquiring one is the next slice, and the decomposition is ready
for it.

---

## E/F/G. Rendered results

### BTC — flows lead

```
What changed
  · BTC returned +0.2% / +3.9% / +1.1% over 24h / 7d / 30d   (reported · CoinGecko)
  · US spot BTC ETFs took $99m net on 7 August                (reported · SoSoValue · recent)
  · Over the last 30 published days those funds took $128m
    net, positive on 18 of them                               (measured · MOVRvest)
  · Those funds hold 1,223,634 BTC — 6.1% of the supply,
    worth $79.5bn                                             (reported · SoSoValue · ongoing)
  · 179 public companies report holding 1,282,501 BTC         (reported · CoinGecko · ongoing)
  · Bitcoin: $139k paid in fees over a day                    (reported · DefiLlama · today)

What appears to be driving it
  · Fund flows have been a net source of demand over the last month.
    (supported by several readings)
    why it matters: an identifiable source of marginal demand that does not
    depend on what other holders do.
  · Identifiable institutional balance sheets hold a material share.  (MOVRvest reading)
    why it matters: a stock rather than a flow — it says who owns the asset,
    not who is buying it, and a large disclosed holder base cuts both ways.

Relative context
  · BTC returned 0.09pp more than the crypto market over 24 hours
    (+0.20% against +0.11%) — MOVRvest's arithmetic over two figures read at
    the same interval.

Foundation
  · Market significance: $1,308.7bn (established, TokenInsight).
  · Supply: 95.6% of a protocol maximum of 21,000,000 tokens has been emitted.
  · Economic system: Bitcoin.
```

### ETH — the same architecture, a different asset

Everything BTC has, plus what only ETH has: **`Ethereum: $32k reached
holders over a day. Amount of ETH burned — base fees plus blob fees.`**
That produces a third driver — *economic activity is reaching the token
itself* — which BTC does not get, because Bitcoin's fees go to miners
and the protocol layer says so. **The difference comes from the
evidence, not from a branch on the symbol.**

ETH's flows are also the stronger story: $540m over 30 days on 21
positive days, against BTC's $128m on 18.

### HYPE — no ETF concepts, and not penalised for it

```
What changed
  · HYPE returned -0.2% / +3.9% / -18.0%                      (reported · CoinGecko)
  · Hyperliquid: $843k paid in fees over a day                (reported · DefiLlama)
  · Hyperliquid: $535k reached holders over a day. Hyperliquid Perps: 99% of
    fees go to Assistance Fund for buying HYPE tokens…        (reported · DefiLlama)
  · Hyperliquid: $10.9bn held open                            (reported · DefiLlama)

Held in tension
  · Economic activity is reaching the token itself. At the same time, the
    asset has moved -18% over a month.
  · How much of this asset is actually circulating is disputed between
    sources, so any figure computed from it inherits the disagreement.
```

No flow claim exists and **nothing says one is missing** — an absent
question is not an unmet demand. Hand it a fund group in a test and it
produces flow claims, which is how the architecture proves it branches
on evidence rather than tickers.

---

## H. Deterministic fallback

**The deterministic renderer *is* the implementation.** No writer is
wired in this slice: the command imports no model, no prompt and no
provider, and a test asserts it. Everything above renders with nothing
but the structured snapshot.

That is a scope decision, stated plainly rather than implied. §13's LLM
synthesis — prioritising evidence, connecting current events to durable
understanding, wording the CIO view — is the natural next step, and it
now has a grounded object to write from and a floor to fall back to.

---

## I. Evidence grounding

`CryptoIntelligenceSnapshot.grounded` is a property, not a promise:
every driver's refs must resolve to claims the snapshot holds. Asserted
for all three assets. A driver cannot be constructed without claims
beneath it, which is what a writer will be unable to circumvent.

`--evidence` shows each driver's underlying claims and what each claim
does *not* establish — progressive disclosure rather than the ledger on
the main view.

---

## J. Product assessment — is this materially more useful?

**Yes for BTC and ETH; marginally for HYPE; and the honest caveats
matter.**

What is genuinely better than the dossier alone:

- **It answers a different question.** The dossier says what Bitcoin
  *is*; this says what is happening to it. An investor opening the app
  wants the second more often.
- **Flows are new information, not a re-cut.** $128m over 30 days on 18
  positive days is a fact the platform did not previously hold, and it
  is the single most-cited driver in crypto commentary.
- **The epistemic labels are a real differentiator.** A CoinGecko
  paragraph asserts *"inflows are supporting BTC"* with no way to tell
  fact from interpretation. This separates them by construction.
- **Tension is preserved.** HYPE earning for holders while down 18% is
  exactly the shape a single bullish/bearish label destroys.

Where it falls short, critically:

- **No current events.** No upgrades, incidents, regulatory
  developments or announcements. For a *current intelligence* product
  that is the biggest remaining gap, and it is why BTC's brief is
  flow-heavy.
- **No narratives.** The `ATTRIBUTED` type has no live producer, so the
  decomposition advantage is demonstrated rather than delivered.
- **Drivers are rule-derived, not reasoned.** *"Fund flows have been a
  net source of demand"* comes from a sign test on a 30-day sum. That is
  honest and shallow; the LLM layer is where it becomes analysis.
- **The 30-day flow leads with the wrong number for BTC.** $128m net on
  18 of 30 positive days means large offsetting days, and the brief
  reports the sum without the dispersion. A reader could take steadier
  demand from it than the data supports.

So: **a real step, and not yet the benchmark.** It beats the dossier at
answering *what now*, and it does not yet beat a good human summary at
*why*.

---

## K. Recommendation on the decision layer

**Do not couple it yet, and when you do, couple it as evidence rather
than as a score.** Three reasons:

1. **The drivers are not yet reasoned.** A sign test on a flow sum
   should not move a recommendation.
2. **The gap is events, not synthesis.** Coupling before the current-event
   family exists would let a recommendation move on flows alone, which
   is the narrowest possible view of *what is happening*.
3. **There is a natural seam already.** `Finding` carries `Sense` and
   `Dimension`, and `CommitteeOpinion` states positions over *referenced*
   findings. An intelligence claim is already ref-addressable, so the
   eventual bridge is projecting claims into findings — the same shape
   `ASSESSMENT_CONVERGENCE.md` describes, not a new mechanism.

Suggested order: **current events and narratives first, then the LLM
synthesis layer, then a decision contract.** Each earns the next.

---

## Boundaries held

Asset Quality cannot reach this layer and does not gate it. Market
context uses S4's interval-safe arithmetic and is never recomputed here.
No recommendation threshold, no quality factor, no equity behaviour
changed. Nothing that decides imports the layer, asserted by test.
