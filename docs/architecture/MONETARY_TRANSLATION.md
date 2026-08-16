# Authorised monetary translation

**Status: built. `fx-translation@1`. No threshold change, no band
change, no decision tuning. Stopped for review.**

C6. #143 left seventeen-then-fourteen securities in an honest cul-de-sac:
market caps established in CHF, EUR, DKK and GBP by the payload's own
arithmetic, and *refused* against the USD threshold pending an
authorised conversion the platform did not hold. This slice is that
authorisation, and only that:

> An established monetary amount in one currency becomes comparable
> with an established threshold in another currency only through an
> explicit, evidenced FX translation. The translation never alters the
> original fact: it creates a derived monetary claim carrying its own
> evidence, and the original remains the provider fact beside it.

## 1. What already existed — the inventory that scoped the seam

The repository already held a single-pair FX seam, built for portfolio
display: `ExchangeRateProvider` reads Yahoo's `EURUSD=X` close and
inverts it **once** into USD→EUR ("the rate is inverted once, here,
rather than at each call site where an inversion could go the wrong
way unnoticed"), `CachedExchangeRateProvider` stores it under a daily
cadence (`data/cache/fx`, schema 1, one record held: USD→EUR 0.8666,
observed 2026-08-11), and `ExchangeRateService` converts the account
total. Its provenance and shape are sound; its *direction* is exactly
backwards for translation (market caps need foreign→USD), and its one
pair covers one of the four needed.

So the acquisition seam is the smallest extension of that provider,
not a second one: `to_usd(base)` reads the **direct** quote
(`CHFUSD=X` is already dollars per franc — inverted zero times), for
the four measured foreign denominations only (`TRANSLATABLE_TO_USD =
("CHF", "DKK", "EUR", "GBP")`), cached under the same daily cadence
and the same stored-door discipline. `movrvest acquire` reads the four
pairs in the same cycle as the fundamentals they translate. No
universal FX service, no routing, no triangulation, no history
warehouse, no second provider: nothing in the evidence forced one.

## 2. The temporal rule — researched, then chosen

What the stores actually hold, measured before choosing (2026-08-16):

| Evidence | Timestamp it carries |
|---|---|
| fundamentals records (77) | `observed_at` = read time; corpus spread across 08-08 (49), 08-09 (27), 08-12 (1) |
| the one FX record | `observed_at` = read time, 08-11 |
| the market cap's own effective instant | **not stored** — Yahoo's `regularMarketTime` exists in the payload and is unread |
| the FX close's own market date | **not stored** — available in the history index, discarded at read |

Neither side of a translation currently evidences its market-effective
instant; both carry the moment *this platform* observed them, on a
declared once-a-day cadence (`is_from_today()` on both stores). A rule
about market instants would therefore be invented rather than
evidenced — so the rule is about the observations this platform holds:

> **A translation is temporally compatible only when the rate
> observation and the market-cap observation share a UTC calendar
> day.** No tolerance beyond the day boundary. A rate from any other
> day — including a last-known rate served after a provider failure,
> which keeps its original date — leaves the translation held but
> **unauthorised**: the derived amount is withheld, and the refusal
> names both dates. "Latest FX" is never silently applied to an older
> market-cap observation, and an older rate is never applied to a
> fresher one.

Why this rule is defensible: it is the cadence both stores already
declare and enforce; `movrvest acquire` reads the fundamentals and the
four pairs in one cycle, so compatible pairs are produced by the
platform's own acquisition act rather than by coincidence; and both
readings, taken together on one day, describe the market as last
settled at that day's observation. Its consequence today, stated
rather than hidden: **the stored corpus holds zero temporally
compatible (cap, rate) pairs** — fundamentals from 08-08/09/12, one
rate from 08-11 — so no stored security's comparison opens in this PR,
and no decision can change until the next funded acquire refreshes
both sides together.

Named for a future slice, not solved: reading `regularMarketTime` and
the FX close's own date would permit a market-effective rule; until
they are read and stored, this platform does not pretend to one.

## 3. The type — `MonetaryTranslation`

`app/domain/monetary_translation.py`, the smallest object carrying
everything C6 requires:

| Requirement | Where it lives |
|---|---|
| source currency | `rate.base`, forced equal to `original.currency` at construction |
| target currency | `rate.quote` (`target`) |
| rate | `rate.rate` — units of quote per one base (`ExchangeRate`, reused, not duplicated) |
| observed timestamp | `rate.reading.observed_at`, and `subject_observed_at` beside it |
| provenance/source | `rate.reading.source` |
| authority | `authorised` — construction guarantees direction and evidence; time is what remains |
| translated amount | `translated` — computed here, only while authorised |
| reference to the original | `original: MonetaryAmount`, never altered |

**Direction is structural.** `CHF→USD` and `USD→CHF` are not labels
around a float: a translation constructed with a rate whose base is
not the original's currency raises (`"inverted or mismatched"`), so
the inverted-rate bug is a loud failure rather than a numerically
plausible wrong answer — and the Nestlé derivation is additionally
pinned to the digit, so a *mislabeled* feed (right direction, inverted
number) fails the product assertion.

**The derived amount cannot exist without its evidence.** There is no
constructor parameter through which a translated figure could arrive;
it is computed from the original and the rate, and only while the
temporal rule holds. The derivation is inspectable without
recomputation:

```
CHF 208,375,545,856 × [CHF→USD 1.2402, Yahoo Finance, observed 2026-08-16] = USD 258,427,351,971
```

No frontend performs this arithmetic; `stated` is built in the domain
and carried out.

## 4. Authority — the fourth crossing, consulted last

The comparison conjunction is now, in full:

```
identity        not unresolved, and evaluated       (#134 / #143 amendment)
AND magnitude   measured, warrant ∈ {VERIFIED, VALIDATED}   (#136)
AND denomination established                         (#142/#143)
AND translation authorised, into the threshold's currency —
                only where the currencies differ     (C6)
```

`comparable_with` consults the translation **after** every earlier
crossing holds, so FX can never rescue an unresolved identity, an
ineligible warrant, or an unestablished denomination — and the facts
service never even asks the rate store in those states, which the
spy-provider regressions pin (`rates.asked == []` for unreconciled,
pre-boundary, and disputed-identity records).

The consumer reads `comparable_amount(threshold, warrants)` — the
amount in the threshold's own currency: the figure itself where
denominations agree, the translated amount where an authorised
translation carries it across, nothing everywhere else. Reading
`magnitude.amount` directly for a foreign figure would compare francs
against a dollar line; the DKK regression (50bn DKK — numerically
above 10bn, USD 7.85bn — below it) flips if that ever happens.

## 5. Pinned behaviour

| Case | Outcome |
|---|---|
| CHF 208bn, authorised same-day rate | comparable; USD 258.4bn against USD 10bn; Quality reads 3/3 |
| EUR / DKK / GBP amounts | translated at their own pairs; DKK pins translated-not-raw |
| same-currency USD | comparable, FX never involved |
| missing rate | not comparable; refusal names the missing `CHF→USD` observation; **never 1:1** |
| rate from another day | not comparable; refusal names both dates; never "latest" |
| unknown denomination | FX never invoked (spy) — and a translation cannot even ride on an unestablished currency (constructor) |
| unreconciled magnitude | FX never invoked (spy) |
| unresolved identity | FX never invoked (spy); refusal names identity, not translation |
| BP.L | the **GBP pounds** figure × GBP→USD — never GBp (the type refuses the pair), never statement USD (`financialCurrency` read nowhere) |
| translation of a different figure | cannot be attached to the magnitude (constructor) |
| translation into a non-threshold currency | not comparable |

**The translation deletion invariant**, which the architecture
supports naturally: deleting FX authority (no translation, or a stale
one) withdraws the size factor entirely — Quality falls to 2/3 and
abstains — and can never reverse a finding: Nestlé reads *Large-cap*
with the translation, *nothing* without it, and *Small or mid-cap*
under no deletion whatsoever.

## 6. Nestlé and BP.L, before → after

**NESN.SW** — before: established CHF by arithmetic (#143), refused
against USD pending an authorised conversion; Quality 2/3, UNKNOWN.
After, *with a same-day CHF→USD rate in the store*: authorised USD
258.4bn (at the pinned specimen rate), size factor reads Large-cap,
Quality 3/3 → HIGH — the full chain pinned end-to-end through
`CompanyFactsService` with the stored-shape evidence. Live today:
still refused — the stored fundamentals (08-09) and any rate acquired
now cannot share a day, and the broker's book currently lists NESN.ZU
(which holds no cap in its payload) where NESN.SW was. The specimen is
the *mechanism*; the population fills at the next funded acquire.

**BP.L** — before: established **GBP** by the minor-unit identity
(ratio exactly 0.010), refused against USD. After: the pounds figure
80,798,785,536 × GBP→USD, pinned exactly — a pence-labelled rate
cannot construct the translation, and the statement's USD has no path
in because nothing on this path reads `financialCurrency` at all.

## 7. No decision changed — and what will, later, legitimately

Measured over the live book after the change: **HOLD 78/78, Quality
authorised 0/78**, both deletion invariants at 0, six specimens HOLD,
`provider-quality` fingerprint unchanged. Nothing *could* move in this
PR: stored fundamentals predate the denomination boundary (no
denomination → no translation is ever attempted), and no stored (cap,
rate) pair shares a day.

The armed causal chain, per foreign security, for the next funded
`movrvest acquire`:

```
acquire (one cycle)
  → denomination established at acquisition     (#143, sharesOutstanding identity)
  → same-cycle {CHF,DKK,EUR,GBP}USD=X rates stored
  → identity joined on read, not unresolved     (#134)
  → translation authorised (same UTC day)       (C6)
  → comparable_amount in USD → size factor readable
  → Quality 3/3 possible → band → kernel direction → recommendation
```

If that acquisition changes a Quality completeness or a decision, it
will be **newly authorised evidence** moving through unchanged rules —
every threshold, band, weight and fingerprinted constant is untouched
in this slice, which the pins prove.

## 8. Rule and provenance

`fx-translation@1`, status **ARGUED**, fingerprint `e3a548db860c` over
the translatable membership (sorted), the same-UTC-day rule, and the
two standing refusals (missing rate is never 1:1; another day's rate
is never "latest"). ARGUED count 6 → 7. `monetary-comparison@1`
untouched at `92a418fb4a78`; `provider-quality@1` untouched at
`3adc0fd3fd9f`; `LARGE_CAP` still `USD 10,000,000,000` built from the
fingerprinted constant. The four pair closes are registered in the
translation inventory as ASSUMED inputs (`Close (CHFUSD=X)` …), with
the EUR entry noting that the display path reads the same field
inverted once at its own seam.

## Recorded, not solved

- **Market-effective time** stays unread (`regularMarketTime`, the FX
  close's own date). The temporal rule governs this platform's
  observations; tightening it to market instants is future evidence
  work, named in §2.
- **One provider.** The rate is a single source's claim, registered
  ASSUMED. A corroboration story for FX (a second source, or a
  cross-pair consistency check) was not built — nothing forced it, and
  C6 forbids inventing it ahead of need.
- **The display seam** (`usd_to_eur`, portfolio page) keeps its own
  inversion and its own undated-consumption semantics; it predates
  this boundary and was not upgraded to the temporal rule. Its repair
  belongs to a portfolio-page slice, not here.
- **NESN.ZU** — the broker book's current Nestlé entry returns no
  market cap from the vendor, so the live Nestlé chain waits on either
  the book naming NESN.SW again or the resolver mapping ZU→SW at
  acquisition (the registry's one suffix entry already documents the
  mapping for profiles).
