"""Market quotes that are fetched once, not once per question asked."""

from __future__ import annotations

from datetime import datetime, timedelta

from app.domain.market_sensitivity import MarketSensitivity
from app.domain.market_snapshot import MarketData, MarketQuote
from app.domain.provenance import Provenance
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

    Two doors, and which one a caller opens decides whether it can reach
    the network. This one acquires: an expired quote is fetched again, and
    an acquisition cycle is the thing that opens it. `stored` is the
    read-only door a page uses.

    An instrument this door cannot price keeps whatever the store already
    held for it. A failure used to be written *over* the last real quote,
    which was survivable while a stale quote was refused anyway — and is
    not now that the surfaces serve stored prices with their age. One
    transient failure during the first acquisition cycle left a holding
    with no price at all, when a three-hour-old one was sitting there.
    """

    VIX_KEY = "^VIX:vix"

    def __init__(
        self,
        provider: YahooMarketProvider | None = None,
        cache: JsonCache | None = None,
        ttl: timedelta = timedelta(minutes=15),
        acquires: bool = True,
    ) -> None:
        self._provider = provider or YahooMarketProvider()
        self._cache = cache or JsonCache(
            "data/cache/quotes",
            # Schema 1, and records written before this store
            # declared one are accepted as schema 1 deliberately —
            # their shape is what schema 1 describes. The next bump
            # needs a migration or they re-acquire, which is the
            # protection: the store cannot change shape by accident.
            schema=1,
            accepts_unversioned=True,
        )
        self._ttl = ttl

        self._acquires = acquires

    @classmethod
    def stored(
        cls,
        cache: JsonCache | None = None,
    ) -> CachedMarketProvider:
        """
        The prices this platform has already read, and nothing it has not.

        The read-only door, for surfaces rather than for acquisition —
        the same door `CompanyKnowledgeService.established` is for the
        filings. A page view that acquires is a page view that decides,
        on the investor's behalf and without being asked, to spend a
        rate limit and wait for a provider: one dossier downloaded a
        year of daily closes eleven times over, and `SPY` thirteen
        times, because the benchmark is read once per batch and the page
        asked in batches of one.

        Freshness is not enforced here, and that is the point. A stored
        quote keeps the moment it was taken, so what a surface serves is
        "Yahoo Finance, three hours ago" — old evidence, dated, which
        this platform already prefers to a wait or a blank. A symbol
        never acquired has no quote, and an absence is reported as one.
        """

        return cls(cache=cache, acquires=False)

    async def snapshot(self) -> MarketData:
        return MarketData(
            quotes=await self.quotes(),
            vix=await self.vix(),
        )

    async def vix(self) -> float | None:
        entry = self._cache.read(self.VIX_KEY)

        if entry is not None and (not self._acquires or entry.is_fresh(self._ttl)):
            value = entry.value.get("vix")

            return float(value) if isinstance(value, (int, float)) else None

        if not self._acquires:
            return None

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

            if entry is not None and (not self._acquires or entry.is_fresh(self._ttl)):
                quote = self._restore(entry.value)

                if quote is not None:
                    cached[instrument.movrvest_symbol] = quote
                    continue

            missing.append(instrument)

        if missing and self._acquires:
            try:
                fetched = await self._provider.quotes(tuple(missing))
            except Exception:
                # Every missing instrument failed. Whatever was already
                # priced recently still stands; the rest simply has no
                # quote, which is reported as absent further up.
                if not cached:
                    raise

                fetched = ()

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

        # An acquisition that priced nothing failed; a store that holds
        # nothing is simply empty. Only the first is an error — the second
        # is an absence, and absences are reported, not raised.
        if not ordered and self._acquires:
            raise RuntimeError("Yahoo Finance returned no usable market quotes")

        return ordered

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
            # Measured off a year of history that a replayed quote does not
            # carry, so it is kept whole here rather than recomputed against
            # a benchmark this fast path never fetched.
            "market_sensitivity": CachedMarketProvider._encode_sensitivity(
                quote.market_sensitivity
            ),
            # The time the price was taken, not the time it was written.
            # A replayed quote that redated itself would report a
            # fifteen-minute-old price as current, which is the thing this
            # cache exists to avoid doing quietly.
            "source": quote.reading.source if quote.reading else None,
            "observed_at": (
                quote.reading.observed_at.isoformat() if quote.reading else None
            ),
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
            market_sensitivity=CachedMarketProvider._restore_sensitivity(
                value.get("market_sensitivity")
            ),
            reading=CachedMarketProvider._reading(value),
        )

    @staticmethod
    def _encode_sensitivity(
        sensitivity: MarketSensitivity | None,
    ) -> dict[str, object] | None:
        if sensitivity is None:
            return None

        return {
            "beta": sensitivity.beta,
            "correlation": sensitivity.correlation,
            "observations": sensitivity.observations,
            "benchmark": sensitivity.benchmark,
        }

    @staticmethod
    def _restore_sensitivity(
        value: object,
    ) -> MarketSensitivity | None:
        if not isinstance(value, dict):
            return None

        beta = value.get("beta")
        correlation = value.get("correlation")
        observations = value.get("observations")
        benchmark = value.get("benchmark")

        if not isinstance(beta, (int, float)) or not isinstance(
            correlation, (int, float)
        ):
            return None

        if not isinstance(observations, int) or not isinstance(benchmark, str):
            return None

        return MarketSensitivity(
            beta=float(beta),
            correlation=float(correlation),
            observations=observations,
            benchmark=benchmark,
        )

    @staticmethod
    def _reading(
        value: dict[str, object],
    ) -> Provenance | None:
        source = value.get("source")
        observed_at = value.get("observed_at")

        if not isinstance(source, str) or not isinstance(observed_at, str):
            return None

        try:
            return Provenance(
                source=source,
                observed_at=datetime.fromisoformat(observed_at),
            )
        except ValueError:
            return None
