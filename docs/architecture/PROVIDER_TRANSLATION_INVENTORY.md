# The governed provider translation inventory

**Generated from `app/domain/provider_translations.py` by**
**`movrvest translations --markdown`. Do not edit by hand —**
**`tests/test_provider_translation_inventory.py` will fail.**

Every crossing from an external provider's field to a MOVRvest
domain concept, with the four questions it answers and the
authority it is performed under. A warrant is authority for a
translation, never confidence in a value: a plausible number can
stand at ASSUMED, and a reputable provider can supply an UNKNOWN
semantic interpretation.

## Census

| Warrant | Count | Means |
|---|---|---|
| Verified | 1 | checked against the provider or an independent source, and recorded with what was checked |
| Assumed | 34 | the interpretation exists only in this platform's adapter code |
| Unknown | 4 | provenance is insufficient to say why this mapping would be valid |

Total governed crossings: **39**.

## The four questions

| Kind | Question | Crossings |
|---|---|---|
| Identity | What economic instrument does this record describe? | 2 |
| Vocabulary | What does the provider's category or token mean? | 6 |
| Unit | What representation is the value expressed in? | 5 |
| Semantic | What concept does this field actually measure? | 29 |

A crossing may answer more than one — `^TNX` needs a semantic and
a unit translation on the same field — so these do not sum to the
total.

## Every governed crossing

| Provider | Field | Endpoint | Domain concept | Kinds | Warrant | Reaches |
|---|---|---|---|---|---|---|
| Yahoo Finance | `Close (CHFUSD=X)` | yf.download | ExchangeRate CHF→USD (translation input) | Semantic | Assumed | gates a decision |
| Yahoo Finance | `Close (DKKUSD=X)` | yf.download | ExchangeRate DKK→USD (translation input) | Semantic | Assumed | gates a decision |
| Yahoo Finance | `Close (EURUSD=X)` | yf.download | ExchangeRate EUR→USD (translation input) | Semantic | Assumed | gates a decision |
| Yahoo Finance | `Close (GBPUSD=X)` | yf.download | ExchangeRate GBP→USD (translation input) | Semantic | Assumed | gates a decision |
| Yahoo Finance | `currency` | Ticker.info (merged) | MarketCapDenomination (corroboration input) | Vocabulary | Assumed | gates a decision |
| Yahoo Finance | `regularMarketPrice` | Ticker.info (merged) | MarketCapDenomination (corroboration input) | Semantic | Assumed | gates a decision |
| Yahoo Finance | `sharesOutstanding` | Ticker.info (merged) | MarketCapDenomination (corroboration input) | Semantic | Assumed | gates a decision |
| Yahoo Finance | `Close (pair)` | yf.download | MarketQuote.change_percent | Unit, Semantic | Assumed | gates a decision |
| Yahoo Finance | `dividendYield` | Ticker.info (merged) | ValuationSnapshot.dividend_yield | Unit, Semantic | Unknown | gates a decision |
| Yahoo Finance | `trailingEps` | Ticker.info (merged) | ValuationSnapshot.eps | Semantic | Assumed | gates a decision |
| Yahoo Finance | `forwardEps` | Ticker.info (merged) | ValuationSnapshot.eps (substituted) | Semantic | Unknown | gates a decision |
| Yahoo Finance | `forwardPE` | Ticker.info (merged) | ValuationSnapshot.forward_pe | Semantic | Assumed | gates a decision |
| Yahoo Finance | `marketCap` | Ticker.info (merged) | ValuationSnapshot.market_cap | Semantic | Assumed | gates a decision |
| Yahoo Finance | `<symbol>` | Ticker.info (merged) | YahooInstrument.yahoo_symbol | Identity | Assumed | gates a decision |
| Yahoo Finance | `<venue suffix>` | Ticker.info (merged) | YahooInstrument.yahoo_symbol (venue) | Identity | Verified | gates a decision |
| eToro | `assetTypeId` | /api/v1/watchlists | AssetClass | Vocabulary | Assumed | selects which analysis runs |
| eToro | `instrumentTypeID` | /api/v1/market-data/instruments | AssetClass | Vocabulary | Unknown | selects which analysis runs |
| Yahoo Finance | `industry` | Ticker.info (merged) | ValuationSnapshot.industry | Vocabulary | Assumed | selects which analysis runs |
| Yahoo Finance | `sector` | Ticker.info (merged) | ValuationSnapshot.sector | Vocabulary | Assumed | selects which analysis runs |
| Yahoo Finance | `currentRatio` | Ticker.info (merged) | ValuationSnapshot.current_ratio | Semantic | Assumed | shapes research findings |
| Yahoo Finance | `debtToEquity` | Ticker.info (merged) | ValuationSnapshot.debt_to_equity | Unit | Assumed | shapes research findings |
| Yahoo Finance | `earningsGrowth` | Ticker.info (merged) | ValuationSnapshot.earnings_growth | Semantic | Assumed | shapes research findings |
| Yahoo Finance | `freeCashflow` | Ticker.info (merged) | ValuationSnapshot.free_cash_flow | Semantic | Assumed | shapes research findings |
| Yahoo Finance | `grossMargins` | Ticker.info (merged) | ValuationSnapshot.gross_margin | Semantic | Assumed | shapes research findings |
| Yahoo Finance | `profitMargins` | Ticker.info (merged) | ValuationSnapshot.net_margin | Semantic | Assumed | shapes research findings |
| Yahoo Finance | `operatingCashflow` | Ticker.info (merged) | ValuationSnapshot.operating_cash_flow | Semantic | Assumed | shapes research findings |
| Yahoo Finance | `operatingMargins` | Ticker.info (merged) | ValuationSnapshot.operating_margin | Semantic | Assumed | shapes research findings |
| Yahoo Finance | `revenueGrowth` | Ticker.info (merged) | ValuationSnapshot.revenue_growth | Semantic | Assumed | shapes research findings |
| Yahoo Finance | `<none — hardcoded>` | yf.download | MarketQuote.currency | Vocabulary | Assumed | display only |
| Yahoo Finance | `Close` | yf.download | MarketQuote.price | Semantic | Assumed | display only |
| Yahoo Finance | `Close (^TNX)` | yf.download | MarketQuote.price (^TNX) | Semantic, Unit | Unknown | display only |
| Yahoo Finance | `netExpenseRatio` | Ticker.info (merged) | ValuationSnapshot.expense_ratio | Unit | Assumed | display only |
| Yahoo Finance | `circulatingSupply` | Ticker.info (merged) | ValuationSnapshot.circulating_supply | Semantic | Assumed | consumed by nothing |
| Yahoo Finance | `startDate` | Ticker.info (merged) | ValuationSnapshot.inception | Semantic | Assumed | consumed by nothing |
| Yahoo Finance | `maxSupply` | Ticker.info (merged) | ValuationSnapshot.max_supply | Semantic | Assumed | consumed by nothing |
| Yahoo Finance | `pegRatio` | Ticker.info (merged) | ValuationSnapshot.peg_ratio | Semantic | Assumed | consumed by nothing |
| Yahoo Finance | `returnOnEquity` | Ticker.info (merged) | ValuationSnapshot.return_on_equity | Semantic | Assumed | consumed by nothing |
| Yahoo Finance | `trailingPE` | Ticker.info (merged) | ValuationSnapshot.trailing_pe | Semantic | Assumed | consumed by nothing |
| Yahoo Finance | `volume24Hr` | Ticker.info (merged) | ValuationSnapshot.volume_24h | Semantic | Assumed | consumed by nothing |

## Awaiting a warrant, ranked by reach

What a later slice should repair first. Ranked by how far a
crossing reaches — a measured fact — and never by warrant, which
is not a quantity.

1. **ExchangeRate CHF→USD (translation input)** — Yahoo Finance `Close (CHFUSD=X)`, assumed, gates a decision.
2. **ExchangeRate DKK→USD (translation input)** — Yahoo Finance `Close (DKKUSD=X)`, assumed, gates a decision.
3. **ExchangeRate EUR→USD (translation input)** — Yahoo Finance `Close (EURUSD=X)`, assumed, gates a decision.
   the same field the portfolio display reads inverted once for its USD→EUR direction; this path reads it direct, and each seam writes its own direction down exactly once.
4. **ExchangeRate GBP→USD (translation input)** — Yahoo Finance `Close (GBPUSD=X)`, assumed, gates a decision.
   the pound's rate, for a cap established GBP by the minor-unit identity — the translation multiplies the POUNDS figure, never the pence quote and never the statement dollars.
5. **MarketCapDenomination (corroboration input)** — Yahoo Finance `currency`, assumed, gates a decision.
6. **MarketCapDenomination (corroboration input)** — Yahoo Finance `regularMarketPrice`, assumed, gates a decision.
7. **MarketCapDenomination (corroboration input)** — Yahoo Finance `sharesOutstanding`, assumed, gates a decision.
8. **MarketQuote.change_percent** — Yahoo Finance `Close (pair)`, assumed, gates a decision.
9. **ValuationSnapshot.dividend_yield** — Yahoo Finance `dividendYield`, unknown, gates a decision.
   two provider schemas serve this key at two scales — quoteSummary as a fraction (0.0517), /v7/finance/quote as percentage points (5.17) — and the client library merges them, so which arrived depends on whether an HTTP call succeeded. No interpretation of the merged field is justified; measured over 77 stored records, 33 are percent-scale and 1 is a fraction.
10. **ValuationSnapshot.eps** — Yahoo Finance `trailingEps`, assumed, gates a decision.
11. **ValuationSnapshot.eps (substituted)** — Yahoo Finance `forwardEps`, unknown, gates a decision.
   a forecast standing in for a realised figure under one field name. The substitution is decision-visible exactly where trailing and forward earnings differ in sign — the turnaround case — where a loss-making company earns the platform's positive-earnings point on an estimate.
12. **ValuationSnapshot.forward_pe** — Yahoo Finance `forwardPE`, assumed, gates a decision.
13. **ValuationSnapshot.market_cap** — Yahoo Finance `marketCap`, assumed, gates a decision.
14. **YahooInstrument.yahoo_symbol** — Yahoo Finance `<symbol>`, assumed, gates a decision.
15. **AssetClass** — eToro `assetTypeId`, assumed, selects which analysis runs.
16. **AssetClass** — eToro `instrumentTypeID`, unknown, selects which analysis runs.
   read through the same four-row table as the watchlist's assetTypeId, and nothing establishes that the two eToro endpoints share a codespace. The broker publishes a taxonomy endpoint that would declare it; nothing calls it.
17. **ValuationSnapshot.industry** — Yahoo Finance `industry`, assumed, selects which analysis runs.
18. **ValuationSnapshot.sector** — Yahoo Finance `sector`, assumed, selects which analysis runs.
19. **ValuationSnapshot.current_ratio** — Yahoo Finance `currentRatio`, assumed, shapes research findings.
20. **ValuationSnapshot.debt_to_equity** — Yahoo Finance `debtToEquity`, assumed, shapes research findings.
21. **ValuationSnapshot.earnings_growth** — Yahoo Finance `earningsGrowth`, assumed, shapes research findings.
22. **ValuationSnapshot.free_cash_flow** — Yahoo Finance `freeCashflow`, assumed, shapes research findings.
23. **ValuationSnapshot.gross_margin** — Yahoo Finance `grossMargins`, assumed, shapes research findings.
24. **ValuationSnapshot.net_margin** — Yahoo Finance `profitMargins`, assumed, shapes research findings.
25. **ValuationSnapshot.operating_cash_flow** — Yahoo Finance `operatingCashflow`, assumed, shapes research findings.
26. **ValuationSnapshot.operating_margin** — Yahoo Finance `operatingMargins`, assumed, shapes research findings.
27. **ValuationSnapshot.revenue_growth** — Yahoo Finance `revenueGrowth`, assumed, shapes research findings.
28. **MarketQuote.currency** — Yahoo Finance `<none — hardcoded>`, assumed, display only.
29. **MarketQuote.price** — Yahoo Finance `Close`, assumed, display only.
30. **MarketQuote.price (^TNX)** — Yahoo Finance `Close (^TNX)`, unknown, display only.
   the value is a yield under the CBOE's times-ten convention (42.5 is 4.25%) entering a field named price, and the currency beside it is invented. Two translations on one field, neither of them checked; the representation is left unnamed because what it should be is exactly what is in dispute.
31. **ValuationSnapshot.expense_ratio** — Yahoo Finance `netExpenseRatio`, assumed, display only.
32. **ValuationSnapshot.circulating_supply** — Yahoo Finance `circulatingSupply`, assumed, consumed by nothing.
33. **ValuationSnapshot.inception** — Yahoo Finance `startDate`, assumed, consumed by nothing.
34. **ValuationSnapshot.max_supply** — Yahoo Finance `maxSupply`, assumed, consumed by nothing.
35. **ValuationSnapshot.peg_ratio** — Yahoo Finance `pegRatio`, assumed, consumed by nothing.
36. **ValuationSnapshot.return_on_equity** — Yahoo Finance `returnOnEquity`, assumed, consumed by nothing.
37. **ValuationSnapshot.trailing_pe** — Yahoo Finance `trailingPE`, assumed, consumed by nothing.
38. **ValuationSnapshot.volume_24h** — Yahoo Finance `volume24Hr`, assumed, consumed by nothing.

