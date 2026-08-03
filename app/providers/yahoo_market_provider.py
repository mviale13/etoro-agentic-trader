from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from math import isfinite, sqrt
from typing import Any

import yfinance as yf

from app.domain.asset_class import AssetClass
from app.domain.market_snapshot import MarketData, MarketQuote
from app.domain.provenance import Provenance


@dataclass(frozen=True, slots=True)
class YahooInstrument:
    yahoo_symbol: str
    movrvest_symbol: str
    name: str

    @classmethod
    def for_security(
        cls,
        symbol: str,
        name: str,
        asset_class: AssetClass,
    ) -> YahooInstrument:
        """
        The ticker Yahoo prices this security under.

        Most securities trade under the symbol the broker already uses.
        Cryptocurrencies do not: Yahoo quotes them against a currency, so
        `BTC` prices as `BTC-USD` and the bare ticker returns nothing at
        all. The security keeps its own symbol everywhere else, so evidence
        still comes back under the name the investor knows.
        """

        return cls(
            yahoo_symbol=(
                f"{symbol}-USD" if asset_class is AssetClass.CRYPTO else symbol
            ),
            movrvest_symbol=symbol,
            name=name,
        )


class YahooMarketProvider:
    DEFAULT_INSTRUMENTS = (
        YahooInstrument(
            yahoo_symbol="SPY",
            movrvest_symbol="SPY",
            name="S&P 500 ETF",
        ),
        YahooInstrument(
            yahoo_symbol="QQQ",
            movrvest_symbol="QQQ",
            name="Nasdaq 100 ETF",
        ),
        YahooInstrument(
            yahoo_symbol="IWM",
            movrvest_symbol="IWM",
            name="Russell 2000 ETF",
        ),
        YahooInstrument(
            yahoo_symbol="BTC-USD",
            movrvest_symbol="BTC",
            name="Bitcoin",
        ),
        YahooInstrument(
            yahoo_symbol="ETH-USD",
            movrvest_symbol="ETH",
            name="Ethereum",
        ),
        YahooInstrument(
            yahoo_symbol="GLD",
            movrvest_symbol="GLD",
            name="Gold ETF",
        ),
        YahooInstrument(
            yahoo_symbol="CL=F",
            movrvest_symbol="WTI",
            name="WTI Crude Oil",
        ),
        YahooInstrument(
            yahoo_symbol="DX-Y.NYB",
            movrvest_symbol="DXY",
            name="US Dollar Index",
        ),
        YahooInstrument(
            yahoo_symbol="^TNX",
            movrvest_symbol="TNX",
            name="US 10-Year Treasury Yield",
        ),
    )

    #: Named as the investor would see it, because it is printed to them.
    SOURCE = "Yahoo Finance"

    VIX_SYMBOL = "^VIX"

    #: How much price history one quote request carries.
    #:
    #: Five days priced the instrument and told us nothing else. A year costs
    #: the same single request and is enough to measure how violently the
    #: security has actually moved — which is the difference between risk
    #: being measured and risk being asserted.
    HISTORY_PERIOD = "1y"

    #: Daily observations needed before volatility or drawdown mean anything.
    MINIMUM_OBSERVATIONS = 30

    #: Trading days in a year, for annualising a daily standard deviation.
    TRADING_DAYS = 252

    async def snapshot(self) -> MarketData:
        quotes_task = asyncio.create_task(self.quotes())
        vix_task = asyncio.create_task(self.vix())

        quotes, vix = await asyncio.gather(
            quotes_task,
            vix_task,
        )

        return MarketData(
            quotes=quotes,
            vix=vix,
        )

    async def quotes(
        self,
        instruments: tuple[
            YahooInstrument,
            ...,
        ]
        | None = None,
    ) -> tuple[MarketQuote, ...]:
        selected = instruments or self.DEFAULT_INSTRUMENTS

        tasks = [
            asyncio.to_thread(
                self._fetch_quote,
                instrument,
            )
            for instrument in selected
        ]

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

        quotes: list[MarketQuote] = []

        for result in results:
            if isinstance(
                result,
                BaseException,
            ):
                continue

            quotes.append(result)

        if not quotes:
            raise RuntimeError("Yahoo Finance returned no usable market quotes")

        return tuple(quotes)

    async def vix(self) -> float | None:
        try:
            return await asyncio.to_thread(
                self._fetch_latest_close,
                self.VIX_SYMBOL,
            )
        except Exception:
            return None

    @staticmethod
    def _fetch_quote(
        instrument: YahooInstrument,
    ) -> MarketQuote:
        history = yf.download(
            instrument.yahoo_symbol,
            period=YahooMarketProvider.HISTORY_PERIOD,
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False,
            timeout=15,
            multi_level_index=False,
        )

        if history is None or history.empty:
            raise RuntimeError(
                f"No Yahoo Finance data returned for {instrument.yahoo_symbol}"
            )

        closes = history["Close"].dropna()

        if closes.empty:
            raise RuntimeError(
                f"No closing prices returned for {instrument.yahoo_symbol}"
            )

        latest = float(closes.iloc[-1])

        if len(closes) >= 2:
            previous = float(closes.iloc[-2])

            change_percent = (
                ((latest - previous) / previous) * 100 if previous != 0 else 0.0
            )
        else:
            change_percent = 0.0

        return MarketQuote(
            symbol=(instrument.movrvest_symbol),
            name=instrument.name,
            price=round(latest, 4),
            change_percent=round(
                change_percent,
                2,
            ),
            currency="USD",
            realized_volatility=YahooMarketProvider._realized_volatility(closes),
            max_drawdown=YahooMarketProvider._max_drawdown(closes),
            reading=Provenance(
                source=YahooMarketProvider.SOURCE,
                observed_at=datetime.now(UTC),
            ),
        )

    @classmethod
    def _realized_volatility(
        cls,
        closes: Any,
    ) -> float | None:
        """
        How violently this security actually moved, annualised.

        This is a measurement of the observed window, not a forecast. A
        series too short to say anything returns nothing.
        """

        if len(closes) < cls.MINIMUM_OBSERVATIONS:
            return None

        returns = closes.pct_change().dropna()

        if returns.empty:
            return None

        deviation = float(returns.std())

        if not isfinite(deviation):
            return None

        return round(deviation * sqrt(cls.TRADING_DAYS), 4)

    @classmethod
    def _max_drawdown(
        cls,
        closes: Any,
    ) -> float | None:
        """The deepest peak-to-trough fall in the observed window."""

        if len(closes) < cls.MINIMUM_OBSERVATIONS:
            return None

        drawdowns = closes / closes.cummax() - 1.0

        deepest = float(drawdowns.min())

        if not isfinite(deepest):
            return None

        return round(abs(deepest), 4)

    @staticmethod
    def _fetch_latest_close(
        symbol: str,
    ) -> float:
        history = yf.download(
            symbol,
            period="5d",
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False,
            timeout=15,
            multi_level_index=False,
        )

        if history is None or history.empty:
            raise RuntimeError(f"No Yahoo Finance data returned for {symbol}")

        closes = history["Close"].dropna()

        if closes.empty:
            raise RuntimeError(f"No closing prices returned for {symbol}")

        return round(
            float(closes.iloc[-1]),
            2,
        )
