# Crypto Intelligence, slice 2 — current events and market narratives

**Status: built 2026-08-10. Decision-neutral.** No recommendation
threshold moved, no crypto-quality factor changed, no quorum touched,
equity untouched. No model is asked anywhere in the slice.

> What happened recently that could materially change the investment
> case or explain current market behaviour?

```bash
movrvest crypto-intelligence BTC          # the brief
movrvest crypto-events BTC --evidence     # the developments, with sources
```

---

## A. Source measurement

Every candidate was probed before anything was built on it. Thirty-one
surfaces; the ones that decided the design:

| Source | API? | Cost | Freshness | Coverage | Tier | Verdict |
|---|---|---|---|---|---|---|
| **CoinGecko insights** (`/en/coins/{id}/insights`) | **no — web only** | free, keyless | ISO to the minute, newest ~30 min | **8 of 8** corpus assets, 8 entries each | aggregator | **integrated** |
| **DefiLlama `/hacks`** | yes, JSON | free, keyless | 613 incidents, newest 2 days | by chain: 6 of 8 assets | primary | **integrated** |
| **GitHub `/releases`** | yes, JSON | free, keyless (60/hr) | latest BTC 2026-07-10, ETH 2026-07-27 | 3 assets have a canonical client | primary | **integrated** |
| CoinDesk / Cointelegraph / The Block / Decrypt RSS | yes, XML | free, keyless | minutes | broad, unfiltered | secondary | **integrated, corroboration only** |
| CoinGecko `/api/v3/news` | — | **401 — PRO only** | — | — | — | declined |
| CoinGecko `/coins/{id}/status_updates` | — | **404, endpoint gone** | — | — | — | declined |
| CryptoPanic | — | **403 Cloudflare** | — | — | — | declined |
| Messari news | — | **404** | — | — | — | declined |
| Snapshot GraphQL (governance) | yes, POST | free, keyless | works — proposals real | **every proposal closed** for the two governed corpus assets; BTC/ETH/HYPE are not governed this way | primary | **measured, not integrated** |
| SEC / CFTC press RSS | yes, XML | free | days | crypto-specific items rare and unlabelled | primary | measured, not integrated — no way to select the relevant items without a keyword model |
| Farside, CoinGlass, Mobula, CoinCap | — | HTML / key / 500 / DNS | — | — | — | declined |

### §5: the CoinGecko narrative surface, answered point by point

The ruling named this as the acceptance case and asked seven questions.

- **API-accessible or web-only?** **Web-only.** `/api/v3/news` returns
  401 *"limited to PRO API subscribers"*; `/coins/{id}/status_updates`
  returns 404 — the endpoint no longer exists. There is no free JSON
  surface carrying this content.
- **Publication timestamp / freshness?** Minute-resolution ISO stamps
  (`data-rel-time="2026-08-10T15:51:00Z"`), newest entry 31 minutes old
  when measured.
- **Underlying source links exposed?** **Yes.** Each entry names its
  sources; the per-insight page carries each source's own paragraph and
  its outbound URL.
- **Per asset?** Yes — the asset *is* the URL.
- **Coverage for BTC / ETH / HYPE?** All three, richly: 8 entries each.
- **Generated from identifiable news/events?** Yes, and cited.
- **Access/cost?** Free, keyless, no attribution requirement found.

**So it is web-only, and §5 says to report that before scraping it.**
Reported. The risk is real: this is not a published interface, nothing
obliges CoinGecko to keep it, and a page change breaks the parse. Two
things make it worth taking. The parse reads **`data-` attributes and
two component classes** — machine scaffolding, not visual layout — so it
fails loudly rather than mis-reading quietly. And when it breaks it
reports `EventFeedHealth` rather than an empty brief:

```
CoinGecko Insights returned 8 entries and 8 could not be read —
its page shape may have changed
```

**A surface that returns nothing and a surface that returns nothing
*because it changed* must not look the same.**

### The rule that keeps the press out of the brief

> **A press item may corroborate an event another source established. It
> may never introduce one.**

A wire carries a hundred headlines a day, of which perhaps three bear on
a held asset — and this platform has no way to tell which three. A
keyword gate over headlines *is* a relevance model, and a bad one, and
it produces exactly the "longer news list" the ruling calls failure.
What the press can do with no judgement at all is answer a question
already asked: **did anyone else report this?** That is matching, not
selection.

---

## B. The canonical model

```text
CryptoEvent          one development, however many sources reported it
  identity           subject | family | day | shared figure
  ├─ SourceReport    one source's account, with its tier and its link
  ├─ EventFact       an asserted sentence, REPORTED, with its anchors
  └─ Interpretation  a source's reading, ATTRIBUTED, with is_causal
EventFeed            events + EventFeedHealth per surface
```

**Nine families**, each observed in the live corpus *before* it was
declared: `REGULATORY`, `SECURITY`, `PROTOCOL_UPGRADE`,
`INSTITUTIONAL_ADOPTION`, `CAPITAL_FLOW`, `NETWORK_OPERATION`,
`MARKET_STRUCTURE`, `ECOSYSTEM_ADOPTION`, `TOKENOMICS`. **`GOVERNANCE`
is measured and declined** — Snapshot answers keylessly, but every
proposal for the two governed corpus assets is closed and none of BTC,
ETH or HYPE is governed that way. A family with no instance is a
category waiting to be filled.

**Three source tiers**, and a tier is *not* a standing: `PRIMARY` (the
register or the party itself), `SECONDARY` (a publication),
`AGGREGATOR` (a vendor's summary over other people's reporting).

### The epistemic boundary, and the rule that draws it

**A hedge separates a fact from a reading; a number makes a fact
checkable.** Two different properties, and the first draft conflated
them — it required a digit before a sentence could be a fact, and duly
filed *"AUSTRAC suspended Cryptolink's VASP registration"* as an
opinion. The corrected rule:

| Sentence | Outcome |
|---|---|
| *"Marathon sold 23,093 BTC, valued at ~$1.6 billion"* | `EventFact`, anchors `23093`, `1600000000` |
| *"AUSTRAC suspended Cryptolink's VASP registration"* | `EventFact`, no anchors — still a fact |
| *"This indicates sustained institutional demand"* | `Interpretation`, attributed |
| *"Ethereum **dominates** RWA lending deposits"* | `Interpretation` — a grading is an assessment |
| *"ETF demand is **supporting** the price"* | `Interpretation`, `is_causal=True` |

**Gradings are markers.** *dominates*, *significant*, *robust*,
*elevated* are the writer's score wearing a reported fact's clothes, and
they are the sentences most likely to be mistaken for measurements.

**The headline is never decomposed.** It is the vendor's framing and it
is already the event's name; decomposing it too produced every claim
twice and asked whether *"Ethereum Dominates RWA Lending Deposits"* is a
measurement.

### Identity, and the two defects that shaped it

`identity = subject | family | day | shared figure`. The figure does the
work: two outlets never choose the same words and almost always quote
the same number. Normalisation therefore matters more than it looks —
and both of these were produced against live copy:

- **`"23,093 BTC"` → 23,093 *billion***, because the magnitude table
  matched `b` inside `BTC`. Not a rounding error: an anchor no other
  account of the same event could ever match.
- **`"since China's 2021 ban"` → 2,021 *billion***, same cause, and
  bare years are now excluded outright — an identity built on `2026`
  would collapse every event of the year into one.

---

## C. Flow distribution — and the defect it exposed

The slice-1 handoff flagged that a 30-day total without dispersion
*"reads as steadier demand than the data supports."* The measurement
proved the flag right, and by more than expected:

| | BTC | ETH |
|---|---|---|
| Net, 30 published days | **+$128m** | **+$540m** |
| Positive days | 18 of 30 | 21 of 30 |
| Largest day of buying | +$266m | +$92m |
| **Largest day of selling** | **−$445m** | −$71m |
| Biggest day ÷ net total | **3.48×** | 0.17× |
| Current streak | +5 | +4 |
| **Shape** | **concentrated** | **persistent** |

**BTC's single largest outflow day is three and a half times the whole
month's net total.** The month is noise around a near-zero residue.
ETH's $540m arrived on 21 of 30 sessions with no day above $92m — that
is accumulation. Slice 1 printed both as *"$Xm net, positive on N of
30"* and they read as the same thing, differing only in size.

**Fixing the sentence was not enough.** With only the wording changed,
the brief contradicted itself — the claim said *"offsetting flows rather
than accumulation"* while the driver beside it still called the same
month *"a net source of demand"* and filed it under **tailwinds**. The
driver was slice 1's sign test on the sum, and it had to change too. BTC
now has **no flow tailwind**; the driver reads:

> Fund flows netted positive over the month, but on offsetting sessions
> rather than sustained buying. *(observed)*
> why it matters: the net total is the residue of days pulling both
> ways, so it is a weaker signal of demand than its size suggests.

Stored under cache schema **2**, with a schema-1 migration that leaves
the three new figures **absent rather than zero** — the daily series was
never stored, and a zero would say the biggest day was nothing.

---

## D. BTC brief — real output

```
BTC — current intelligence
  Monetary network · read 2026-08-10 16:45 UTC

  What changed
    · BTC returned +0.2% / +3.9% / +1.1% over 24h / 7d / 30d   (reported · CoinGecko)
    · US spot BTC ETFs took $99m net on 7 August               (reported · SoSoValue)
    · Over the last 30 published days those funds took $128m net, positive on
      18 of them; the largest single day of buying was $266m and the largest
      day of selling -$445m — a single session outweighed the month's whole
      net total, so this is offsetting flows rather than accumulation.
                                                               (measured · MOVRvest)
    · Those funds hold 1,223,634 BTC — 6.1% of the supply       (reported · SoSoValue)
    · 179 public companies report holding 1,282,501 BTC         (reported · CoinGecko)
    · Bitcoin: $139k paid in fees over a day                    (reported · DefiLlama)

  Material developments
    · [Security] COLDCARD: $115m lost to Non-Random Private Key Generation
      (31 Jul · DefiLlama · primary source · ongoing)
    · [Regulatory] AUSTRAC Suspends Cryptolink Bitcoin ATM Registration
      (10 Aug 14:51 · 2 sources · press report)
    · [Institutional participation] Marathon Sells 23,093 BTC in First Half 2026
      (10 Aug 15:51 · 2 sources · press report)
    · [Institutional participation] H100 Group Increases Bitcoin Holdings to 3,506 BTC
      (10 Aug 13:52 · 5 sources · press report)
    · [Institutional participation] MicroStrategy Sells 1,690 BTC for Stock Buybacks
      (10 Aug 12:40 · 8 sources · press report)

  What appears to be driving it
    · Fund flows netted positive over the month, but on offsetting sessions
      rather than sustained buying.                            (observed)
    · Identifiable institutional balance sheets hold a material share.  (MOVRvest)
    · Security: COLDCARD: $115m lost to Non-Random Private Key Generation (observed)
      why it matters: it is still running, so the next reading may differ.
    · Regulatory: AUSTRAC Suspends Cryptolink Bitcoin ATM Registration
    · Fund flows were net positive over the last month while the asset moved +1%.
                                       (coincident, not shown to be causal)

  Headwinds
    · Security: COLDCARD — $115m lost to Non-Random Private Key Generation
    · Regulatory: AUSTRAC Suspends Cryptolink Bitcoin ATM Registration

  Watch next
    · Whether COLDCARD is resolved — the register still records this one as unsettled.
      measured by: the incident register's own record of funds returned
    · Whether fund flows stay positive over the next few sessions, and whether
      the pattern stops being offsetting days around a small net total.
      measured by: the published daily net flow, and the count of positive days
```

**§6's acceptance set, checked against what is actually present:** ETF
flow developments ✅, institutional holdings/adoption ✅ (three separate
events), major regulatory action ✅ (AUSTRAC), network/security incidents
✅ (COLDCARD, mining difficulty), **major custody/hardware security
events ✅** — COLDCARD is exactly that, and it arrived from the incident
register rather than from any list of expected events. Protocol/fork
developments: Bitcoin Core v29.4 was read and **aged out** at 10 days,
correctly. Nothing is prescribed in code.

---

## E. ETH brief — a genuinely different event set

ETH's five developments share **one family** with BTC's five:

| BTC | ETH |
|---|---|
| Security — COLDCARD wallet keys | Security — Coinsbuy wallet drain |
| Regulatory — AUSTRAC | **Token economics** — Tether destroys 1.75bn USDT |
| Institutional — Marathon | **Capital flow** — $245m ETH ETF inflows |
| Institutional — H100 | **Network operation** — record staked supply, 41.4M ETH |
| Institutional — MicroStrategy | **Market structure** — large holder exits at a $19m loss |

Plus what only ETH has in *What changed*: **`Ethereum: $32k reached
holders over a day. Amount of ETH burned — base fees plus blob fees.`**
None of this is a branch on the symbol — the families come from the
evidence, and the same parser reading Bitcoin's markup under the symbol
`ETH` produces Bitcoin's events attributed to ETH (asserted by test).

ETH's flows are also the better story, and now visibly so: **persistent**
against BTC's **concentrated**.

---

## F. HYPE brief — no ETF concepts, and no complaint about it

HYPE's five developments are venue and network events. **This platform
reads no fund flow for it and nothing says one is missing.**

One finding worth recording. A source published *"HYPE Spot ETFs record
$2.84M net inflows last week"*, so HYPE now carries a `CAPITAL_FLOW`
**event**. That is not MOVRvest asserting a fund group exists — it is
MOVRvest reporting that somebody else did, carried as an attributed
claim about a vehicle this platform holds no reading for. The
distinction is the whole layer, and it forced a slice-1 test to be
sharpened: the guard used to say *no capital-flow claim of any kind* and
now says **no flow reading**, which is what it always meant.

HYPE keeps its tension: *economic activity is reaching the token itself*
(tailwind) beside *the asset has moved −18% over a month* (headwind).

---

## G. Narrative decomposition — one provider paragraph, four outcomes

Taking the eight-source MicroStrategy event:

**Raw attributed narrative** (CoinGecko Insights):
> *"MicroStrategy Sells 1,690 BTC for Stock Buybacks: MicroStrategy sold
> 1,690 BTC for approximately $109 million between August 3-9. Proceeds
> were used for STRC stock buybacks, reducing their total Bitcoin
> holdings to about 840,447 BTC."*

**Factual claims** (`REPORTED`, with anchors):
- *MicroStrategy sold 1,690 BTC for approximately $109 million between August 3-9* — `1690`, `109000000`
- *Proceeds were used for STRC stock buybacks, reducing total holdings to about 840,447 BTC* — `840447`
- *Strategy (MSTR) reported on Monday the sale of Bitcoin worth roughly $109 million* — `109000000`

**Corroborated claims** — per fact, not per event:
- the sale figure: **✔ also reported by CoinDesk, Cointelegraph, The Block, Decrypt**
- the holdings figure: **single account** — no outlet's headline carried it

**Source interpretation** (`ATTRIBUTED`, never promoted):
> *"The move is an explicit capital-management action by Strategy…"* — Elfa AI

**Unresolved causal statement** (`is_causal`, kept and never settled):
> *"This indicates sustained institutional demand for ETH, potentially
> supporting price discovery"* — CoinGecko Insights, on ETH's ETF event.
> The event's `status` becomes `UNRESOLVED` and the driver it produces
> is `ATTRIBUTED_BY_SOURCE`, worded *"CoinGecko Insights: …"*.

---

## H. Deduplication — eight accounts, one event

```text
MicroStrategy Sells 1,690 BTC for Stock Buybacks
identity: BTC|institutional_adoption|2026-08-10|1690
family: institutional_adoption · tier: secondary · 8 sources

  CoinGecko Insights  [aggregator]  coingecko.com/…/insights/102229425
  Elfa AI             [secondary]   app.elfa.ai/…
  FXStreet            [secondary]   fxstreet.com/…/strategy-sells-another-…
  Tree News           [secondary]   news.bloomberglaw.com/crypto/…
  CoinDesk            [secondary]   coindesk.com/markets/2026/08/10/strategy-sells-1-690-bitco…
  Cointelegraph       [secondary]   cointelegraph.com/markets/strategy-sells-1690-btc-buy-back-…
  The Block           [secondary]   theblock.co/news/business/2026-08-10-michael-saylor-strate…
  Decrypt             [secondary]   decrypt.co/375196/strategy-sells-109m-in-bitcoin-as-dollar-…
```

Four of those are independent press outlets, matched on the shared
figures `1690` and `109000000` — **not on shared words**, which they
barely have. No interpretation was averaged: Elfa AI's two readings
appear under Elfa AI's name and nobody else's.

Two guards the live corpus forced:

- **A press item must name the asset.** Without it, four *bitcoin* ETF
  stories attached themselves to **Ethereum's** ETF event on four shared
  words — *spot*, *ETFs*, *inflows*, *week* — and no shared subject.
- **A small number is not an identity.** *"between August 3-9"* yields
  the anchors `3` and `9`; a headline is very likely to contain a small
  number for reasons of its own. Only figures ≥ 1000, or percentages,
  can identify an event alone.

---

## I. Freshness — stale events leave, and the section says so

The same stored BTC events, read at four moments:

| Read at | Live events | Leading |
|---|---|---|
| now | 9 | COLDCARD: $115m lost… |
| +3 days | 8 | AUSTRAC Suspends Cryptolink… *(COLDCARD aged out)* |
| +8 days | 8 | AUSTRAC Suspends Cryptolink… |
| **+20 days** | **0** | **— no material current event identified —** |

Stale events are **dropped, not ranked last**. Ranking them last still
surfaces them once the list is short, which is precisely §10's *"do not
keep a stale event because no newer event exists."* The empty state is a
stated absence:

> *No material current event identified. Nothing recent enough and
> material enough was found — this is a stated absence, not an empty
> section.*

---

## J. Deterministic fallback — it *is* the implementation

No model is asked anywhere in this slice. `crypto_event_service`,
`crypto_intelligence_service`, `crypto_events` and `intelligence_brief`
reach no writer, no provider, no prompt — asserted by an import-graph
test over the parse tree, not a text search. Every output above is the
deterministic renderer.

**Materiality is ranked, never scored** (§11). Five ordinal terms read in
order: family → still running? → how close the reporting gets →
corroborated? → how new. No weights, no thresholds, nothing to tune. A
materiality *score* for news is exactly the kind of number five slices
have declined to invent.

**Causality is guarded** (§12). Three things the layer will say, and one
it will not:

| | |
|---|---|
| ✅ `OBSERVED` | a development that changes what the asset durably is |
| ✅ `COINCIDENT` | *"Fund flows were net positive over the last month **while** the asset moved +1%."* |
| ✅ `ATTRIBUTED_BY_SOURCE` | *"CoinGecko Insights: this indicates sustained demand…"* |
| ❌ | *"inflows prevented BTC from falling"* — no construction produces this |

---

## Boundaries held

- **Asset Quality** cannot be reached from any event module, in either
  direction. Every crypto asset still reads UNKNOWN; every brief renders
  anyway.
- **The decision layer** is untouched — no `InvestmentDecision`,
  `Recommendation`, `DecisionSynthesis` or `CommitteeOpinion` is
  reachable. No threshold moved.
- **Durable → current, never the reverse** (§19). An event may explain a
  supply rule; nothing here rewrites one. The intelligence layer reads
  the canonical families and writes to none of them.
- **A page view acquires nothing.** `CryptoEventService.stored()` is the
  read-only door; `movrvest acquire` is the spend.
- Equity behaviour unchanged.

---

## K. Is the structured intelligence rich enough for an LLM?

**Yes — for BTC and ETH decisively, for HYPE adequately.** The test the
ruling set was whether an LLM would *materially improve prioritisation
and explanation* rather than *compensate for missing evidence*. Slice 1
failed that test and said so; this one passes it, and the evidence is
that the deterministic output is now visibly **under-synthesised rather
than under-evidenced**:

- BTC carries 9 events across 5 families, 8 sources on one of them, 12
  claims, 5 drivers, 20+ attributed sentences with authors, and a flow
  distribution. That is more material than any brief should print.
- The remaining weakness is **ordering and connection**, not supply. The
  deterministic layer cannot say that MicroStrategy selling, Marathon
  selling and dormant coins moving are *the same story about holder
  behaviour*, or that a concentrated flow month and a +1% price are
  consistent with each other. Those are synthesis judgements.
- Every ingredient an LLM would need is ref-addressable and typed:
  claims by ref, events by identity, each sentence already labelled
  measured / reported / attributed / inferred, each causal assertion
  already flagged. **A writer can be forbidden from adding**, because
  `snapshot.grounded` is a checked property covering drivers, watch
  items *and* narratives.

Two honest caveats. **HYPE is thinner** — its events are venue activity
and market structure, and an LLM would have less to prioritise. And
**the deterministic drivers are still shallow**: *"Regulatory: AUSTRAC
suspends…"* states the family and the headline and does not explain why
an Australian ATM registration matters to a Bitcoin holder. That is the
gap synthesis should close, and it is a synthesis gap.

---

## L. Recommendation — the smallest LLM synthesis slice

**Do not build it yet; this is the specification for when you rule.**

> **Slice 3: the writer orders and explains, and cannot add.**

Scope, deliberately minimal:

1. **One call per asset, over the existing snapshot.** Input is the
   structured object serialised — claims with refs, events with
   identities, drivers, flow distribution, foundation. No fetching, no
   tools, no second pass.
2. **Three outputs only**, each constrained:
   - a **lead paragraph** (≤60 words) — what changed and what matters
     most, citing refs;
   - **why each of the top three developments matters to a holder**
     (≤25 words each), citing the event identity;
   - a **reordering** of `watch_next`, choosing from items already
     constructed and never composing new ones.
3. **The validator is the slice.** Reject any output containing a ref or
   identity the snapshot does not hold; reject any causal verb
   (*because*, *caused*, *drove*, *prevented*) joining a development to
   a price move unless it quotes an `ATTRIBUTED_BY_SOURCE` driver;
   reject any figure not present in a claim. The PR #95/#96 lesson
   applies directly — **forbidden language is refused by the validator,
   not asked for in the prompt.**
4. **The deterministic brief stays the floor.** Writer disabled → today's
   output, unchanged. Writer failing validation → today's output, and a
   line saying the wording was refused.
5. **Configured on the existing seam** (`MOVRVEST_WRITER_*`), small
   model, opt-in behind a flag, and **not run on a page view** — the
   dossier latency lesson from PR #97 says the case and the wording are
   two requests.

What it must **not** do: choose which events appear (that is §11's
ranked rules, and a model choosing materiality is a scoring model in
prose), assert causality, touch Asset Quality, or reach the decision
layer.

**Only after that** should a decision contract be considered — and as
evidence projected onto `Finding`, per `ASSESSMENT_CONVERGENCE.md`,
never as a score.
