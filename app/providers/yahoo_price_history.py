"""Daily closes for a security the journal only knows by symbol."""

from __future__ import annotations

import asyncio
from datetime import date
from typing import Any, Protocol

import yfinance as yf

from app.domain.asset_class import AssetClass
from app.domain.provider_identity import crypto_listing
from app.domain.watchlist_item import WatchlistItem
from app.providers.yahoo_market_provider import YahooInstrument, YahooMarketProvider


class SymbolLookup(Protocol):
    """Anything that can say what kind of thing a symbol is."""

    async def find_symbol(self, symbol: str) -> WatchlistItem | None: ...


class YahooPriceHistory:
    """
    What a security closed at, day by day, over the past year.

    The journal records a symbol and nothing else, and a symbol is not a
    ticker: `BTC` prices under `BTC-USD`, and the watchlists are the only
    place this platform learns which is which. The resolution is the
    existing one rather than a second guess at it — a wrong ticker here
    would price one security's decision against another's chart.

    A symbol nothing can resolve or price returns nothing. The caller
    reports it as unmeasured, which is what it is.
    """

    SOURCE = "Yahoo Finance"

    def __init__(
        self,
        lookup: SymbolLookup | None = None,
        period: str = YahooMarketProvider.HISTORY_PERIOD,
    ) -> None:
        # Imported here, not at module scope: `WatchlistService` reaches
        # the committee stack, which imports providers, and a provider
        # importing it back closes the circle at import time.
        if lookup is None:
            from app.services.watchlist_service import WatchlistService

            lookup = WatchlistService()

        self._lookup: SymbolLookup = lookup
        self._period = period

        # One download per symbol per run. Several decisions about the
        # same security are common — the journal records one per state
        # per day — and each would otherwise cost its own request against
        # a provider that rate-limits.
        self._closes: dict[str, dict[date, float] | None] = {}

    async def closes(self, symbol: str) -> dict[date, float] | None:
        normalized = symbol.upper().strip()

        if normalized in self._closes:
            return self._closes[normalized]

        ticker = await self._ticker(normalized)

        if ticker is None:
            self._closes[normalized] = None

            return None

        try:
            series = await asyncio.to_thread(self._download, ticker)
        except Exception:
            series = None

        self._closes[normalized] = series

        return series

    async def _ticker(self, symbol: str) -> str | None:
        """
        The ticker this symbol actually prices under, or nothing.

        A placeholder symbol — the `#1238` the platform prints for a
        holding no watchlist describes — is not a ticker and is not
        offered to the provider as one.

        Nor is a cryptocurrency pair the vendor lists a different token
        under. `HYPE-USD` returns Supreme Finance and `TAO-USD` returns
        Together As One: charted here, one token's decision would be
        scored against another token's move, and the outcome would look
        exactly like a measurement. The crypto-native pool publishes a
        price and not a year of closes, so this refuses rather than
        substitutes, and the caller reports the outcome as unmeasured —
        which is what it is.
        """

        if symbol.startswith("#"):
            return None

        try:
            item = await self._lookup.find_symbol(symbol)
        except Exception:
            return None

        if item is None:
            return None

        asset_class = AssetClass.from_etoro(item.asset_type_id)

        ticker = YahooInstrument.for_security(
            item.symbol,
            item.name,
            asset_class,
        ).yahoo_symbol

        if asset_class is not AssetClass.CRYPTO:
            return ticker

        return ticker if self._listing_agrees(item, ticker) else None

    def _listing_agrees(self, item: WatchlistItem, ticker: str) -> bool:
        """Whether the vendor's pair listing names this token.

        Read from the fundamentals this platform already stored for the
        ticker — the read-only door, so asking costs nothing and this
        provider stays the only thing here that reaches the network.
        """

        from app.providers.cached_value_provider import CachedValueProvider

        try:
            vendor = CachedValueProvider.stored().snapshot(ticker).vendor_identity
        except Exception:
            vendor = None

        return crypto_listing(
            symbol=item.symbol,
            vendor_symbol=ticker,
            vendor_name=vendor.name if vendor is not None else None,
            token_names=(item.name,),
        ).agrees

    def _download(self, ticker: str) -> dict[date, float] | None:
        history: Any = yf.download(
            ticker,
            period=self._period,
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False,
            timeout=15,
            multi_level_index=False,
        )

        if history is None or history.empty or "Close" not in history:
            return None

        closes = history["Close"].dropna()

        if closes.empty:
            return None

        return {
            index.date(): float(value)
            for index, value in closes.items()
            if hasattr(index, "date")
        }
