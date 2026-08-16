# The denominated monetary comparison boundary

**Status: built, amended in review. `monetary-comparison@1`. No FX, no
threshold change, no band change. Stopped for review.**

Two amendments after the owner's review of the first build (§6–§7):
the establishing set is restricted to independently warranted share
counts — `impliedSharesOutstanding` is out, with the measurement that
decided it — and eligibility is an explicit four-crossing conjunction
in which identity is a prerequisite, with SPCX as the pinned specimen.

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

`MarketCapMagnitude.comparable_with(threshold, warrants)` — the
explicit four-crossing conjunction:

```
identity not unresolved (and evaluated at all)      — whose figure is this
AND measured AND warrant ∈ {VERIFIED, VALIDATED}    — is it a market cap
AND denomination established                        — in what unit
AND magnitude.currency == threshold.currency        — may the units meet
```

Identity is a **prerequisite, not a parallel substitute**: it is
checked first, and no other crossing can compensate for it.
Establishing one crossing never erases another — the property SPCX
pins in §7. An *assumed* identity passes, by #134's own ruling (every
live join rests on symbol equality and is named ASSUMED rather than
silently trusted); an *unresolved* one — the providers' held accounts
disagree — refuses, with a reason that names identity and never
currency; an *unevaluated* one refuses too, because a prerequisite
nobody checked is not a prerequisite met.

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

`reported_shares` carries only counts from the **establishing set** —
`INDEPENDENT_SHARE_COUNT_FIELDS`, fingerprinted under
`monetary-comparison@1`, today `sharesOutstanding` alone. Membership
requires an independently warranted semantic origin: a report of
shares in issue that is not downstream of the market-cap claim it
would corroborate. A count manufactured as `cap ÷ price` makes the
identity a tautology that holds in **any** unit — a pre-converted
dollar cap over a euro price reconciles perfectly against its own
reconstruction and means nothing — and arithmetic cannot detect the
direction, because the two derivations are one equation. That is why
the requirement is semantic and sits on the input, and why widening
the set re-pins a fingerprint rather than editing a tuple (§6). The
three input crossings are registered in the translation inventory as
ASSUMED corroboration inputs — the *derived* denomination is what
becomes VALIDATED, and it carries its `because`.

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

## 6. The establishing set — the independence rule, measured

The first build consulted every count the payload publishes and found
40 USD-establishable against the audit's 29. The owner's review asked
the right question: does `impliedSharesOutstanding` have an
independently warranted semantic origin, or is it downstream of the
market-cap claim it was corroborating? The determination, from
evidence already held and nothing else:

- **No origin warrant exists.** The provider boundary registers the
  field ASSUMED with no statement of what it counts; no provider
  schema in this repository documents it; the first build's sentence
  *"each is the provider's own statement of the same quantity"* was
  asserted, not evidenced.
- **The live corpus measured it reconstructing `cap ÷ price` for
  64 of 64 securities** — within 1.1e-7 relative, median 3.1e-8, ETOR
  to integer exactness — including every dual-class name (GOOG at
  2.21× its reported count, VOW3.DE at 2.43×), every ADR (DIDIY,
  SRAD), and SPCX, whose reported count misses by 74%. **An identity
  that cannot fail checks nothing**: its reconciliation carries no
  information about the cap's unit.
- Per the governing distinction: independently corroborated **0 of
  16** delta names; demonstrably circular at integer reconstruction
  **1** (ETOR); semantic origin unknown, reconstruction-consistent
  with derivation **15**. Unknown origin is insufficient authority,
  not a lesser kind — so the field is out of the establishing set.

The set is now `INDEPENDENT_SHARE_COUNT_FIELDS = ("sharesOutstanding",)`
in `app/domain/monetary.py`, fingerprinted under
`monetary-comparison@1` and pinned in
`tests/test_decision_rule_provenance.py` — widening it is a
written-down act. Nothing hard-codes a population count; the evidence
rule earns whatever it earns.

**The population under the amended rule, measured live 2026-08-16**
(64 equities and funds holding a market cap; 3 more hold none):

| Outcome | Count |
|---|---|
| established **USD** — comparable with the threshold today | **34** |
| established **foreign** — refused pending conversion | **14** (EUR 10, DKK 2, CHF 1, **GBP 1 — BP.L, minor-unit**) |
| structurally unreconciled | **16** |
| insufficient inputs | 0 |

The 16 unreconciled are exactly the names whose establishment had
rested on the circular count: AOS, CPNG, DIDIY, ETOR, F, GOOG, H2O.DE,
META, MSTR, NOVO-B.CO, PLTR, SE, SHOP, SPCX, SRAD, VOW3.DE. The
audit's session measured 29 USD / 13 foreign over the same rule; the
difference (34/14) is payload drift between sessions — reported counts
and caps move into and out of reconciliation as the provider updates
them, which is the known Yahoo instability and one more reason a
population count is never pinned. The regression corpus pins
*specimens* (BP.L, GOOG, the exact-circular construction), not counts.

## 7. Identity is a prerequisite — SPCX, the conjunction's specimen

The owner's second ruling: settling a security's denomination must
never quietly settle its identity. The wiring that makes it structural:

- **The vendor's identity claim is stored at acquisition**
  (`ValuationSnapshot.vendor_identity`, fundamentals cache schema 4,
  identity migration — a pre-capture record restores with the vendor
  having said nothing). The claim is the vendor's own words — name,
  category token, venue — recorded verbatim, never a classification.
- **The join is derived on read** (`CompanyFactsService` →
  `join_identity` over the broker's claim and the stored vendor
  claim), so the join logic can evolve without re-acquisition, and
  the magnitude carries the resulting `CrossProviderIdentity`.
- **The gate refuses an unresolved or unevaluated identity first**,
  with wording that names identity and not currency, and Quality's
  size factor stays unread — never a different band.

The pinned specimen (`tests/test_market_cap_eligibility.py`,
`tests/test_company_facts_service.py`) is #134's recorded SPCX
conflict — eToro instrument 15618 *"Space Exploration Technologies
Corp"* against the vendor's recorded *"SPAC and New Issue ETF"* —
joined by the live ladder, never special-cased: denomination
constructed established-USD (the amendment's *even if*), identity
UNRESOLVED, comparison refused for identity, size factor not restored.

Two live facts reported beside the specimen, not hidden under it.
Under the amended establishing set, today's SPCX payload establishes
**nothing anyway** (reported count misses at 1.74 → UNRECONCILED), so
it is ineligible on two independent grounds. And today's payload
carries a vendor name that *agrees* with the broker's — *"Space
Exploration Technologies Corp."*, quoteType EQUITY — so the join
derived at the next funded acquire may read ASSUMED rather than
UNRESOLVED. The gate is evidence-driven, not a blacklist: if the
held claims stop disagreeing, identity stops refusing, exactly as
#134's own tests demand (*"not special-cased"*). Whether a once-held
conflicting claim should be *remembered* rather than replaced is a
question for the identity boundary's own slice, named here and not
solved.

## The chain, per restored security

```
market-cap claim                    (Yahoo marketCap)
  → denomination established        corroborate_denomination, at acquisition
                                    (independent share counts only)
  → magnitude VALIDATED + currency  CompanyFactsService._market_cap_magnitude
    + identity joined on read       join_identity(broker claim, stored vendor claim)
  → comparable with USD 10bn        MarketCapMagnitude.comparable_with
                                    (identity AND magnitude AND denomination
                                     AND comparison authority)
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

`monetary-comparison@1`, status **ARGUED**, fingerprint `92a418fb4a78`
over the threshold's declared currency, the identical-currency-only
policy, and the establishing set (`INDEPENDENT_SHARE_COUNT_FIELDS`).
ARGUED count 5 → 6. `provider-quality@1` untouched (`3adc0fd3fd9f`).
The rule is unmerged, so the amendment revises version 1 in place
rather than minting a version 2 against nothing.

## Non-goals honoured

No FX implemented or fetched; no suffix or geography inference; no
ADR/dual-class repair (UNRECONCILED routes them to their own
boundary); no threshold, band or fingerprint-input change; no
fallbacks; `CompanyFacts.currency` untouched.

**The FX translation authority boundary is now built** — C6,
[`MONETARY_TRANSLATION.md`](MONETARY_TRANSLATION.md), `fx-translation@1`:
the established-foreign population crosses into USD only through an
explicit, evidenced, same-day translation, and the refusals above are
its exact seams.
