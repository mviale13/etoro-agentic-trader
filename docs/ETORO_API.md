# eToro API — Read Route Inventory

Generated from the eToro MCP route catalogue on 2026-08-03.
API `v1.326.0` · base URL `https://public-api.etoro.com` · skill `1.4.0`.

This replaces a hand-written wish list that named twelve categories of
*information* and not one endpoint. Regenerate it rather than editing it by
hand — route ids and limits change with the API document.

---

## What this does not contain

The catalogue holds **170 routes**, of which **83 are
state-changing** and **7 deprecated**. Only the **85 read routes** are listed here.

Order placement, position closing, stop-loss modification, copy-trading and
money transfer are deliberately excluded. Evidence acquisition reads; it does
not act. Wiring an execution path is a separate decision with a separate
review, and it must not arrive as a side effect of capturing data.

---

## Rate limits

Published: **60 requests/minute for reads, 20 for writes, per user key**, in a
rolling one-minute window, `429` on breach.

The figure that matters is that limits are **pooled**. Most reads share one
60-per-minute budget; market data has its own 120. Calling any endpoint in a
pool spends that pool's allowance, so a batch cannot be planned as though each
endpoint had a limit of its own.

`EtoroClient` reads `ratelimit-remaining` from every response and keeps one
budget per endpoint. Nothing is hardcoded: a limit the headers do not state is
not throttled against.

---

## Trading & portfolio

| Path | Route id | Limit | Scopes |
|---|---|---|---|
| `/api/v1/trading/info/aggregate-portfolio` | `getAggregatedPortfolio` | 60 req / 60s (shared across 3 endpoints — ca | etoro-public:real:read, etoro-public:real:write, etoro-public:trade.real:read, etoro-public:trade.real:write |
| `/api/v1/trading/info/demo/aggregate-portfolio` | `getAggregatedPortfolioDemo` | 60 req / 60s (shared across 3 endpoints — ca | etoro-public:demo:read, etoro-public:demo:write, etoro-public:trade.demo:read, etoro-public:trade.demo:write |
| `/api/v2/trading/copy/{referenceId}` | `getCopyTradingStatus` | 60 req / 60s (default shared pool — shared w | etoro-public:real:read, etoro-public:real:write, etoro-public:trade.real:read, etoro-public:trade.real:write |
| `/api/v2/trading/copy/demo/{referenceId}` | `getCopyTradingStatusDemo` | 60 req / 60s (default shared pool — shared w | etoro-public:demo:read, etoro-public:demo:write, etoro-public:trade.demo:read, etoro-public:trade.demo:write |
| `/api/v1/trading/info/demo/close-orders/{orderId}` | `getTradingInfoDemoCloseOrdersByOrderId` | 60 req / 60s (shared across 3 endpoints — ca | etoro-public:demo:read, etoro-public:demo:write, etoro-public:trade.demo:read, etoro-public:trade.demo:write |
| `/api/v1/trading/info/demo/orders/{orderId}` | `getTradingInfoDemoOrdersByOrderId` | 60 req / 60s (shared across 3 endpoints — ca | etoro-public:demo:read, etoro-public:demo:write, etoro-public:trade.demo:read, etoro-public:trade.demo:write |
| `/api/v2/trading/info/demo/orders:lookup` | `getTradingInfoDemoOrdersLookup` | 60 req / 60s (shared across 3 endpoints — ca | etoro-public:demo:read, etoro-public:demo:write, etoro-public:trade.demo:read, etoro-public:trade.demo:write |
| `/api/v1/trading/info/demo/pnl` | `getTradingInfoDemoPnl` | 60 req / 60s (shared across 3 endpoints — ca | etoro-public:demo:read, etoro-public:demo:write, etoro-public:trade.demo:read, etoro-public:trade.demo:write |
| `/api/v1/trading/info/demo/portfolio` | `getTradingInfoDemoPortfolio` | 60 req / 60s (shared across 3 endpoints — ca | etoro-public:demo:read, etoro-public:demo:write, etoro-public:trade.demo:read, etoro-public:trade.demo:write |
| `/api/v2/trading/info/orders:lookup` | `getTradingInfoOrdersLookup` | 60 req / 60s (shared across 3 endpoints — ca | etoro-public:real:read, etoro-public:real:write, etoro-public:trade.real:read, etoro-public:trade.real:write |
| `/api/v1/trading/info/portfolio` | `getTradingInfoPortfolio` | 60 req / 60s (shared across 3 endpoints — ca | etoro-public:real:read, etoro-public:real:write, etoro-public:trade.real:read, etoro-public:trade.real:write |
| `/api/v1/trading/info/real/close-orders/{orderId}` | `getTradingInfoRealCloseOrdersByOrderId` | 60 req / 60s (shared across 3 endpoints — ca | etoro-public:real:read, etoro-public:real:write, etoro-public:trade.real:read, etoro-public:trade.real:write |
| `/api/v1/trading/info/real/orders/{orderId}` | `getTradingInfoRealOrdersByOrderId` | 60 req / 60s (shared across 3 endpoints — ca | etoro-public:real:read, etoro-public:real:write, etoro-public:trade.real:read, etoro-public:trade.real:write |
| `/api/v1/trading/info/real/pnl` | `getTradingInfoRealPnl` | 60 req / 60s (shared across 3 endpoints — ca | etoro-public:real:read, etoro-public:real:write, etoro-public:trade.real:read, etoro-public:trade.real:write |
| `/api/v1/trading/info/trade/demo/history` | `getTradingInfoTradeDemoHistory` | 60 req / 60s (default shared pool — shared w | etoro-public:demo:read, etoro-public:demo:write, etoro-public:trade.demo:read, etoro-public:trade.demo:write |
| `/api/v1/trading/info/trade/history` | `getTradingInfoTradeHistory` | 60 req / 60s (default shared pool — shared w | etoro-public:real:read, etoro-public:real:write, etoro-public:trade.real:read, etoro-public:trade.real:write |

## Balances

| Path | Route id | Limit | Scopes |
|---|---|---|---|
| `/api/v1/balances/{accountType}/{accountId}` | `getBalanceByAccount` | 60 req / 60s (default shared pool — shared w | etoro-public:money.balance:read |
| `/api/v1/balances` | `getBalances` | 60 req / 60s (default shared pool — shared w | etoro-public:money.balance:read |
| `/api/v1/balances/{accountType}` | `getBalancesByAccountType` | 60 req / 60s (default shared pool — shared w | etoro-public:money.balance:read |
| `/api/v1/balances/{accountType}/{accountId}/history` | `getHistoricalBalanceByAccount` | 60 req / 60s (default shared pool — shared w | etoro-public:money.balance:read |
| `/api/v1/balances/history` | `getHistoricalBalances` | 60 req / 60s (default shared pool — shared w | etoro-public:money.balance:read |
| `/api/v1/balances/{accountType}/history` | `getHistoricalBalancesByAccountType` | 60 req / 60s (default shared pool — shared w | etoro-public:money.balance:read |

## Money & transactions

| Path | Route id | Limit | Scopes |
|---|---|---|---|
| `/api/v1/money/transfers/{transferId}` | `getTransferById` | 60 req / 60s (default shared pool — shared w | etoro-public:money.transfer:read |
| `/api/v1/money/transfer-eligibility` | `getTransferEligibility` | 60 req / 60s (default shared pool — shared w | etoro-public:money.transfer:read |
| `/api/v1/money/transfer-fee-configurations` | `getTransferFeeConfiguration` | 60 req / 60s (default shared pool — shared w | etoro-public:money.transfer:read |
| `/api/v1/money/transfer-limits` | `getTransferLimits` | 60 req / 60s (default shared pool — shared w | etoro-public:money.transfer:read |
| `/api/v1/money/transferable-balance` | `getTransferableBalance` | 60 req / 60s (default shared pool — shared w | etoro-public:money.transfer:read |
| `/api/v1/money/accounts/cash/{accountId}/transactions` | `listCashAccountTransactions` | 60 req / 60s (default shared pool — shared w | etoro-public:money.cash-transactions:read |
| `/api/v1/money/transfers:lookup` | `lookupTransfersByRequestReferenceId` | 60 req / 60s (default shared pool — shared w | etoro-public:money.transfer:read |

## Market data

| Path | Route id | Limit | Scopes |
|---|---|---|---|
| `/api/v1/market-data/exchanges` | `getMarketDataExchanges` | 120 req / 60s (shared across 8 endpoints — c | etoro-public:real:read, etoro-public:demo:read, etoro-public:real:write, etoro-public:demo:write, etoro-public:market-data:read |
| `/api/v1/market-data/instrument-types` | `getMarketDataInstrumentTypes` | 120 req / 60s (shared across 8 endpoints — c | etoro-public:real:read, etoro-public:demo:read, etoro-public:real:write, etoro-public:demo:write, etoro-public:market-data:read |
| `/api/v1/market-data/instruments` | `getMarketDataInstruments` | 120 req / 60s (shared across 8 endpoints — c | etoro-public:real:read, etoro-public:demo:read, etoro-public:real:write, etoro-public:demo:write, etoro-public:market-data:read |
| `/api/v1/market-data/instruments/{instrumentId}/history/candles/{direction}/{interval}/{candlesCount}` | `getMarketDataInstrumentsByInstrumentIdHistoryCandlesByDirectionByIntervalByCandlesCount` | 120 req / 60s (shared across 8 endpoints — c | etoro-public:real:read, etoro-public:demo:read, etoro-public:real:write, etoro-public:demo:write, etoro-public:market-data:read |
| `/api/v1/market-data/instruments/history/closing-price` | `getMarketDataInstrumentsHistoryClosingPrice` | 120 req / 60s (shared across 8 endpoints — c | etoro-public:real:read, etoro-public:demo:read, etoro-public:real:write, etoro-public:demo:write, etoro-public:market-data:read |
| `/api/v1/market-data/instruments/rates` | `getMarketDataInstrumentsRates` | 120 req / 60s (shared across 8 endpoints — c | etoro-public:real:read, etoro-public:demo:read, etoro-public:real:write, etoro-public:demo:write, etoro-public:trade.real:read, etoro-public:trade.real:write, etoro-public:market-data:read |
| `/api/v1/market-data/search` | `getMarketDataSearch` | 120 req / 60s (shared across 8 endpoints — c | etoro-public:real:read, etoro-public:demo:read, etoro-public:real:write, etoro-public:demo:write, etoro-public:market-data:read |
| `/api/v1/market-data/stocks-industries` | `getMarketDataStocksIndustries` | 120 req / 60s (shared across 8 endpoints — c | etoro-public:real:read, etoro-public:demo:read, etoro-public:real:write, etoro-public:demo:write, etoro-public:market-data:read |

## Watchlists

| Path | Route id | Limit | Scopes |
|---|---|---|---|
| `/api/v1/watchlists` | `getWatchlists` | 60 req / 60s (shared across 5 endpoints — ca | etoro-public:demo:read, etoro-public:demo:write, etoro-public:real:read, etoro-public:real:write, etoro-public:watchlist:read, etoro-public:watchlist:write |
| `/api/v1/watchlists/{watchlistId}` | `getWatchlistsByWatchlistId` | 60 req / 60s (shared across 5 endpoints — ca | etoro-public:demo:read, etoro-public:demo:write, etoro-public:real:read, etoro-public:real:write, etoro-public:watchlist:read, etoro-public:watchlist:write |
| `/api/v1/watchlists/default-watchlists/items` | `getWatchlistsDefaultWatchlistsItems` | 60 req / 60s (shared across 5 endpoints — ca | etoro-public:demo:read, etoro-public:real:read, etoro-public:demo:write, etoro-public:real:write, etoro-public:watchlist:read, etoro-public:watchlist:write |
| `/api/v1/watchlists/public/{userId}` | `getWatchlistsPublicByUserId` | 60 req / 60s (shared across 5 endpoints — ca | etoro-public:demo:read, etoro-public:real:read, etoro-public:demo:write, etoro-public:real:write, etoro-public:watchlist:read, etoro-public:watchlist:write |
| `/api/v1/watchlists/public/{userId}/{watchlistId}` | `getWatchlistsPublicByUserIdByWatchlistId` | 60 req / 60s (shared across 5 endpoints — ca | etoro-public:demo:read, etoro-public:real:read, etoro-public:demo:write, etoro-public:real:write, etoro-public:watchlist:read, etoro-public:watchlist:write |

## Investor & performance

| Path | Route id | Limit | Scopes |
|---|---|---|---|
| `/api/v2/portfolios/{username}/assets/history` | `getAssetsHistory` | 60 req / 60s (default shared pool — shared w | etoro-public:user-info:read |
| `/api/v2/portfolios/{username}/exposure/history` | `getExposureHistory` | 60 req / 60s (default shared pool — shared w | etoro-public:user-info:read |
| `/api/v2/portfolios/{username}/gain/{granularity}` | `getGainHistory` | 60 req / 60s (default shared pool — shared w | etoro-public:user-info:read |
| `/api/v2/portfolios/{username}/copiers` | `getPortfolioCopiers` | 60 req / 60s (default shared pool — shared w | etoro-public:user-info:read |
| `/api/v2/portfolios/{username}/rankings` | `getPortfolioRanking` | 60 req / 60s (default shared pool — shared w | etoro-public:user-info:read |
| `/api/v2/portfolios/rankings/presets/{type}` | `getPortfolioRankingsByPreset` | 60 req / 60s (default shared pool — shared w | etoro-public:user-info:read |
| `/api/v2/portfolios/rankings` | `getPortfoliosRankings` | 60 req / 60s (default shared pool — shared w | etoro-public:user-info:read |
| `/api/v2/portfolios/rankings/summary` | `getPortfoliosRankingsSummary` | 60 req / 60s (default shared pool — shared w | etoro-public:user-info:read |
| `/api/v1/user-info/people` | `getUserInfoPeople` | 60 req / 60s (default shared pool — shared w | etoro-public:real:read, etoro-public:demo:read, etoro-public:real:write, etoro-public:demo:write, etoro-public:user-info:read |
| `/api/v1/user-info/people/{username}/daily-gain` | `getUserInfoPeopleByUsernameDailyGain` | 60 req / 60s (default shared pool — shared w | etoro-public:real:read, etoro-public:demo:read, etoro-public:real:write, etoro-public:demo:write, etoro-public:user-info:read |
| `/api/v1/user-info/people/{username}/gain` | `getUserInfoPeopleByUsernameGain` | 60 req / 60s (default shared pool — shared w | etoro-public:real:read, etoro-public:demo:read, etoro-public:real:write, etoro-public:demo:write, etoro-public:user-info:read |
| `/api/v1/user-info/people/{username}/portfolio/live` | `getUserInfoPeopleByUsernamePortfolioLive` | 60 req / 60s (dedicated to this endpoint) | etoro-public:real:read, etoro-public:demo:read, etoro-public:real:write, etoro-public:demo:write, etoro-public:user-info:read |
| `/api/v1/user-info/people/{username}/tradeinfo` | `getUserInfoPeopleByUsernameTradeinfo` | 60 req / 60s (dedicated to this endpoint) | etoro-public:real:read, etoro-public:demo:read, etoro-public:real:write, etoro-public:demo:write, etoro-public:user-info:read |
| `/api/v1/user-info/people/search` | `getUserInfoPeopleSearch` | 60 req / 60s (default shared pool — shared w | etoro-public:real:read, etoro-public:demo:read, etoro-public:real:write, etoro-public:demo:write, etoro-public:user-info:read |
| `/api/v2/portfolios/rankings/presets` | `listPortfolioRankingsPresets` | 60 req / 60s (default shared pool — shared w | etoro-public:user-info:read |
| `/api/v2/portfolios/rankings/tags` | `listPortfolioRankingsTags` | 60 req / 60s (default shared pool — shared w | etoro-public:user-info:read |
| `/api/v1/portfolios/search` | `searchPortfolios` | 60 req / 60s (default shared pool — shared w | etoro-public:user-info:read |

## Social & attention

| Path | Route id | Limit | Scopes |
|---|---|---|---|
| `/api/v1/feeds/following` | `getFeedsFollowing` | 60 req / 60s (shared across 9 endpoints — ca | etoro-public:feed:read |
| `/api/v1/feeds/for-you` | `getFeedsForYou` | 60 req / 60s (shared across 9 endpoints — ca | etoro-public:feed:read |
| `/api/v1/feeds/markets/{marketId}` | `getFeedsMarketsByMarketId` | 60 req / 60s (shared across 9 endpoints — ca | etoro-public:feed:read |
| `/api/v1/feeds/news` | `getFeedsNews` | 60 req / 60s (shared across 9 endpoints — ca | etoro-public:feed:read |
| `/api/v1/feeds/saved` | `getFeedsSaved` | 60 req / 60s (shared across 9 endpoints — ca | etoro-public:feed:read |
| `/api/v1/feeds/users/{userId}` | `getFeedsUsersByUserId` | 60 req / 60s (shared across 9 endpoints — ca | etoro-public:feed:read |
| `/api/v1/feeds/users/{userId}/pinned` | `getFeedsUsersByUserIdPinned` | 60 req / 60s (shared across 9 endpoints — ca | etoro-public:feed:read |
| `/api/v1/impressions/topassets/user/{gcid}` | `getImpressionsTopassetsUserByGcid` | 60 req / 60s (default shared pool — shared w | etoro-public:feed:read |
| `/api/v1/notifications/messages` | `getNotificationsMessages` | 60 req / 60s (default shared pool — shared w | etoro-public:notifications:read |
| `/api/v1/posts/{postId}` | `getPostsByPostId` | 60 req / 60s (default shared pool — shared w | etoro-public:feed:read |
| `/api/v1/posts/{postId}/comments` | `getPostsByPostIdComments` | 60 req / 60s (default shared pool — shared w | etoro-public:feed:read |
| `/api/v1/posts/{postId}/comments/{commentId}/replies` | `getPostsByPostIdCommentsByCommentIdReplies` | 60 req / 60s (default shared pool — shared w | etoro-public:feed:read |
| `/api/v1/posts/{postId}/shares` | `getPostsByPostIdShares` | 60 req / 60s (default shared pool — shared w | etoro-public:feed:read |

## Other

| Path | Route id | Limit | Scopes |
|---|---|---|---|
| `/api/v1/agent-portfolios` | `getAgentPortfolios` | 60 req / 60s (default shared pool — shared w | etoro-public:real:read, etoro-public:real:write, etoro-public:agent-portfolio:read, etoro-public:agent-portfolio:write |
| `/api/v2/agent-portfolios/user-tokens/scopes` | `getAgentPortfoliosScopes` | 60 req / 60s (default shared pool — shared w | etoro-public:agent-portfolio:read, etoro-public:agent-portfolio:write |
| `/api/v1/sso/applications` | `getApplications` | 60 req / 60s (default shared pool — shared w | etoro-public:sso-applications:read, etoro-public:sso-applications:write |
| `/api/v1/clubs` | `getClubs` | 60 req / 60s (default shared pool — shared w | etoro-public:club:read |
| `/api/v1/curated-lists` | `getCuratedLists` | 60 req / 60s (dedicated to this endpoint) | etoro-public:demo:read, etoro-public:real:read, etoro-public:demo:write, etoro-public:real:write, etoro-public:watchlist:read, etoro-public:watchlist:write |
| `/api/v1/market-recommendations/{itemsCount}` | `getMarketRecommendationsByItemsCount` | 60 req / 60s (dedicated to this endpoint) | etoro-public:demo:read, etoro-public:real:read, etoro-public:demo:write, etoro-public:real:write, etoro-public:watchlist:read, etoro-public:watchlist:write |
| `/api/v1/me` | `getMe` | 60 req / 60s (default shared pool — shared w | etoro-public:real:read, etoro-public:demo:read, etoro-public:real:write, etoro-public:demo:write, etoro-public:user-info:read |
| `/api/v1/sub-accounts/me/accounts` | `getMySubAccounts` | 60 req / 60s (default shared pool — shared w | etoro-public:sub-accounts:read, etoro-public:sub-accounts:write |
| `/api/v1/pi-data/copiers` | `getPiDataCopiers` | 60 req / 60s (default shared pool — shared w | etoro-public:real:read, etoro-public:real:write, etoro-public:pi-data:read |
| `/api/v1/price-alerts` | `getPriceAlerts` | 60 req / 60s (default shared pool — shared w | etoro-public:price-alerts:read |
| `/api/v1/sso/scopes` | `getScopes` | 60 req / 60s (default shared pool — shared w | etoro-public:sso-scopes:read, etoro-public:sso-scopes:write |
| `/api/v1/sub-accounts/etoro-trading/user-tokens/scopes` | `getSubAccountUserTokenScopes` | 60 req / 60s (default shared pool — shared w | etoro-public:sub-accounts:read, etoro-public:sub-accounts:write |
| `/api/v1/sub-accounts/etoro-trading/user-tokens` | `getSubAccountUserTokens` | 60 req / 60s (default shared pool — shared w | etoro-public:sub-accounts:read, etoro-public:sub-accounts:write |

---

## Regenerating

```bash
curl -sS -X POST https://mcp.public-api.etoro.com \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get-all-routes","arguments":{}}}'
```

Discovery needs no credentials. Only executing a route does, and the platform
executes through `EtoroClient` with the key from `.env` — never through the
MCP relay, so the secret stays in one place.

