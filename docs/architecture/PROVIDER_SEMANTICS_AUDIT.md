# The Provider Semantics Audit

**Status: investigation, stopped for review. Nothing here is a repair.**

The boundary audited: where an external provider's field becomes a
MOVRvest domain fact. Three trust failures seeded it, all found during
the valuation arc (`VALUATION_AUTHORITY.md`, `VALUATION_COMPARISON.md`):
Yahoo `forwardPE` accepted although its precise definition is
undisclosed; Yahoo `dividendYield` entering with a ×100 scale mismatch
(BNP.PA stored as 8.85 where the domain convention says 0.0885); and
eToro `asset_type_id = 5` trusted as *stock* for SPCX, an ETF. The
question the owner set: are these three defects, or one architectural
defect — and **what must MOVRvest establish before a provider's field,
unit, taxonomy or semantic label is allowed to become a domain fact?**

Three principles govern every finding below, stated before any of them:

1. **A provider value is evidence of what the provider reported.** It is
   not automatically evidence that MOVRvest has established the same
   domain fact.
2. **Provider taxonomy is not domain ontology.**
3. **Plausible numbers are not validated numbers.**

The verdict, stated first and argued throughout: **one architectural
defect, three surfaces.** The equity/broker path has no boundary at all
between *reported* and *established* — every field crosses in one
assignment expression, and the three failures are the three translation
kinds (unit, semantics, identity/vocabulary) each failing in the only
way an unguarded crossing can fail. The platform already owns the
missing architecture: the crypto path built it in #99, and when the
same provider threw the same class of defect at that path — Yahoo's
$8,105 price for an $18bn token — the gate caught it and retained the
rejection with its reason. The audit's recommendation (§10) names the
smallest boundary that prevents the class. **It is not implemented.**

---

## How this was measured

Everything below is measured, not asserted: the live adapters were read
line by line; the installed provider library (`yfinance 1.5.2`) was read
at source; both Yahoo endpoints behind `Ticker.info` were fetched
separately for two live listings and diffed key by key; the stored
corpus in `data/cache` was enumerated; and every consumer of every
translated field was traced to the decision layer or to its absence.
Where a claim could not be measured — Yahoo publishes no definition to
audit — the absence is reported as the finding.

## 1. The live provider → domain translation inventory

Granularity rule: one row per provider field crossing into a domain
object (a fallback chain is one row; a statistic MOVRvest computes
from provider closes is counted once, at its input). Everything below
is a live path; unused SDK fields are excluded.

**Yahoo fundamentals** — `Ticker.info` → `ValuationSnapshot`
([value_provider.py:67–102](../../app/providers/value_provider.py)),
23 rows. Two receive a unit conversion (`netExpenseRatio`,
`debtToEquity` — both `/100`, each earned by one past defect); two
carry silent key-fallbacks (`trailingEps → forwardEps`,
`volume24Hr → regularMarketVolume`); `startDate` gets a guarded
timestamp parse; `sector`/`industry` a non-blank string guard. The
remaining raw numerics (`forwardPE`, `trailingPE`, `pegRatio`,
`dividendYield`, `marketCap`, the growth/margin/balance-sheet family)
cross as-is — and the nine fields at lines 68–76 bypass even the
`_ratio` type guard, so a provider string or bool would land in the
domain object unconverted (the cache restore's stricter cast then
silently drops it: pre-cache and post-cache snapshots are not
equivalent). Provenance: `datetime.now(UTC)` — the payload offers no
reading time and none is sought.

**Yahoo quotes** — `yf.download` closes → `MarketQuote`
([yahoo_market_provider.py:232–269](../../app/providers/yahoo_market_provider.py)),
5 rows: `price` (last close, `auto_adjust=True` applied by the
library and unstated downstream), `change_percent` (computed; `0.0`
manufactured on short history and on zero-previous), `currency`
(hardcoded `"USD"`), `name` (eToro's display name attached to Yahoo's
numbers), and the close-series input from which volatility, drawdown
and sensitivity are derived (length/finite guards only). The VIX is
a bare undated float; a failed VIX fetch is cached and served for the
TTL as if measured. **The provider's own close dates are read for
alignment and discarded for provenance** — a Friday close served on
Sunday is dated Sunday.

**Yahoo history** — closes → `dict[date, float]`
([yahoo_price_history.py:120–132](../../app/providers/yahoo_price_history.py)):
the one Yahoo reader where the provider's dates *survive* (as dict
keys) — and the one carrying no `Provenance` at all.

**FX** — `EURUSD=X` → `ExchangeRate`
([exchange_rate_provider.py:56–67](../../app/providers/exchange_rate_provider.py)):
inverted, and guarded by `rate > 0` — **the only numeric range check
applied to any provider value on the entire equity path**.

**Earnings** — `Ticker.calendar` → `EarningsWindow`
([earnings_provider.py:33–66](../../app/providers/earnings_provider.py)):
date-typed filter only; the empty tuple is correctly preserved as
"no date published" distinct from a failed read. The cache is keyed
by the **Yahoo** ticker while the surrounding domain speaks eToro
symbols — two identity spaces, one store.

**eToro account** — `/pnl` → `AccountSnapshot`/`PortfolioPosition`
([etoro_account.py:75–217](../../app/brokers/etoro_account.py)),
~10 money rows: every monetary figure passes `_number`, whose
malformed-value default is `0.0` — **a broken payload value is
indistinguishable from a real zero** in every field except `credit`.
The account's currency is assumed USD (`_usd` suffixes asserted,
never evidenced); `connected=True` is hardcoded; payload shape is
discovered by BFS for any of five keys, first hit wins.

**eToro watchlists / instrument catalog** → `WatchlistItem`
([etoro_watchlist_parser.py:54–80](../../app/services/etoro_watchlist_parser.py),
[instrument_metadata_service.py:67–102](../../app/services/instrument_metadata_service.py)),
~11 rows: type-guarded with integer defaults of 0 — an absent
`assetTypeId` silently becomes 0 → UNKNOWN, an absent `instrumentId`
becomes the valid dict key 0. The two endpoints name the same
concepts differently (`assetTypeId`/`instrumentTypeID`,
`symbolName`/`symbolFull`, `exchangeId`/`exchangeID`) and both feed
the same domain fields — **nothing establishes that the two key
families share a codespace**.

**eToro history/identity/rate envelope**: balance history parses
eToro's own dates (string-truncated `[:10]`) and carries the one
currency gate on the path (`totalCurrencyIso == "USD"` before the
fallback figure is accepted —
[portfolio_history_service.py:137](../../app/services/portfolio_history_service.py));
OAuth scopes and ratelimit headers are read under vocabularies the
repo actually documents ([ETORO_API.md](../ETORO_API.md)).

**Identity translations** (symbol → provider ticker): pass-through
for equities, `VENUES` (`ZU → SW`, hand-verified, one entry),
`-USD` suffix for crypto, and the nine hardcoded
`DEFAULT_INSTRUMENTS` (`WTI → CL=F`, `DXY → DX-Y.NYB`,
`TNX → ^TNX`). On the filings path — outside this audit's decision
scope but the repo's own counter-example — symbol → ISIN crosses a
43-entry reviewed table and is then **cross-checked against GLEIF's
legal name, refusing on mismatch**
([issuer_identity.py:146–155](../../app/providers/issuer_identity.py)).

**Vocabulary translations**: `assetTypeId → AssetClass` (four rows,
§6); Yahoo `sector` string → `Sector` enum (casefolded table,
unmatched → OTHER — an unrecognised sector is indistinguishable from
an absent one,
[company_profiler.py:9–28](../../app/services/company_profiler.py));
Yahoo `industry` string → `PlaybookKind` (ordered substring table,
[playbook_selector.py:31–57](../../app/services/playbook_selector.py));
eToro `exchangeId` → `CompanyFacts.exchange` as a **stringified
integer with no vocabulary anywhere** (`exchange="4"`).

**The four validations that exist, in full**: the all-fields-empty
`carries_nothing` raise (payload-level), the FX `rate > 0` range
check, the balance-history currency gate, and the GLEIF name
cross-check (filings side). No range check, no unit check, and no
cross-source corroboration exists anywhere else on the path. The
crypto gate (`TokenFactsService`) is referenced by
`company_facts_service.py` itself for token market caps — the
boundary exists in the same file and stops at the asset class.

---

## 2. Semantic trust classification

Counted over the ~65 live mappings above, at the granularity stated.
Per the brief, nothing is upgraded for having plausible values.

| Class | Count | What qualifies |
|---|---|---|
| VERIFIED | **1** | `VENUES` `ZU → SW` — hand-checked against the provider, documented with what it does not check. (The filings-path ISIN table + GLEIF cross-check is the second specimen in the repo, outside this path.) |
| VALIDATED | **2** | FX `rate > 0`; balance-history fallback gated on `totalCurrencyIso == "USD"`. |
| DECLARED | **2** | OAuth scope vocabulary; ratelimit headers — the two cases where in-repo provider documentation ([ETORO_API.md](../ETORO_API.md)) states the semantics being relied on. |
| ASSUMED | **~57** | Everything else: every Yahoo fundamental including both `/100` conversions (each justified once, at design time, by a single observed implausibility or one issuer statement — neither checked live), every quote field, every eToro money and identity field, all three vocabulary tables, the ticker pass-through rule, the hardcoded currency. |
| UNKNOWN | **3** | `dividendYield` (measured: two provider schemas share the key at two scales — no interpretation of the merged field can be justified); `instrumentTypeID` read through `assetTypeId`'s table (shared codespace never established); `exchangeId → exchange` (no vocabulary exists on either side). |

The shape of the distribution is the finding: **60 of the ~65
mappings — 92% of the boundary — are ASSUMED or worse, and the two
conversions that exist were each installed reactively, after a
defect, field by field.** The `dividendYield` row is the control
experiment for the whole class — it sat in the ASSUMED mass looking
exactly like its 57 neighbours until measurement moved it to UNKNOWN.
Nothing distinguishes the neighbours except that they have not been
measured yet.

---

## 3. The four translation kinds

The brief asks whether the architecture distinguishes identity,
vocabulary, unit and semantic translation. **It does not — all four
cross the same unguarded assignment boundary**, and the distinctions
that exist are incidental, not architectural: `VENUES` happens to be
an identity table, `_percentage_as_ratio` happens to be a unit rule
for exactly two fields, the `AssetClass`/`Sector`/`PlaybookKind`
tables happen to be vocabulary maps. No shared concept names what
kind of translation any mapping performs, and therefore nothing can
demand the right validation for its kind.

The three seed failures are one failure of each kind, which is why
they looked unrelated:

| Kind | Seed | What validation the kind needs |
|---|---|---|
| **Unit** | `dividendYield` ×100 | a declared expected unit, checked against an invariant or a second reading (both readings exist in the payload — §5) |
| **Semantic** | `forwardPE` undisclosed | either a provider definition, or an honest downgrade of what the fact claims (*reported*, not *established*) |
| **Identity + vocabulary** | `asset_type_id 5` / SPCX | the provider's own declaration (the uncalled taxonomy endpoints) or corroborating evidence (name, second vendor) before a domain category is pronounced |

The fourth kind's live specimens without a seed: identity —
the ticker pass-through that let one vendor's SPCX wear the other
vendor's numbers (§6); vocabulary — `exchangeId` stringified into a
field named `exchange`. A single "provider confidence" score would
collapse exactly these distinctions; the brief forbids it and the
measurements above justify the prohibition.

---

## 4. Yahoo `forwardPE`: exact findings

**Source endpoint.** `ValueProvider.snapshot`
([value_provider.py:41](../../app/providers/value_provider.py)) reads
`yf.Ticker(symbol).info`. In the installed yfinance 1.5.2, `info` is
not one endpoint: `Quote._fetch_info`
(`.venv/…/yfinance/scrapers/quote.py:677`) fetches **quoteSummary**
(modules `financialData`, `quoteType`, `defaultKeyStatistics`,
`assetProfile`, `summaryDetail`) and **`/v7/finance/quote`**
(`_fetch_additional_info`, line 666), then flattens both into one dict.
Keys shared by both sources are silently overwritten by the v7 value.
`forwardPE` is served by both; for the probed listings the two values
agree, so which endpoint answered is currently unobservable downstream
— and nothing checks the agreement.

**Definition.** Undisclosed. Neither endpoint's response carries a
definition, a methodology note, an estimate source, or documentation
pointers; the repository holds no Yahoo field documentation
(measured: the only match for `forwardPE|quoteSummary|summaryDetail`
under `docs/` is `VALUATION_AUTHORITY.md`, this audit's own
predecessor).

**Earnings basis — established by measurement.** For both probed
listings, `forwardPE = regularMarketPrice / epsForward` to six decimal
places (BNP.PA: 112.1 / 13.13126 = 8.536881 vs reported 8.5368805;
NOVO-B.CO: 294.7 / 21.88219 = 13.467573 vs reported 13.467573). So the
denominator is Yahoo's `epsForward` — a consensus estimate whose
aggregation, contributor set, dilution basis and precise horizon are
all undisclosed. `epsCurrentYear` is a separate field with a different
value, which *suggests* `epsForward` is a next-fiscal-year figure; that
is an inference from field naming, not an established fact, and is
labelled as such.

**Forecast horizon.** Not established. See above: next fiscal year by
inference only.

**Update timing — the numerator and denominator live on different
clocks.** `regularMarketPrice` moves intraday; `epsForward` carries no
date at all. The ratio therefore has the *price's* freshness and the
*estimate's* staleness simultaneously, and nothing in the payload says
when the estimate was last revised.

**Treatment of negative earnings.** A negative `epsForward` produces a
negative `forwardPE`. The platform's band
([value_signal_service.py:84](../../app/services/value_signal_service.py))
tests `pe < 18` with no lower bound, so a company expected to lose
money would read CHEAP at confidence 90. Latent — no live security
currently exercises it — and recorded in `VALUATION_AUTHORITY.md`;
re-verified here against the live band.

**Currency/unit assumptions.** The ratio arrives precomputed and
dimensionless, so MOVRvest performs no currency arithmetic on it. Both
probed listings carry consistent `currency`/`financialCurrency`
(EUR/EUR, DKK/DKK); whether Yahoo guarantees price and estimate share a
currency on every listing (GBp-priced London lines are the standing
risk) is **not established** — the platform trusts the provider's
internal consistency without evidence either way.

**Null semantics.** `info.get("forwardPE")` → `None` → the field is
absent → `ValueSignal` UNKNOWN at confidence 20. Honest. But the
yfinance flatten drops keys whose value is JSON null, so *provider
reported null* and *provider omitted the field* are already
indistinguishable before MOVRvest reads anything. A `forwardPE` of
`0.0`, should the provider ever serve one, would read CHEAP@90 — no
sentinel check exists.

**Timestamp semantics.** The `Provenance` on the snapshot is stamped
`datetime.now(UTC)` at fetch
([value_provider.py:42](../../app/providers/value_provider.py)) — it
records *when MOVRvest asked*, not any provider assertion about when
the figure was true. The cache preserves this honestly ("Yahoo
Finance, 3 hours ago"), but what it preserves is request time. For a
ratio whose denominator is an undated estimate, the platform's date is
the only date there is.

**Yahoo reports `forwardPE = X` vs MOVRvest has established forward
P/E = X.** The first is true; the second is not, and the gap is now
measurable: undisclosed definition, undated denominator, unverified
currency consistency, no cross-source corroboration (one provider, one
field, no second reading — the platform's own S1 rule, *agreement
inside one provider is not corroboration*, has never been applied to
this field). In S4.5's vocabulary the field is a **secondary
computation with undisclosed methodology**; the equity path grants it
what amounts to established standing the moment it is assigned.

**Does `ValuationObservation` overstate?** Partially, and the
overstatement is the label rather than the number.
`ValuationObservation.stated` renders "Forward P/E of 17.4×."
([valuation_comparison.py:73](../../app/domain/valuation_comparison.py))
— no relation word, no band word, no benchmark, per #132. But the
label **"Forward P/E"** presents a defined metric where what is held is
*Yahoo's `forwardPE` field, definition undisclosed*. The provenance
(`reading`) carries the source name, so the sentence is defensible as
"the provider's forward P/E"; what it cannot claim is that MOVRvest
knows what "forward" means here. Per the brief, it is **not removed**:
no evidence invariant forces removal, because the number is genuinely
the provider's report and the source travels with it. The finding
stands as the exact measure of what a future boundary must add — the
distinction between *reported* and *established*, carried on the fact
itself.

---

## 5. Yahoo `dividendYield`: root cause and extent

**The root cause is found, at source, and it is none of the simple
candidates.** Not a provider unit change alone, not an adapter typo,
not display formatting. It is the brief's sixth hypothesis:
**multiple provider schemas sharing one field name** — compounded by an
adapter (yfinance) that merges them silently and an error path that
makes the winner nondeterministic.

Measured mechanism, in the installed yfinance 1.5.2
(`scrapers/quote.py`):

1. `_fetch_info` (line 677) fetches quoteSummary; `summaryDetail`
   carries `dividendYield` as a **fraction** — measured live for
   BNP.PA: `0.0517`.
2. `_fetch_additional_info` (line 666) fetches `/v7/finance/quote`;
   its quote object carries `dividendYield` in **percent points** —
   measured live, same call, same listing: `5.17`.
3. Both are flattened into one dict, quoteSummary's leaves first, v7's
   keys after — so on collision **the v7 value wins**.
4. `_fetch_additional_info` catches `HTTPError` and returns `None` —
   so when the v7 side call fails (rate limit, outage), the
   quoteSummary **fraction** survives instead. **A transient HTTP
   failure flips the unit of the stored fact.**

The full collision surface was measured: **31 keys are served by both
endpoints for BNP.PA, and exactly one of them — `dividendYield` —
differs in value.** `forwardPE`, `trailingPE`, `marketCap` and the
other 27 currently agree, which is why only the yield has misbehaved;
the *mechanism* covers all 31 and checks none of them. Beside it in
the same v7 payload, `trailingAnnualDividendYield` remains a fraction
(`0.0516…`) — the provider's scale convention is not even uniform
within one endpoint; it is per-field.

This explains the stored corpus exactly. Same-day readings disagree
because the split is **per-call v7 availability**, not per-listing
convention: NOVO-B.CO stored `0.0521` (a day its v7 call failed;
measured today, its v7 answers `3.97`), BNP.PA stored `8.85` (a day
its v7 call succeeded). The adapter
([value_provider.py:71](../../app/providers/value_provider.py))
passes whichever value won through raw — the one percent-shaped field
in `from_info` given no `_percentage_as_ratio`, while `debtToEquity`
and `netExpenseRatio` beside it are converted. The cache
([cached_value_provider.py:145](../../app/providers/cached_value_provider.py))
faithfully preserves whatever scale was written.

**Corpus extent — measured over all 77 stored fundamentals records.**
35 records hold a dividend yield: **33 percent-scale, 1
fraction-scale, 1 zero.** The fraction is NOVO-B.CO (`0.0521`); the
zero is IB01.L (the accumulating share class F1 already handles). The
decisive record pair: **NOVO-B.CO (fraction) and SOLB.BR (percent,
9.07) were acquired in the same second** — `observed_at`
2026-08-09T16:13:36 both — so the scale flips *within one acquisition
run, per symbol call*. Exchange does not correlate (`.CO` holds both
scales: NOVO-B.CO fraction, VWS.CO percent); run date does not
correlate. Per-call v7 availability is the only explanation that fits
the corpus, and it is the one the vendored source predicts.

Two residuals the mechanism does not explain, reported rather than
absorbed: NVDA's stored `0.45` is implausible under *either* scale
(the true yield is roughly 0.02%), so at least one value is wrong a
third way; and the store can never distinguish these cases after the
fact — records keep no history (one file per symbol, last-write-wins),
no per-field provenance, and `observed_at` equals `stored_at` to the
millisecond in all 77 records. **A scale defect, once written, is
undatable and unattributable from the record alone.**

**Downstream effect — measured, and narrower than the defect
deserves.** An exhaustive sweep of `dividend_yield` across the
repository (app, apps/web, all extensions) finds exactly one
analytical reader: the quality signal's sign test,
`company.dividend_yield > 0`
([quality_signal_service.py:96–100](../../app/services/quality_signal_service.py)).
A sign test is scale-invariant, so the ×100 error moves **no gate, no
score, no decision** today. No surface — backend, CLI, API or frontend
— renders the number; the "885%" of #131 was this audit's predecessor
reading the stored 8.85 under the domain's declared decimal-ratio
convention (`valuation_snapshot.py` documents company fundamentals as
decimal ratios). The defect is therefore **latent**: the corpus holds
two units under one field whose declared convention is one of them,
and it fires the day any consumer reads magnitude — a yield band, a
payout display, an income-portfolio rule. The near-miss is
`dividend-signals@1`: provider HIGH quality requires a payout, and the
payout bit is the sign test above.

**What Yahoo actually publishes, for the eventual repair to weigh
(not built here):** `trailingAnnualDividendYield` — a realized yield,
fraction-scaled in both endpoints, alongside `dividendRate` and
`trailingAnnualDividendRate` in currency units. An established-unit
sibling exists; the platform reads the ambiguous field.

---

## 6. eToro `asset_type_id`: SPCX and the identity boundary

**Root cause, in one sentence: the platform assumed a vocabulary the
provider declares on request — and it turns out the deeper failure is
identity, not vocabulary.** eToro's own catalog documents a
`/api/v1/market-data/instrument-types` endpoint
([ETORO_API.md:89](../ETORO_API.md)) — the broker's authoritative
statement of what each type id means — and two more vocabulary
endpoints beside it (`/exchanges`, `/stocks-industries`). **Nothing in
`app/` calls any of the three** (measured: zero references). The
vocabulary MOVRvest applies instead is a four-row hardcoded table
inferred from observed instances.

**The mapping itself, and its honest parts.**
`AssetClass.from_etoro` ([asset_class.py:26–33](../../app/domain/asset_class.py))
reads `_ETORO_ASSET_TYPES` — `2 → COMMODITY`, `5 → STOCK`, `6 → ETF`,
`10 → CRYPTO` (lines 86–89) — and an unmapped id is **UNKNOWN, never a
guess**, with `UNKNOWN` deliberately excluded from `has_no_company`
(an unclassified thing is not asserted to have no business). The
absence discipline is right at the enum and inverts one hop later:
`company_facts_service.py:105` computes `has_company = not
asset_class.has_no_company`, so an instrument whose type id the
platform has never seen is **treated as a company and given the full
company reading** — the honest UNKNOWN becomes a positive claim at
the first consumer. What is missing is any validation of the
*presence* case, and any consumer treating UNKNOWN as unknown. `has_no_company` is a property of the enum
(asset_class.py:49–71), so the single integer in one watchlist field
decides, alone and unchecked, whether an instrument receives the
entire company question set — the blast radius is every
`has_no_company` consumer: `artificial_cio.py:276,304`,
`decision_evidence_builder.py:999`, `investment_committee.py:83,123`,
`quality_signal_service.py:61`, `value_signal_service.py:27`,
`executive_writer_service.py:141`, `score_basis.py:129`,
`playbook_coverage_service.py:271`, `company_facts_service.py:105`,
plus the dossier definition and the fund-cost field.

**What the payload could establish, and what is discarded.** No
reachable eToro field carries an ISIN, and none is a dedicated fund
flag. The fields that do carry independent signal are read-and-ignored
or discarded outright: `assetTypeSubCategoryId` is parsed into
`WatchlistItem` and **consumed by nothing** (it distinguishes HYPE at
1010 from every other crypto at 1001); the instrument catalog's
`stocksIndustryID` (a second broker-declared classification with its
own uncalled vocabulary endpoint), `distributionType` and `priceSource`
(a textual venue name — "Euronext", "NASDAQ") are all discarded;
`exchangeId` reaches `CompanyFacts` as the stringified integer `"4"`
with no exchange vocabulary anywhere in `app/`
([company_facts_service.py:125](../../app/services/company_facts_service.py)).
The display name does carry identity evidence — "iShares $ Treasury
Bond 0-1yr **UCITS ETF**" (type 6), "AstraZeneca PLC **ADR**" and
"Sea Ltd-**ADR**" (type 5) — and nothing reads it.

**The SPCX re-examination — the audit corrects its own premise.** The
brief, following #131, described SPCX as "an ETF classed stock." The
measured record does not establish that. eToro's own entry for
instrument 15618 reads `displayName: "Space Exploration Technologies
Corp"` — the broker asserts this is **SpaceX's corporate stock**, not
the Tuttle "SPAC and New Issue ETF" the ticker SPCX has historically
denoted at Yahoo. And every Yahoo-sourced cache for the ticker is
company-shaped: market cap $1.75T, forward P/E 71.84, an earnings
date, beta 3.68 — while the one instrument eToro *does* call an ETF
(IB01.L, type 6) caches fund-shaped: null P/E, null market cap, an
expense ratio. So either both vendors now denote a listed SpaceX and
the classification was **right** — or the two vendors' SPCX are two
different securities and MOVRvest has been attaching one vendor's
numbers to the other vendor's instrument. **The platform cannot
currently tell which**, and that inability is the finding: identity
between the broker's instrument and the data vendor's ticker is never
established — `YahooInstrument.for_security`
([yahoo_market_provider.py:45–71](../../app/providers/yahoo_market_provider.py))
passes the eToro ticker through untranslated, stamps the quote with
*eToro's* display name, and a ticker collision is unobservable from
the output. This is Invariant 2 exactly — the invariant the platform
learned from `BTC` resolving to a bitcoin trust at the SEC and from an
ISIN lookup returning a CEDEAR — operating live on the equity quote
path with no identity gate. SPCX never even passed through the
instrument catalog: its identity rests solely on the watchlist read.

**The corpus, audited for the same class** (75 unique instruments:
65 × type 5, 2 × type 2, 1 × type 6, 8 × type 10 — plus three
catalog-only ids, all type 5): no instrument named ETF/UCITS/Fund/ETN/
ETC is classed 5, so no *second* fund-question defect exists in this
corpus. What does exist, all type 5, all receiving the plain-company
treatment their names already qualify: **SE and AZN are ADRs by their
own display names**; DIDIY is an OTC ADR (exchangeId 19, unique in the
corpus, distinguishable only by a vocabulary the platform never
fetched); **EPD is a master limited partnership** — "Enterprise
Products Partners **LP**" — whose units are not common stock; MBGL
carries a "-W" marker. Each is a vocabulary distinction the provider
publishes (in a name, a subcategory, an industry id, or a taxonomy
endpoint) and the platform flattens into `STOCK`.

**Why this is the F1 defect re-entering through the input.** The Fund
Analytical Boundary (F1) keys every company-question consumer on
`AssetClass.has_no_company`, so the *membership* fix was complete —
for any instrument whose asset class is right. SPCX shows the same
wrong meaning arriving one layer earlier: the boundary is sound, the
classification feeding it is unvalidated. A fund classed `stock`
receives the whole company question set — P/E banding, company
quality, the dividend wall, the SELL veto — every one of them F1
already refuses *when it can see the fund*.

---

## 7. Sibling defects

The three seeds were used as probes; each sibling below is a live code
path, cited, with its measured (or latent) effect. Speculative
cleanups are excluded.

**Unit / scale**

- **`MarketQuote.currency` hardcoded `"USD"`**
  ([yahoo_market_provider.py:258](../../app/providers/yahoo_market_provider.py))
  — measured over the stored corpus: **all 78 valued quote records
  carry the literal string "USD"**, including at least 15 European
  listings whose prices are visibly local-currency (AIR.PA 213.60 EUR,
  NOVO-B.CO 305.10 DKK, NESN.SW 81.21 CHF, …). The GBp hazard is
  **live, not hypothetical: BP.L is stored as 517.2 "USD" — pence**,
  a ~100× error the moment anything converts by the label (IB01.L at
  121.4 is safe only by the coincidence that that LSE line trades in
  dollars). Standing open defect (`movrvest-provider-data-hygiene`),
  same class: an ASSUMED constant presented as a fact. The v7 payload
  carries a real `currency` field the platform discards — measured
  present and correct (EUR/DKK) on both probed listings.
- **`^TNX` "price" is not a price** — the CBOE convention is yield×10
  (42.5 = 4.25%). It enters `MarketQuote.price` through the same
  pipeline as SPY's dollars
  ([yahoo_market_provider.py:128–131](../../app/providers/yahoo_market_provider.py)),
  labelled USD by the constant above. Two semantic translations deep on
  one field, both silent.

**Null / sentinel as zero**

- **`change_percent` manufactured as `0.0`** in two places: a history
  of fewer than two closes
  ([yahoo_market_provider.py:248](../../app/providers/yahoo_market_provider.py))
  and a cache restore of a non-numeric value
  ([cached_market_provider.py:226](../../app/providers/cached_market_provider.py)).
  This one is **decision-bearing**: `daily_change_pct` is the momentum
  signal's whole input
  ([company_facts_service.py:142](../../app/services/company_facts_service.py),
  [momentum_signal_service.py:17](../../app/services/momentum_signal_service.py)),
  and a manufactured 0.0 reads NEUTRAL at confidence 60 with the
  rendered sentence "*moved +0.00% today*", where an honest absence
  reads UNKNOWN at confidence 20. **One live occurrence in the stored
  corpus**: ARB-USD holds `change_percent: 0.0` on a record whose
  price is 0.0006 and whose fundamentals market cap is 0 — a broken
  provider read whose fingerprint is a manufactured neutral. (The
  seven honestly-unavailable records — COCOA.FUT, `^VIX`, NESN.ZU and
  friends — carry `null` with `unavailable: true`, which is the
  correct shape sitting one field away from the wrong one.) The
  domain type participates in the defect: `MarketQuote.change_percent`
  is `float`, not `float | None` — the shape has no way to say
  *unmeasured*, so the adapter must invent a number. Invariant 1,
  structurally enforced against.

**Trailing / forward confusion**

- **`eps = info.get("trailingEps", info.get("forwardEps"))`**
  ([value_provider.py:73](../../app/providers/value_provider.py)).
  A silent semantic fallback: when the provider omits `trailingEps`,
  a *forecast* enters the field with nothing recording which was read.
  The consumer is a sign test
  ([quality_signal_service.py:90–94](../../app/services/quality_signal_service.py)),
  so the conflation is decision-visible **exactly when trailing and
  forward EPS differ in sign — the turnaround case**, where "Positive
  earnings." would be asserted about a company that has none yet, on
  an estimate. The cached record carries no marker of which key was
  read (schema: one `eps` field), so the corpus cannot be
  retro-classified.
- **`volume_24h = info.get("volume24Hr", info.get("regularMarketVolume"))`**
  ([value_provider.py:76](../../app/providers/value_provider.py)) —
  a crypto field falling back to an equity field under one name. For
  equities the first key never exists, so the fallback always fires;
  the field is then dropped for companies at the facts boundary
  ([company_facts_service.py:180](../../app/services/company_facts_service.py)).
  Harmless today by two accidents, declared by nothing.

**Timestamps discarded / stale as current**

- **The last close's own date is discarded.** `yf.download` returns
  date-indexed closes; the quote takes `closes.iloc[-1]` and stamps
  `datetime.now(UTC)`
  ([yahoo_market_provider.py:239–268](../../app/providers/yahoo_market_provider.py)).
  A Friday close read on Sunday is a quote observed Sunday, and the
  momentum sentence built from it says the security "moved X% today."
  The cache preserves request time truthfully; the request time was
  never the price's time.
- **`epsForward` is undated** (see §4) — the forward P/E's
  denominator has no vintage anywhere in the chain.

**Provider estimates presented as established facts**

- `forwardPE` (§4) is the type specimen: a consensus estimate ratio,
  banded at confidence 90 under `pe-bands@1` the moment it arrives.

**Identity / vocabulary**

- `asset_type_id → AssetClass` (§6) is the type specimen. The same
  mapper's sibling risks are inventoried in §1's table and §6's corpus
  sweep.
- The **`VENUES` table**
  ([yahoo_market_provider.py:36](../../app/providers/yahoo_market_provider.py))
  is recorded here as the *counter-example*: one entry (`ZU → SW`),
  added only after hand-verification against the provider, documented
  with what it does not check. This is what a validated vocabulary
  translation looks like on the equity path — it exists, once.

**Found by the corpus sweep, not the probes**

- **A quote can be filed under one symbol and carry another.** The
  stored `NESN.SW` quote record contains `symbol: "NESN.ZU"` while a
  separate `NESN.ZU` record sits beside it marked unavailable — the
  `VENUES` translation's two names for one listing leaking into the
  store as two records, one of them self-contradicting. Harmless
  today; an identity wrinkle of exactly the class Invariant 2 exists
  for.
- **SPCX's stored market cap is 1.754 trillion dollars** — plausible
  if Yahoo's SPCX is a listed SpaceX, absurd if it is the small ETF
  the ticker historically denoted, and the platform holds no evidence
  deciding which (§6). Stored without any plausibility check, it
  clears the $10bn large-cap line and earns the quality point — a
  figure whose *identity* is unresolved is participating in a score.
- **The store cannot answer "when did this go wrong."** One record
  per symbol, overwritten in place; no per-field provenance;
  `observed_at` ≡ `stored_at` in 77 of 77 records. Any future unit or
  identity audit starts from the same blindness this one did.

**Found by the inventory sweep**

- **`CompanyFacts.currency` is never assigned** — no call site passes
  it, so even the hardcoded "USD" is dropped rather than propagated,
  and every monetary figure on the decision path is currency-less
  while the field to carry one sits empty
  ([company_facts.py:48](../../app/domain/company_facts.py)).
- **A second, duplicated quote-restore implementation** —
  `market_snapshot_archive.py:264–293` re-implements the
  `MarketQuote` restore with the same hardcoded defaults
  (`change_percent` 0.0, `currency` "USD") copied in. One translation,
  two owners; a fix to one will not reach the other.
- **Schema-1 fundamentals records predate the `/100` conversions and
  come forward unconverted** — the cache's migration is the identity
  function ([cached_value_provider.py:62](../../app/providers/cached_value_provider.py)),
  so a `debt_to_equity` or `expense_ratio` written before its
  conversion existed restores at the old scale under the new
  convention. The schema contract versions the record's *shape*;
  nothing versions a field's *unit*.
- **A failed VIX fetch is cached and served as a measurement** for
  the TTL, with no provenance object at all — the VIX is the one
  undated bare float on the market panel (display/narrative only;
  it never reaches `decide()`).
- **Every eToro monetary field defaults a malformed value to 0.0**
  (`_number`, [etoro_account.py:75–80](../../app/brokers/etoro_account.py))
  — on the account path, a broken payload value and a real zero are
  the same number everywhere except `credit`.

---

## 8. Which affected fields reach decisions

The chain, once: `ValuationSnapshot` → `CompanyFacts`
(`company_facts_service.build`) → four signal services + the analyst
research → `CompanyRecommendation` → `DecisionEvidence` →
`ArtificialCIO.decide()`. Every consumer below was traced to that
chain or to its absence.

**Gated — a provider field that moves a named rule directly:**

- **`forward_pe`** → `pe-bands@1` (18/28, no lower bound) →
  `valuation-scores@1` (80/55/25) → the FAIR wall at
  `artificial_cio.py:216–223` and the heaviest committee vote term
  (×0.40). A ÷100 scale error makes everything CHEAP; a ×100 makes
  everything EXPENSIVE and −0.40 on the vote.
- **`market_cap`** → the large-cap point in `provider-quality@1`
  ([quality_signal_service.py:84–88](../../app/services/quality_signal_service.py),
  the $10bn line) → quality 80/62/40 → three CIO gates. **No sanity
  or currency check exists on the field** — SPCX's suspect $1.75T
  clears the line and earns the point; a currency-unit error flips
  small-cap→large-cap, which at the margin is the difference between
  clearing the 75 recommendation gate and parking at PREPARE.
- **`eps`, `dividend_yield`** → sign tests in the same quality rule.
  Scale-invariant; the eps trailing-vs-forward substitution is the
  live semantic risk (a loss-maker with a positive forecast earns
  "Positive earnings.").
- **`daily_change_pct`** → `momentum-bands@1` (±0.5/±2.0). The
  manufactured 0.0 (§7) reads NEUTRAL@60 vs honest UNKNOWN@20 — the
  vote is 0 either way, but the *confidence* difference enters
  `evidence_score` (`decision_evidence_builder.py:364`), which three
  CIO gates read.
- **`realized_volatility`, `max_drawdown`** → `risk-bands@1`
  (0.20/0.35/0.60; 0.20/0.40) → `risk-severity@1` → risk score →
  REJECT above 70. **A ratio-vs-percent confusion here is the single
  most destructive unit error available on the platform: any
  volatility reading ≥ 0.60 after a ×100 error makes every security
  SEVERE and every case REJECT.** The field is guarded by nothing but
  the convention in a docstring.

**Findings-only — fundamentals that shape research but hit no gate:**
`revenue_growth`, `earnings_growth`, the three margins,
`debt_to_equity`, `current_ratio` and the two cash flows reach
`decide()` only as RESEARCH findings with a sense
(`decision_evidence_builder.py:966–972`, 75/40). Two audit-relevant
facts here. First, **their threshold tables are ungoverned**: the
analyst ladders (`growth_analyst.py:92–114`,
`profitability_analyst.py:110–147`, `balance_sheet_analyst.py:95–121`,
`cash_flow_analyst.py:127–137`) sit in no `DecisionRule`, are absent
from `GOVERNED_MODULES` in the provenance test, and every one
compares a decimal ratio to a bare literal — the exact ×100-fragile
shape the provenance regime was built to pin, and the same tables are
reused by the filing route, so one scale error would corrupt both
routes at once. Second, `debt_to_equity`'s `/100` at
[value_provider.py:95](../../app/providers/value_provider.py) is **the
only unit conversion on the platform protecting a scored threshold** —
remove it and every company reads ≥ 2.00×, WEAK, adverse.

**Vocabulary that selects the analysts:** `sector`/`industry` decide
the `PlaybookKind` (26 substrings + 3 sector fallbacks,
[playbook_selector.py:31–65](../../app/services/playbook_selector.py)),
which decides **which analysts run at all** (a bank drops cash flow, a
REIT drops profitability) and whether filing knowledge is read
(`company_research_service.py:132–133`). A substring mismatch
silently downgrades to GENERAL_CORPORATE — no error, no signal. A
provider string is choosing the platform's own reasoning shape.

**Written and never read:** `trailing_pe`, `peg_ratio`, `volume_24h`,
`roe`, `roic` (hardcoded None), `current_price` on `CompanyFacts` —
write-only fields. The corroboration gate protecting `volume_24h` on
the token path guards a value nothing consumes; `market_sensitivity`
is deliberately non-scoring (a neutral finding); the VIX never
reaches `decide()` (`app/committee/` does not reach it, and
`MarketAnalyst` never reads the VIX).

**The asset class is the meta-field — it decides which of the above
runs.** All `has_no_company` consumers were enumerated in §6. The
decision-shaped consequence is an inversion worth stating on its own:
for a **correctly-classed** ETF or crypto asset, value and quality
both read UNKNOWN, their vote terms are 0, the maximum negative vote
is −0.25, and the SELL veto (threshold −0.50) is **mathematically
unreachable**. For a fund misclassed STOCK, the fund's P/E reads
EXPENSIVE (−0.40) and its size/earnings/dividend read as a weak
company (−0.35): −0.75, veto, REJECT ahead of every score. **The
misclassification is not merely mislabeling — it is what arms the
most powerful bit in the decision system** (`veto-sell@1`, 13/14 in
the philosophy audit). The full SPCX chain was traced through
eighteen wrong treatments, from `has_company=True` at
`company_facts_service.py:105` through the earnings calendar fetched
for a fund, the four `_FUNDAMENTALS` analysts asked about margins a
fund does not have, filing knowledge read for a fund
(`company_research_service.py:132`), the dropped expense ratio (the
one genuine fund fact, set to None at `:199–200` because the class
reads STOCK), to the veto at `artificial_cio.py:113–117`. The risk
path alone is class-blind and correct throughout.

---

## 9. The boundary responsible

**There is no boundary.** On the equity/broker path, a provider field
becomes a domain fact in a single assignment expression inside an
adapter — `from_info` for fundamentals, `_fetch_quote` for quotes, the
watchlist parser for identity — with unit conversions applied
field-by-field where a past defect taught one, and nothing else: no
identity validation, no semantic declaration, no cross-source check,
no record on the fact of what was and was not established. The three
seed failures are the three translation kinds crossing that
non-boundary: a **unit** (dividendYield), a **semantic label**
(forwardPE), an **identity/vocabulary** (asset_type_id). One
architectural defect, three surfaces. The sign tests that make two of
them decision-invisible today are accidents of consumption, not
protections — §8 names the consumers that would inhale each error the
day they read magnitude.

The platform has already designed, built, measured and shipped the
missing architecture — on the other path. The crypto fact pipeline
(#99, `token_fact_validation.py`) runs claim → identity validation →
semantic validation → internal consistency → cross-claim comparison →
standing, deterministically, with rejections retained and rendered;
S4.5 adds *where a fact came from* as an axis (`EvidenceAuthority`);
S4.6 adds *what a number claims to measure* (`SupplyMethodology`,
where an undisclosed methodology is not a different methodology). Each
element exists because a measured equity-path-style failure forced it
(ARB's frozen float, Yahoo's $8,105 HYPE price, ADA's three
"conflicting" supplies that were three different facts). The
equity/broker path predates all of it and received none of it. That is
the audit's answer to "three defects or one": **one — the absence of
the boundary the platform already knows how to build.**

---

## 10. The smallest boundary that prevents the class

Four architectures were compared against the measured defects — not
against elegance.

**A. Adapter validation** — each adapter proves its own translation.
Rejected as the *whole* answer by measurement: the adapters are where
every defect lives, and the pattern already failed incrementally —
`_percentage_as_ratio` exists and `dividendYield` didn't get it;
the fix-per-field cadence is how the platform got here. Adapter checks
are necessary (only the adapter sees both raw endpoints) but a rule
that lives only in adapters leaves no record on the fact and nothing
for a consumer to refuse.

**B. Typed provider claims + promotion layer** — adapters emit
provider-native claims; a separate deterministic layer promotes them
to domain facts. This is #99, proven live on crypto. It prevents all
three seeds: the dividendYield claim would fail semantic validation
(two readings of one field under two units — the exact ADA shape);
forwardPE would carry claim standing, never established; asset_type_id
would be an identity claim requiring corroboration (name, ISIN, the
taxonomy endpoint) before an AssetClass is pronounced. Its cost is
real: the equity path's consumers read `CompanyFacts` directly, and a
full claims pool for ~20 fundamentals fields is a second trust
architecture's worth of machinery on a path the owner has frozen
against new layers.

**C. Provenance-qualified facts** — values flow as today, carrying a
semantic status naming what is and is not established. Prevents
nothing by itself (the wrong unit still arrives; SPCX still reads
`stock`), but it is the *reporting* half the platform's principles
already demand: Invariant 10's "say that the interpretation is not
established" applied to provider semantics, and `FactOrigin`
(ESTABLISHED/ASSESSED) already walks this road on the dossier.

**D. Different boundaries per translation kind** — the audit's own
classification (§3) shows the four kinds fail differently and are
checked differently: an identity needs corroborating evidence, a unit
needs an invariant or a reference range, a vocabulary needs the
provider's own declaration, a semantic label needs either a definition
or an honest downgrade of what the fact claims. One generic "provider
confidence" score would erase exactly the distinctions the defects
exploit.

**Recommendation — not implemented.** The smallest boundary preventing
the *class* is **D with B's spine, scoped to where the defects are**:

1. **Every translation names its kind and its warrant.** A small,
   declarative per-field contract at the adapter boundary — field,
   kind (identity / vocabulary / unit / semantic), expected unit or
   vocabulary, and the warrant class (VERIFIED / VALIDATED / DECLARED
   / ASSUMED) — replacing the current implicit table scattered through
   `from_info`. The contract is data, so the audit's inventory (§1)
   stops rotting: it becomes the code.
2. **A unit translation is checked, not assumed** — against a domain
   invariant where one exists (a yield is a fraction; the two-endpoint
   diff in §5 shows the check is *possible* at the adapter, where both
   readings are visible), and a value failing its declared unit is a
   **rejected reading retained with its reason** (#99's vocabulary),
   never a stored fact.
3. **An identity or vocabulary translation requires the provider's own
   declaration or a second source** — for eToro, reading the
   instrument-types endpoint the provider already offers; a mapping
   entry with neither is ASSUMED and says so on the fact.
4. **A semantic label the provider does not define cannot claim the
   domain concept** — the fact carries *provider-reported* standing
   (C's qualifier, S4.5's axis), and surfaces already built to render
   worded absences render the qualification.

This is one boundary asked four questions, not four architectures: the
promotion rule differs by kind (D), the shape it flows through is a
claim with a standing (B), the standing travels on the fact (C), and
the adapter is where the check runs because only it sees the raw
payload (A's kernel). What makes it smallest: it touches only the
translation surface the inventory enumerates, adds no new consumer
contract, and changes no decision — every current value that would
fail a check is already either sign-read or unread, so the boundary
can land as *reporting first*, behaviour-identical, exactly as
`FactOrigin` and the #132 comparison boundary did.

**Explicitly out of scope, per the brief:** no valuation benchmark, no
market-implied expectations, no CHEAP/FAIR/EXPENSIVE evidence claims,
no change to `pe-bands@1`'s banding, scoring or gating, no decision
input altered. #132's boundary is preserved untouched.

---

## Appendix: measurements not repeated above

- yfinance `info` drops every key whose value is JSON null during
  flattening (`quote.py`, `_fetch_info`) — *provider said null* and
  *provider omitted* are indistinguishable to every adapter downstream.
- The `.get(A, .get(B))` fallback idiom evaluates B **eagerly** and
  falls back only on a *missing key*, never on a null value — with the
  flatten above, the two conditions coincide today; a provider change
  serving explicit nulls would not be noticed.
- `UNREAD` ([cached_value_provider.py:18](../../app/providers/cached_value_provider.py))
  is the honest absent-snapshot; the refusal-cached-as-reading defect
  it guards against was measured and fixed previously
  (`carries_nothing`). The provider layer *has* learned absence
  discipline — for presence/absence. Unit and meaning discipline are
  what this audit finds missing.
