import asyncio
from dataclasses import dataclass

import yfinance as yf

from app.domain.market_snapshot import MarketData, MarketQuote


@dataclass(frozen=True, slots=True)
class YahooInstrument:
    yahoo_symbol: str
    movrvest_symbol: str
    name: str


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
            yahoo_symbol="BTC-USD",
            movrvest_symbol="BTC",
            name="Bitcoin",
        ),
        YahooInstrument(
            yahoo_symbol="GLD",
            movrvest_symbol="GLD",
            name="Gold ETF",
        ),
    )

    VIX_SYMBOL = "^VIX"

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
        instruments: tuple[YahooInstrument, ...] | None = None,
    ) -> tuple[MarketQuote, ...]:
        selected = instruments or self.DEFAULT_INSTRUMENTS

        tasks = [
            asyncio.to_thread(self._fetch_quote, instrument) for instrument in selected
        ]

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

        quotes: list[MarketQuote] = []

        for result in results:
            if isinstance(result, Exception):
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
            period="5d",
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
            symbol=instrument.movrvest_symbol,
            name=instrument.name,
            price=round(latest, 4),
            change_percent=round(change_percent, 2),
            currency="USD",
        )

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

        return round(float(closes.iloc[-1]), 2)
