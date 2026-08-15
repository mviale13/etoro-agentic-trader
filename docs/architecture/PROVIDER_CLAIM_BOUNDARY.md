# The Provider Claim & Identity Boundary

**Status: built, reporting-first, decision-neutral. Stopped for review.**

The repair slice for the Provider Semantics Audit
([`PROVIDER_SEMANTICS_AUDIT.md`](PROVIDER_SEMANTICS_AUDIT.md), #133),
which measured the equity/broker boundary and found there was none: a
provider field became a domain fact in a single assignment expression,
and three unrelated-looking failures were one architectural defect.

This slice does not fix those failures. It makes them **structurally
visible and enforceably declared**, so that the repairs — which change
behaviour and need their own product story — can be argued against
evidence instead of against memory. Every defect the audit ranked is
still exactly as wrong as it was, and now says so.

The governing principles, unchanged from the brief:

> Reported is not established. Symbol equality is not identity proof.
> Provider taxonomy is not domain ontology. A translation has a
> warrant, not a confidence score. A domain invariant may reject a
> representation; it may not invent provider semantics. Acquisition
> failure is not a measurement of zero.

---

## 1. The executable inventory

`app/domain/provider_translations.py` holds **32 governed crossings**,
each a `ProviderTranslation` (`app/domain/provider_translation.py`)
carrying provider, provider-native field, endpoint, domain concept,
translation kinds, expected representation, warrant, what the provider
declares, decision relevance, and the evidence behind the warrant.

**Construction is the gate.** A translation that names no kind is
refused; a warrant above ASSUMED must name what was checked; a
DECLARED warrant must point at the provider's actual declaration.
A VERIFIED translation with nothing behind it cannot be built — the
same refusal `ValuationBenchmark` makes in #132, applied to
translations.

**The document is generated, not maintained.**
[`PROVIDER_TRANSLATION_INVENTORY.md`](PROVIDER_TRANSLATION_INVENTORY.md)
is the output of `movrvest translations --markdown`, and
`tests/test_provider_translation_inventory.py` fails if the checked-in
copy drifts from the registry. The audit's table stops being a
historical spreadsheet and becomes the thing the code consults. This
follows the audit's own finding about `market_snapshot_archive` — one
translation with two owners is a defect — applied to documentation.

Census, recomputed from the live registry rather than quoted:

| Warrant | Count |
|---|---|
| VERIFIED | 1 |
| VALIDATED | 0 |
| DECLARED | 0 |
| ASSUMED | 27 |
| UNKNOWN | 4 |

The audit's counts were over ~65 mappings at a finer granularity
(every field of every adapter); this registry governs the 32 crossings
where a translation decision is actually made. The shape is the same
and the conclusion is unchanged: **one crossing on this entire path is
warranted**, and it is the venue table somebody checked by hand.

`VALIDATED` and `DECLARED` are empty on purpose. The FX range check
and the balance-history currency gate the audit classed VALIDATED are
on paths this registry does not yet govern; leaving the members unused
rather than borrowing them keeps the census honest.

## 2. The provider-native claim

`ProviderClaim` (`app/domain/provider_claim.py`) records what arrived,
before interpretation: provider, endpoint, field, raw value, request
time, provider observation time, declared unit, declared vocabulary.

Three properties do the work:

- **The endpoint is part of the claim's identity.** Two claims for one
  field name from two endpoints are two claims. Without this the
  `dividendYield` conflict is unrepresentable.
- **Request time and observation time are separate fields that never
  fall back to one another.** `claim.acquisition` is a `Provenance`
  for when we asked; `claim.observation` returns `None` unless the
  provider actually stated when the figure was true — which, on this
  path, is never. The existing `Provenance` primitive is reused
  verbatim for the first and simply not manufactured for the second.
- **Absence is classified, not flattened.** `ClaimAbsence` has five
  members — field absent, reported null, insufficient history,
  malformed stored value, provider unavailable — and
  `is_measurement` returns `False` for every one of them, because
  acquisition failure is not a measurement of zero.

A claim carrying neither a value nor a reason raises, as does one
carrying both.

## 3. Translation kinds

`TranslationKind` — IDENTITY, VOCABULARY, UNIT, SEMANTIC — with each
member carrying the question it asks. A crossing declares a **tuple**,
because `^TNX` needs two (see §7) and a design permitting one per
field could not describe the corpus.

Live distribution: 2 identity, 5 vocabulary, 5 unit, 22 semantic
(they do not sum to 32; a crossing may answer more than one).

## 4. The warrant

`TranslationWarrant` — VERIFIED / VALIDATED / DECLARED / ASSUMED /
UNKNOWN, the audit's vocabulary unchanged. Defined as **authority for
a translation, not confidence in a value**, and deliberately
unordered: there is no domain comparison operator, no numeric weight,
and a test asserts the alphabetical accident of `StrEnum` is not a
ranking. `establishes_domain_fact` is true only for VERIFIED and
VALIDATED — a DECLARED translation is honest and still not
established, because a provider's own word is evidence about the
provider.

## 5. How standing reaches domain facts

`ProviderFact` (`app/domain/provider_fact.py`) is a claim set promoted
under a translation. A consumer asks `fact.warrant`,
`fact.establishes_domain_fact`, `fact.substituted` and `fact.stated`
without opening an adapter.

Two rules are enforced in `promote()` rather than documented beside it:

- **A disagreement overrides the registry.** Where claims conflict the
  fact reads UNKNOWN even if the translation is VERIFIED — proved by a
  guard that deliberately supplies the strongest warrant available.
- **A representation may reject, never convert.** A value failing its
  declared representation is flagged and **served unchanged**. 5.17 is
  not a decimal ratio; that it "looks like" percentage points is a
  guess about Yahoo's intent, and inferring semantics from magnitude is
  the defect rather than the repair.

`ProviderFactLedger` is the reporting surface: established, unresolved
and substituted facts, per security.

**No parallel metadata universe.** `Provenance` is reused as-is.
`EvidenceStanding` is deliberately *not* reused for warrants — it
grades how far a provider's claim about a *value* can be trusted, a
different axis from why a *translation* is permitted, and #133 (via
S4.5) already established that where a fact came from is a second axis
and never a second standing. `FactOrigin` was considered and rejected:
its two members answer a question in the executive conclusion layer
(filing-read versus analyst-assessed), not at the provider boundary.

## 6. Cross-provider identity

`app/domain/provider_identity.py` records what each provider says
before anything joins them, and `join_identity` states what the
evidence supports — deterministically, resolving nothing.

`IdentityStanding` — ESTABLISHED / CORROBORATED / ASSUMED /
UNRESOLVED. It is a separate vocabulary from `EvidenceStanding` for a
precise reason: `EvidenceStanding`'s weakest member, CLAIMED, means
"a source reports it and we cannot check it", and **no source claims
this join at all**. Neither eToro nor Yahoo asserts that eToro 15618
is Yahoo `SPCX`; MOVRvest assumed it by writing one symbol into both
requests. A vocabulary whose weakest state is "a source reports it"
cannot express an assumption nobody made.

**A symbol alone can never establish identity** — enforced in the
join, not documented beside it. The ladder: a shared global identifier
establishes; agreeing instrument *form* corroborates; disagreeing form
is unresolved; **one-sided form evidence is unresolved too**, because
silence is not assent, and reading it as assent is how a fund could
become a company.

No security master is invented. `CrossProviderIdentityService` reads
only evidence already held — the broker's watchlist entry, the
vendor's quote metadata — and carries the provider's raw taxonomy
token (`"5"`, `"ETF"`) untranslated, because translating there would
let the vocabulary assumption in through the identity door.

## 7. Before → after

Each case: the value is unchanged; what it says about itself is new.

**SPCX.** Before: joined on the symbol, eToro's `asset_type_id 5`
becomes `STOCK`, and nothing anywhere records that Yahoo's SPCX may be
a different instrument. After: `join_identity` returns **UNRESOLVED**
with both accounts retained — eToro's "Space Exploration Technologies
Corp" beside Yahoo's fund-shaped record — and
`establishes_identity` is `False`. **No `SPCX → STOCK` or
`SPCX → ETF` repair was made**; the compatibility path still classes
it exactly as before, and is now identifiable as resting on an
unresolved identity. Not special-cased: every other security on the
platform reads ASSUMED for the same reason, which is the finding.

**dividendYield.** Before: one number, scale unknowable, silently
decided by whether an HTTP call succeeded. After: where the unmerged
payloads are available the fact holds **two claims** — `0.0517`
(quoteSummary) and `5.17` (v7) — reads `unresolved`, promotes to
UNKNOWN, and states both readings with their endpoints. Where only the
merged dict exists, the registry warrant is already UNKNOWN. **No
`5.17 → 0.0517` inference anywhere**, and a transient HTTP failure can
no longer alter the promoted field's semantics unnoticed.

**forwardPE.** Before and after, the value is `8.5368805` and
`ValuationObservation` renders exactly what #132 left. What is new is
that the crossing is governed, ASSUMED, and marked `gates a decision`
— so the distinction between *Yahoo reports forwardPE = 8.54* and
*MOVRvest has established a defined forward P/E of 8.54* is now a
property a consumer can read. Nothing was removed; #132's surface is
untouched.

**change_percent.** Before: `0.0` on a short history and `0.0` on a
malformed stored value, indistinguishable from a flat trading day.
After: the same `0.0` flows to the same momentum band, and
`MarketQuote.change_absence` says whether anything was measured, with
`change_is_measured` as the consumer-facing question. The legacy type
is named as the cause in the field's own docstring: `change_percent`
is a bare `float` and has no way to say *unmeasured*, so the adapter
must invent a number. Widening it is a consumer-facing change and was
deliberately not made here.

**EPS fallback.** Before: `trailingEps` or `forwardEps`, one field,
no record of which. After: the value is unchanged, and when a forecast
supplied it the fact is governed by the **`forwardEps` translation** —
concept `ValuationSnapshot.eps (substituted)`, warrant UNKNOWN — with
the realised figure's absence retained as a claim beside it. An
acceptance fixture covers the turnaround case where trailing and
forward differ in sign.

**BP.L currency.** Before: `"USD"` on every quote, hardcoded,
indistinguishable from a provider-declared currency. After: same
string, plus `currency_is_assumed=True` on every Yahoo quote. **The
price is not repaired and GBp is not converted** — BP.L still stores
517.2 — but nothing can now convert by that label believing it was
measured. The v7 `currency` field was *not* silently promoted to
truth: reading it is a new translation and would need its own warrant.

**^TNX.** Before: a yield under the CBOE's ×10 convention entering a
field named `price`, wearing an invented currency. After: a governed
crossing declaring **two kinds on one field** (SEMANTIC and UNIT), at
UNKNOWN, with its representation deliberately left unnamed because
what it should be is exactly what is in dispute. The representation is
not repaired. This is the fixture proving one provider field may
require more than one translation warrant.

## 8–10. The proofs

`tests/test_provider_boundary_guards.py` — 27 tests, one class per
failure mode, written against domain types rather than by scanning
source text:

- **Identity cannot silently compose** — symbol equality yields
  ASSUMED; conflicting forms yield UNRESOLVED; both accounts survive;
  differing ISINs are UNRESOLVED. Plus the inverse, so the guard is
  not a blanket refusal: a shared ISIN *does* establish.
- **Vocabulary cannot cross unwarranted** — an undeclared kind, an
  unevidenced VERIFIED, and a DECLARED warrant pointing at nothing are
  all construction errors. The eToro mapping is asserted to stand at
  ASSUMED *although it matches the provider's truth*.
- **Units cannot collapse** — two endpoints disagreeing are two
  claims; a conflict promotes to UNKNOWN over the strongest warrant;
  promotion never converts.
- **Semantics cannot substitute silently** — the substituted EPS
  concept is governed, UNKNOWN, and cannot borrow the realised
  figure's warrant.
- **Absence cannot become an observed zero** — a valueless claim
  without a reason raises; no `ClaimAbsence` is a measurement; a
  manufactured zero and an observed zero carry the same float and
  answer `change_is_measured` differently.
- **Request time cannot become observation time** — an unsupplied
  observation time stays `None` through claim and fact.
- **A hardcoded currency cannot pass as declared.**

## 11. Decision corpus byte identity

The decision machinery was replayed over a **172,800-trial grid** —
forward P/E, market cap, EPS, dividend yield, daily change, realized
volatility and max drawdown, at every boundary value the audit
surfaced (including the negative P/E, the $10bn line, and both
dividend scales) — hashing every value, band, confidence, point,
sense and evidence sentence produced by the value, quality, momentum
and risk signals plus the committee.

```
before (af726f9): 426ccd06bd2313423f8c0df2b6669501552dbe2a31582a6a20b0b1f188a836a3
after  (this):    426ccd06bd2313423f8c0df2b6669501552dbe2a31582a6a20b0b1f188a836a3
```

**Identical.** Separately, the ledger was run over the **live 77-record
fundamentals corpus**: 1,617 field comparisons, **zero divergences**
between the promoted value and the adapter's own — the property that
keeps one translation from becoming two. (That measurement is run
explicitly rather than as a test, because `data/` is gitignored and a
corpus test would pass vacuously in CI by skipping — #118's rule.)

Full suite: 2,385 passing, mypy clean, ruff clean.

## 12. What was reused from crypto, and what was not

**Reused as-is:** `Provenance`, unchanged, for acquisition time.

**Reused as pattern, not as code:** the claim → validation → standing
→ retained-rejection shape of `token_fact_validation.py`. The equity
boundary is a *translation* gate, not a corroboration gate: the crypto
pipeline decides whether two vendors' numbers agree, this decides
whether we are entitled to read one vendor's field a given way. Same
discipline, different question.

**Deliberately separate:** `EvidenceStanding` (a value's
trustworthiness, not a translation's authority — and #133's own S4.5
rule says a second axis is never a second standing);
`EvidenceAuthority` and `SupplyMethodology` (chain and vendor
vocabulary — equity must not depend on token vocabulary);
`TokenFactStanding`; `FactOrigin` (conclusion-layer). No token module
is imported by anything in this slice, and no equity module was added
to the crypto path.

## 13. Ranked: what remains unwarranted, by causal authority

31 of 32 crossings await a warrant. Ranked by reach — a measured fact
— never by warrant, which is not a quantity. Ties break on the concept
name, so the order is a property of the system rather than of the
file. **Not repaired, per the brief.** Full list in the generated
inventory; the head of it:

| # | Concept | Warrant | Reaches |
|---|---|---|---|
| 1 | `MarketQuote.change_percent` | assumed | gates a decision |
| 2 | `ValuationSnapshot.dividend_yield` | **unknown** | gates a decision |
| 3 | `ValuationSnapshot.eps` | assumed | gates a decision |
| 4 | `ValuationSnapshot.eps (substituted)` | **unknown** | gates a decision |
| 5 | `ValuationSnapshot.forward_pe` | assumed | gates a decision |
| 6 | `ValuationSnapshot.market_cap` | assumed | gates a decision |
| 7 | `YahooInstrument.yahoo_symbol` | assumed | gates a decision |
| 8 | `AssetClass` (watchlist) | assumed | selects analysis |
| 9 | `AssetClass` (catalog) | **unknown** | selects analysis |
| 10 | `ValuationSnapshot.industry` | assumed | selects analysis |

Seven crossings gate a decision, three select which analysis runs.
The two `AssetClass` rows are the SPCX surface; `yahoo_symbol` is the
cross-provider join.

## What this slice deliberately did not do

No valuation benchmark, no change to `pe-bands@1`, the FAIR wall, the
CIO gates, the analyst veto or quality scoring. No `InvestmentEffect`
licensed. No consumer reads a warrant yet — widening
`change_percent` to an optional, refusing an unresolved identity, or
letting a signal decline an UNKNOWN fact are all behaviour changes
that need their own slice and their own product story.

**Recorded and unsolved:** the eToro taxonomy endpoints are still
uncalled, and the architecture now permits acquiring that declaration
to promote the `assetTypeId` warrant from ASSUMED to DECLARED
**without touching domain code** — the registry entry changes, and
nothing else. `MarketQuote` still cannot express an unmeasured change.
`CompanyFacts.currency` is still never assigned. The FX and
balance-history paths are not yet governed by this registry.
