# Observation Time Authority

**Status: accepted and built.** The rule: *a timestamp is evidence of
what it measures, and a provider publishing one is not a provider
stating when it observed the value beside it.*

A fourth instance of the class `PROVIDER_SEMANTICS_AUDIT.md` catalogued
— a provider field accepted under an assumed definition — and the first
of them where the assumed definition was about **time** rather than
about a quantity. It is also `#223`'s ruling arriving through the
provider door instead of the broker one, and it is answered the same
way.

---

## The defect

The live cycle of 2026-08-21 (`9be89b3aa074`) recorded a price for HYPE
that had moved since the previous run under an `observed_at` that had
not:

| run | price | payload `observed_at` |
|---|---|---|
| 2026-08-20 | 73.43639113145252 | 2026-08-20T14:29:38+00:00 |
| 2026-08-21 | 72.73774324560395 | 2026-08-20T14:29:38+00:00 |

The cache file's own `stored_at` advanced to 2026-08-21T06:59:42, so the
fetch was genuinely fresh and the value genuinely changed. It was the
*source's stated observation time* that did not move.

`TokenFact.observed_at` flows into `CompanyFacts.price_reading` and into
the price-provenance sentence `#231` requires, so all eight tokens in
the book rendered:

> The price for HYPE (hyperliquid) was established by TokenInsight and
> CoinGecko, **observed 2026-08-20 14:29 UTC**, under
> token-fact-establishment@1.

Accurate about what the source states. Misleading about how fresh the
figure is — and a reader takes it as the price's age. It is exactly the
conflation `INTELLIGENCE_JOURNAL.md` names (*the world moved* vs *the
source revised itself*), and it was worst precisely when the data was
best: the three assets whose cache was eleven days stale were roughly
honest, and the five freshly acquired ones were wrong by 16.5 hours.

---

## What was measured

**1. The field does not advance with the price.** Live, in one
90-second window:

| | t0 | t0 + 90 s | moved |
|---|---|---|---|
| `price_latest` | 73.06613809983222 | 73.0488279001271 | **yes** |
| `market_data.last_updated` | 2026-08-20T14:29:38 | 2026-08-20T14:29:38 | no |
| newest `tickers[].last_traded_at` | 2026-08-21T07:09:28 | 2026-08-21T07:09:28 | no |

**2. It is a batch stamp, not a per-quote clock.** Five assets read on
2026-08-21 carried `last_updated` values spanning 49 seconds
(14:29:05–14:29:54), all 16.5 hours behind the fetch.

**3. The provider offers no per-quote timestamp that advances.** Every
timestamp-shaped field in the payload was enumerated:
`rating.update_date` belongs to another object (39 h old),
`ath_date`/`atl_date` are all-time extremes, and
`tickers[].last_traded_at` is a venue's last trade — recent, but frozen
across the same 90 seconds and a different concept in any case. **There
is no field that states when `price_latest` was observed.**

**4. CoinGecko's equivalent field does advance.** Measured the same
morning: 06:56:40 → 07:12:40, minutes behind each fetch. The two
claimants run different kinds of clock.

**5. The figures are contemporaneous; the timestamp was wrong.** Across
all eight tokens the two claimants agreed to between 0.004% and 0.32%
while the clocks they carried stood up to 16.47 hours apart. Pro-rated
from each asset's own stored 24-hour move, a genuine 16-hour separation
implies a gap **6× to 53× larger** than the one measured:

| | BTC | ETH | SOL | TAO | HYPE |
|---|---|---|---|---|---|
| implied by a real 16 h gap | 6.02% | 3.62% | 3.90% | 4.48% | 0.90% |
| actually measured | 0.190% | 0.119% | 0.074% | 0.148% | 0.154% |
| ratio | 31.6× | 30.5× | 52.7× | 30.3× | 5.9× |

So the price is fresh and the stated time does not describe it. The
repair belongs to the clock, **not** to `CROSS_TOLERANCE`.

---

## The ruling

**A source that states no observation time is not a source with a stale
one.** Three wordings were on the table and the measurement chose
between them:

- *Keep the source's stated time and say so* — rests on a premise the
  measurement destroys. TokenInsight does not state an observation
  time; it publishes a timestamp that means something else. Printing it
  as an observation time is a semantic mapping error, not a disclosure.
- *Substitute the fetch time* — prohibited outright by `#223` and the
  intelligence journal. Receipt time is not observation time.
- **Carry the receipt time and name it a receipt time** — `#223`'s own
  answer, and the one built.

`Provenance.observation_stated` (default `True`) carries it. The default
matters: every source that does state an observation time is untouched
and unqualified, so the receipt wording marks a real difference between
sources rather than becoming the platform's uniform hedge. CoinGecko is
still quoted as observing.

**A corroborator's clock is never borrowed.** The temptation is to let
CoinGecko's real observation time date the served figure, since it is
the better timestamp. That would let a claim wear an authority it does
not have — TokenInsight observed nothing at CoinGecko's moment. The
served claimant's own clock dates the fact, and where that clock is a
receipt clock the fact says so. Agreement on a *value* is not permission
to borrow a *clock*.

**The qualifier is a property of the claim, not of the standing.** It
travels through the gate on `TokenFact` because a bare datetime arriving
downstream is indistinguishable from an observation time, and every
consumer would read it as one.

---

## What the investor sees

> The price for HYPE (hyperliquid) was established by TokenInsight and
> CoinGecko, **received 2026-08-21 06:59 UTC (receipt time; TokenInsight
> states no observation time for it)**, under token-fact-establishment@1.

and on a card, `TokenInsight, received 28 minutes ago`.

Sixteen and a half hours of false age withdrawn from five of eight
assets; the three genuinely stale ones still read *11 days ago*, now
from a clock that measures it.

---

## The store

Schema 2, with a migration rather than a re-acquisition. A schema-1
`observed_at` cannot become an observation time (it never was one) and
must not be relabelled a receipt time (it is not that either) — so it is
dropped, and the record's own `stored_at`, a genuine receipt moment,
carries the entry. All eight live assets came forward with their figures
intact.

---

## Found one layer out, and closed with it

`asset_profile_adapter._age` rebuilt a `Provenance` from a fact's source
and moment alone, so the third field defaulted back to `True` and the
row rendered a receipt clock as an observation — the original defect
restored one layer further out. It takes the whole fact now. **The gate
can only carry a fact honestly; every surface that unpacks one has to
keep it that way**, and a test walks the wire payload to prove it.

---

## Recorded, not fixed

- **`CompanyFacts.observed_at` mixes clocks.** It returns `oldest(...)`
  across price, fundamentals and identity readings as a bare datetime,
  so a receipt clock and two observation clocks are compared and the
  winner's kind is dropped. Strictly better than before this slice —
  the crypto price previously entered that comparison with a wrong
  observation time rather than an honest receipt one — but the
  comparison itself is still not clock-aware.
- **What `market_data.last_updated` actually measures is unestablished.**
  It was measured *not* to be the price's observation time. It was not
  measured to be anything in particular, and nothing here claims it is.
- **The capital envelope is unaffected, by construction rather than by
  design.** Its staleness gate reads `brain.market.quotes`, which holds
  nothing for a token whose vendor listing `#231` refused. If crypto
  sizing is ever built, that gate will need a clock-aware age — a
  receipt time is a legitimate input to a freshness policy, but only one
  that knows it is reading one.
