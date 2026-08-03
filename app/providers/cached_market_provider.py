"""Market quotes that are fetched once, not once per question asked."""

from __future__ import annotations

from datetime import timedelta

from app.domain.market_snapshot import MarketData, MarketQuote
from app.infrastructure.cache.json_cache import JsonCache
from app.providers.yahoo_market_provider import (
    YahooInstrument,
    YahooMarketProvider,
)


class CachedMarketProvider:
    """
    Serve a recent quote instead of asking for the same one again.

    A single page load used to price the same instruments many times over:
    once for the market snapshot, then again for every holding and every
    research candidate. The provider rate-limits, so that volume was the
    main reason evidence went missing.

    Unlike fundamentals, a quote is never served stale. A price is a claim
    about right now, so when the cached one has expired and the provider
    cannot be reached, this reports no quote rather than yesterday's.
    """

    VIX_KEY = "^VIX:vix"

    def __init__(
        self,
        provider: YahooMarketProvider | None = None,
        cache: JsonCache | None = None,
        ttl: timedelta = timedelta(minutes=15),
        failure_ttl: timedelta = timedelta(minutes=30),
    ) -> None:
        self._provider = provider or YahooMarketProvider()
        self._cache = cache or JsonCache("data/cache/quotes")
        self._ttl = ttl

        # A symbol the provider cannot price is remembered too, briefly. Some
        # instruments are simply not priceable under their current ticker —
        # crypto needs a -USD suffix, eToro futures have no Yahoo listing —
        # and retrying them on every request spent the rate limit that the
        # priceable securities needed.
        self._failure_ttl = failure_ttl

    async def snapshot(self) -> MarketData:
        return MarketData(
            quotes=await self.quotes(),
            vix=await self.vix(),
        )

    async def vix(self) -> float | None:
        entry = self._cache.read(self.VIX_KEY)

        if entry is not None and entry.is_fresh(self._ttl):
            value = entry.value.get("vix")

            return float(value) if isinstance(value, (int, float)) else None

        vix = await self._provider.vix()

        self._cache.write(self.VIX_KEY, {"vix": vix})

        return vix

    async def quotes(
        self,
        instruments: tuple[YahooInstrument, ...] | None = None,
    ) -> tuple[MarketQuote, ...]:
        selected = instruments or self._provider.DEFAULT_INSTRUMENTS

        cached: dict[str, MarketQuote] = {}
        missing: list[YahooInstrument] = []

        for instrument in selected:
            entry = self._cache.read(instrument.yahoo_symbol)

            if entry is not None:
                if entry.value.get("unavailable") is True:
                    if entry.is_fresh(self._failure_ttl):
                        continue
                elif entry.is_fresh(self._ttl):
                    quote = self._restore(entry.value)

                    if quote is not None:
                        cached[instrument.movrvest_symbol] = quote
                        continue

            missing.append(instrument)

        if missing:
            try:
                fetched = await self._provider.quotes(tuple(missing))
            except Exception:
                # Every missing instrument failed. Whatever was already
                # priced recently still stands; the rest simply has no
                # quote, which is reported as absent further up.
                self._remember_failures(missing, ())

                if not cached:
                    raise

                fetched = ()
            else:
                self._remember_failures(missing, fetched)

            by_symbol = {
                instrument.movrvest_symbol: instrument for instrument in missing
            }

            for quote in fetched:
                cached[quote.symbol] = quote

                fetched_instrument = by_symbol.get(quote.symbol)

                if fetched_instrument is not None:
                    self._cache.write(
                        fetched_instrument.yahoo_symbol,
                        self._encode(quote),
                    )

        ordered = tuple(
            cached[instrument.movrvest_symbol]
            for instrument in selected
            if instrument.movrvest_symbol in cached
        )

        if not ordered:
            raise RuntimeError("Yahoo Finance returned no usable market quotes")

        return ordered

    def _remember_failures(
        self,
        requested: list[YahooInstrument],
        fetched: tuple[MarketQuote, ...],
    ) -> None:
        """Record which instruments the provider could not price."""

        priced = {quote.symbol for quote in fetched}

        for instrument in requested:
            if instrument.movrvest_symbol not in priced:
                self._cache.write(
                    instrument.yahoo_symbol,
                    {"unavailable": True},
                )

    @staticmethod
    def _encode(
        quote: MarketQuote,
    ) -> dict[str, object]:
        return {
            "symbol": quote.symbol,
            "name": quote.name,
            "price": quote.price,
            "change_percent": quote.change_percent,
            "currency": quote.currency,
            "realized_volatility": quote.realized_volatility,
            "max_drawdown": quote.max_drawdown,
        }

    @staticmethod
    def _restore(
        value: dict[str, object],
    ) -> MarketQuote | None:
        symbol = value.get("symbol")
        price = value.get("price")
        change = value.get("change_percent")

        if not isinstance(symbol, str):
            return None

        if not isinstance(price, (int, float)):
            return None

        def ratio(field: str) -> float | None:
            raw = value.get(field)

            return float(raw) if isinstance(raw, (int, float)) else None

        return MarketQuote(
            symbol=symbol,
            name=str(value.get("name", symbol)),
            price=float(price),
            change_percent=float(change) if isinstance(change, (int, float)) else 0.0,
            currency=str(value.get("currency", "USD")),
            realized_volatility=ratio("realized_volatility"),
            max_drawdown=ratio("max_drawdown"),
        )
