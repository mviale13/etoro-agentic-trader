# The denominated monetary comparison boundary

**Status: built. `monetary-comparison@1`. No FX, no threshold change,
no band change. Stopped for review.**

C5. #142 established that no provider field states a market cap's
denomination and that the platform's one absolute monetary threshold
declared none either. This slice makes both sides say what they are
in, and refuses the comparison everywhere they do not match.

The governing rule, now enforced in types:

> Monetary values may be compared only when both sides have an
> explicit denomination. Different denominations require a separately
> authorised conversion. Absence of denomination is not permission to
> inherit one.

---

## 1. The threshold declares itself

`app/domain/monetary.py` — `MonetaryAmount(amount, currency)`, a
frozen pair whose currency cannot be blank. The policy ruling lives at
[quality_signal_service.py](../../app/services/quality_signal_service.py):

```python
LARGE_CAP_THRESHOLD = 10_000_000_000          # unchanged, still fingerprinted
LARGE_CAP = MonetaryAmount(amount=float(LARGE_CAP_THRESHOLD), currency="USD")
```

The typed threshold is **built from the fingerprinted constant**, so
the two amounts cannot drift, and `provider-quality@1`'s fingerprint
inputs are untouched (`3adc0fd3fd9f`, verified after the change).
`LARGE_CAP.stated` renders `USD 10,000,000,000` — the declaration is
visible in output and can never become implicit again (test 10).

`CompanyFacts.currency` was neither renamed nor repurposed: #142
established it has no trustworthy meaning, and nothing forced its use.

## 2. Denomination-aware comparison

`MarketCapMagnitude.comparable_with(threshold, warrants)` — the #136
conjunction plus the currency identity:

```
measured AND warrant ∈ {VERIFIED, VALIDATED}
         AND denomination established
         AND magnitude.currency == threshold.currency
```

Only same-currency comparison is authorised. The refusal wording
distinguishes the two new cases: an **undenominated** magnitude is
refused because its currency is not established; an **established
foreign** magnitude is refused *pending an authorised currency
conversion, which this platform does not yet hold* — the figure is
known, and what is missing is a licensed transformation. Nestlé is the
second kind now, not the first.

`QualitySignalService._size` consumes `comparable_with(LARGE_CAP, …)`,
so an incomparable magnitude leaves the size factor unread and
`quality-authority@1` withholds the band — never a different band
(test 9).

## 3. Establishment without inheritance

`corroborate_denomination(market_cap, price, shares, quote_currency)`
in `app/domain/monetary.py`, run **at acquisition** in
`ValueProvider.from_info` and stored with the snapshot (fundamentals
cache schema 3; identity migrations; pre-boundary records restore with
no denomination and stay silent).

The only establishment rule, from #142's measurement: where
`cap = price × shares` within 0.5%, the cap **is** that product, and a
product takes its unit from its factors — so the cap is denominated in
the quote unit **by derivation**. Where the price ticks in a declared
minor unit (`GBp`, factor 100 — a fact about sterling, not about any
provider) and the identity holds only at that factor, the cap is in
the major unit.

`shares` carries every count the payload publishes (`sharesOutstanding`
and `impliedSharesOutstanding`); the identity holding for **any one**
of them establishes, since each is the provider's own statement of the
same quantity. The four input crossings are registered in the
translation inventory as ASSUMED corroboration inputs — the *derived*
denomination is what becomes VALIDATED, and it carries its `because`.

Where nothing reconciles, the outcome is **UNRECONCILED** — a
structural fact about share classes or depositary receipts, typed
distinctly from INSUFFICIENT, and `MarketCapDenomination.__post_init__`
refuses a currency on any non-establishing basis, so an inherited
denomination cannot wear a basis (test 8, plus the constructor guard).
**No suffix, geography, or field inheritance appears anywhere in the
function** — the property BP.L pins.

The magnitude's warrant follows the check: a corroborated reading is
*checked against corroborating evidence*, which is exactly
`TranslationWarrant.VALIDATED`'s meaning, so the #136 gate opens for
it; anything else keeps the registry's ASSUMED and stays refused.

## 4. BP.L, the negative specimen

Pinned in `tests/test_monetary_comparison.py` with the live-measured
payload: cap 80,798,785,536 · price 522.90 · shares 15,452,053,728 ·
quote `GBp` · statements `USD`.

The direct identity fails at ratio exactly 0.010, so **GBp is
refused**; the minor-unit identity holds exactly, so the cap is
established **GBP by arithmetic**; and nothing consults
`financialCurrency`, so **USD has no path in** (tests 6–7, at both the
function and the live adapter). Established GBP is then refused
against the USD threshold pending conversion.

## 5. Invariants after the change

| Check | Result |
|---|---|
| Quality authorised | **0/77** (stored records carry no denomination) |
| Recommendations | BUY 0 · **HOLD 77** · SELL 0 |
| Kernel deletion invariant | 143 deletions, **0** hardened |
| Intra-Quality deletion invariant | 42 deletions, **0** direction moves |
| Six blocking specimens | all HOLD |
| `provider-quality` fingerprint | `3adc0fd3fd9f`, unchanged |
| `LARGE_CAP_THRESHOLD` / `BANDS` | `10_000_000_000` / unchanged |

**No investment decision changed in this slice.** The stored corpus
predates the boundary, so every stored magnitude restores without a
denomination and keeps its silence. Restoration happens per security
at the next funded `movrvest acquire`, when the corroboration runs
against a live payload and is stored.

## 6. The recoverable population — measured, with one honest surprise

The shipped `corroborate_denomination` was run against the live
payloads of all 64 equities and funds holding a market cap:

| Outcome | Count |
|---|---|
| established **USD** — comparable with the threshold today | **40** |
| established **foreign** — refused pending conversion | **17** (EUR 12, DKK 3, CHF 1, **GBP 1 — BP.L, minor-unit**) |
| unreconciled / insufficient | 7 |

**This is 40, not the audit's 29, and the difference is reported
rather than shipped silently.** #142's probe checked the identity
against one preferred share count; the shipped rule checks it against
*every* count the payload publishes, and `impliedSharesOutstanding` —
which spans all share classes — reconciles GOOG, DIDIY, NOVO-B.CO and
eight others that the single-count probe called unreconciled. The
principle is identical (the provider's own arithmetic, no inheritance,
no heuristic); the evidence consulted is wider. **If the owner prefers
the audit's exact population, restricting `shares` to
`sharesOutstanding` alone reproduces 29** — a one-line change and a
re-pin.

One consequence worth naming: **SPCX establishes USD** under the wider
rule and would regain a size factor on re-acquisition — while its
*cross-provider identity* remains UNRESOLVED (#134 §6). Denomination
and identity are different crossings; establishing one does not settle
the other, and the identity boundary still holds whatever this one
does.

## The chain, per restored security

```
market-cap claim                    (Yahoo marketCap)
  → denomination established        corroborate_denomination, at acquisition
  → magnitude VALIDATED + currency  CompanyFactsService._market_cap_magnitude
  → comparable with USD 10bn        MarketCapMagnitude.comparable_with
  → size factor readable            QualitySignalService._size
  → quality authority possible      quality-authority@1 (3/3 again)
  → band → kernel direction → recommendation   (all unchanged rules)
```

Knowledge re-enters at step two and nowhere else.

## Nestlé, before and after

Before: bare `208,375,545,856`, denomination absent, size factor
unread, refusal says the currency is not established.
After acquisition under this boundary: **established CHF by
arithmetic**, warrant VALIDATED — and **still refused**, now with the
honest reason: *established in CHF; the threshold is declared in USD;
pending an authorised currency conversion*. Quality still abstains at
2/3. That refusal is the FX translation authority's exact work order.

## Rule and provenance

`monetary-comparison@1`, status **ARGUED**, fingerprint `12627d19b901`
over the threshold's declared currency and the identical-currency-only
policy. ARGUED count 5 → 6. `provider-quality@1` untouched.

## Non-goals honoured

No FX implemented or fetched; no suffix or geography inference; no
ADR/dual-class repair (UNRECONCILED routes them to their own
boundary); no threshold, band or fingerprint-input change; no
fallbacks; `CompanyFacts.currency` untouched.

**Next slice, as ruled: the FX translation authority boundary** — the
17 established-foreign securities are its measured, named work order.
