from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, date, datetime
from math import isfinite, sqrt
from typing import Any

import yfinance as yf

from app.domain.asset_class import AssetClass
from app.domain.drawdown import deepest_drawdown
from app.domain.market_sensitivity import MarketSensitivity, measure_sensitivity
from app.domain.market_snapshot import MarketData, MarketQuote
from app.domain.provenance import Provenance
from app.domain.provider_claim import ClaimAbsence

#: Venues the broker and Yahoo name differently.
#:
#: eToro suffixes a listing with the city; Yahoo suffixes it with the
#: exchange's own code. Where the two words name one venue the local
#: ticker is identical and only the suffix differs, so this translates a
#: venue's name and nothing else.
#:
#: Measured before it was written, and every other suffix on this book
#: measured with it: `.BR`, `.DE`, `.CO`, `.PA`, `.L`, `.MC` and `.MI`
#: are the same word at both vendors and are passed through untouched.
#: Only Zurich differed — `NESN.ZU` returns a single empty field, and
#: `NESN.SW` returns Nestlé with 169 of them and a market cap of $208bn.
#:
#: What this does not do is check that the security at the translated
#: ticker is the one intended. That is the trust this platform already
#: extends to every ticker it passes through unchanged, and it is why an
#: entry is added here only after being checked against the provider by
#: hand — a venue guessed rather than verified is how a platform ends up
#: pricing another company's listing and cannot see that it did.
VENUES = {"ZU": "SW"}


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
        all. Nor does a listing at a venue the two vendors name
        differently. The security keeps its own symbol everywhere else,
        so evidence still comes back under the name the investor knows.
        """

        return cls(
            yahoo_symbol=(
                f"{symbol}-USD"
                if asset_class is AssetClass.CRYPTO
                else cls._at_venue(symbol)
            ),
            movrvest_symbol=symbol,
            name=name,
        )

    @staticmethod
    def _at_venue(symbol: str) -> str:
        """The same local ticker, at the venue under Yahoo's name for it."""

        local, separator, venue = symbol.rpartition(".")

        if not separator or venue not in VENUES:
            return symbol

        return f"{local}.{VENUES[venue]}"


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

    #: The market every security's sensitivity is measured against.
    #:
    #: One broad index stands for "the market" here, so a beta is a single,
    #: comparable number across the book rather than one measured against a
    #: different yardstick per holding. It is named on the measurement so a
    #: reader always knows which market the security was found to move with.
    BENCHMARK_SYMBOL = "SPY"

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

        # Read once, for the whole batch, before anything is priced against
        # it. Every quote is measured for its sensitivity to the same market,
        # so downloading that market's history per instrument would spend the
        # rate limit on the same series over and over. A benchmark that could
        # not be read leaves every sensitivity absent rather than failing the
        # batch — the prices still stand.
        benchmark_closes = await asyncio.to_thread(self._benchmark_closes)

        tasks = [
            asyncio.to_thread(
                self._fetch_quote,
                instrument,
                benchmark_closes,
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
        benchmark_closes: Any | None = None,
    ) -> MarketQuote:
        closes = YahooMarketProvider._download_closes(instrument.yahoo_symbol)

        latest = float(closes.iloc[-1])

        # The zero and its reason are decided together. Both branches
        # below produce 0.0 exactly as they always have — the value is
        # untouched — but a zero that stands in for a measurement now
        # says so, because downstream the momentum signal reads it as
        # "did not move today" at confidence 60 and cannot currently
        # tell that nothing was measured at all.
        change_absence: ClaimAbsence | None = None

        if len(closes) >= 2:
            previous = float(closes.iloc[-2])

            if previous != 0:
                change_percent = ((latest - previous) / previous) * 100
            else:
                change_percent = 0.0
                change_absence = ClaimAbsence.MALFORMED_STORED_VALUE
        else:
            change_percent = 0.0
            change_absence = ClaimAbsence.INSUFFICIENT_HISTORY

        return MarketQuote(
            symbol=(instrument.movrvest_symbol),
            name=instrument.name,
            price=round(latest, 4),
            change_percent=round(
                change_percent,
                2,
            ),
            change_absence=change_absence,
            # The closing series' own last date, which this adapter
            # previously read for alignment and threw away. It is the
            # only evidence that can tell a move made today from a
            # Friday close read on a Sunday, and without it the
            # momentum sentence claimed "today" for both.
            session_date=YahooMarketProvider._session_date(closes),
            # The provider does report a currency for the listing; this
            # adapter does not read it, and writes the same word for
            # every instrument. Left exactly as it was — repairing it
            # would move prices — and now labelled as the assumption it
            # is, so nothing converts by it believing it was measured.
            currency="USD",
            currency_is_assumed=True,
            realized_volatility=YahooMarketProvider._realized_volatility(closes),
            max_drawdown=YahooMarketProvider._max_drawdown(closes),
            market_sensitivity=YahooMarketProvider._market_sensitivity(
                closes,
                benchmark_closes,
            ),
            reading=Provenance(
                source=YahooMarketProvider.SOURCE,
                observed_at=datetime.now(UTC),
            ),
        )

    @staticmethod
    def _session_date(closes: Any) -> date | None:
        """The date of the last close, if the series carries one.

        Read from the index the provider already supplies. Nothing is
        inferred: a series whose index is not dated yields `None`, and
        the momentum sentence then declines to name a session rather
        than guessing one.
        """

        try:
            stamp = closes.index[-1]
        except (AttributeError, IndexError):
            return None

        moment = getattr(stamp, "date", None)

        return moment() if callable(moment) else None

    @staticmethod
    def _download_closes(yahoo_symbol: str) -> Any:
        """
        A year of daily closing prices for one symbol, dropna'd.

        Extracted because two readings now come off the same download — the
        security's own history and the benchmark it is measured against — and
        one place to ask for closes keeps the two asking the same way.
        """

        history = yf.download(
            yahoo_symbol,
            period=YahooMarketProvider.HISTORY_PERIOD,
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False,
            timeout=15,
            multi_level_index=False,
        )

        if history is None or history.empty:
            raise RuntimeError(f"No Yahoo Finance data returned for {yahoo_symbol}")

        closes = history["Close"].dropna()

        if closes.empty:
            raise RuntimeError(f"No closing prices returned for {yahoo_symbol}")

        return closes

    @classmethod
    def _benchmark_closes(cls) -> Any | None:
        """The market's own history, or nothing when it could not be read."""

        try:
            return cls._download_closes(cls.BENCHMARK_SYMBOL)
        except Exception:
            return None

    @classmethod
    def _market_sensitivity(
        cls,
        closes: Any,
        benchmark_closes: Any | None,
    ) -> MarketSensitivity | None:
        """
        How much this security moved with the benchmark over the window.

        The two return series are aligned to their common dates before
        anything is measured: a crypto that trades on weekends and an index
        that does not are only comparable on the days both were priced, and
        pairing them any other way would correlate Monday's move with
        Sunday's. A benchmark that was not read, or a window with nothing in
        common, leaves the sensitivity absent.
        """

        if benchmark_closes is None:
            return None

        security_returns = closes.pct_change().dropna()
        benchmark_returns = benchmark_closes.pct_change().dropna()

        aligned_security, aligned_benchmark = security_returns.align(
            benchmark_returns,
            join="inner",
        )

        if aligned_security.empty:
            return None

        return measure_sensitivity(
            [float(value) for value in aligned_security],
            [float(value) for value in aligned_benchmark],
            benchmark=cls.BENCHMARK_SYMBOL,
            minimum_observations=cls.MINIMUM_OBSERVATIONS,
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
        """
        The deepest peak-to-trough fall in the observed window.

        The walk itself lives in the domain, because the account's own
        equity curve is measured the same way and two implementations of
        "how far did it fall" would eventually disagree on a dashboard
        that shows both.
        """

        if len(closes) < cls.MINIMUM_OBSERVATIONS:
            return None

        measurement = deepest_drawdown([float(close) for close in closes])

        if measurement is None:
            return None

        return measurement.depth

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
