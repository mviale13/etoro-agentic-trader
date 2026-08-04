"""The market as this account meets it."""

from __future__ import annotations

from app.domain.market_risk import ExposureVolatility, MarketRisk
from app.domain.market_snapshot import MarketSnapshot
from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.domain.provenance import Provenance, least_reliable
from app.services.risk_signal_service import RiskSignalService


class MarketRiskService:
    """
    Measure market risk from what the account holds and how it has moved.

    Two things were already true and never joined. Every benchmark quote
    carries a year of realised volatility, measured off its own closes.
    Every holding is classified against the watchlists, so the account
    knows how much of itself is equities, crypto or cash. Between them
    they say how violently the market this particular account is exposed
    to has actually been moving — which is what market risk means for a
    portfolio, and what was a hardcoded 0.50 until now.

    A blended figure is not the market's volatility. It is this account's,
    and an account in cash is exposed to none of it.
    """

    #: The instruments that stand for each market.
    #:
    #: Broad indices, not the account's own holdings: market risk is what
    #: the account carries by being in the market at all, which is exactly
    #: what a single security's own volatility does not describe.
    EQUITY_BENCHMARKS = ("SPY", "QQQ", "IWM")
    CRYPTO_BENCHMARKS = ("BTC", "ETH")

    #: How much of the account must have a benchmark before a blended
    #: figure may describe it.
    #:
    #: Below this, too much of the account is holdings no benchmark was
    #: found for, and a number covering the rest would be read as covering
    #: all of it.
    MINIMUM_COVERAGE = 0.80

    def measure(
        self,
        market: MarketSnapshot,
        portfolio: PortfolioSnapshot,
    ) -> MarketRisk | None:
        """
        The account's blended market volatility, or nothing.

        Nothing where too little of the account could be assigned a
        benchmark — including the case where the benchmarks themselves
        carry no volatility, which is what a market provider that did not
        answer looks like from here.
        """

        allocation = portfolio.allocation

        exposures: list[ExposureVolatility] = []
        readings: list[Provenance | None] = []

        cash_share = allocation.cash / 100.0

        if cash_share > 0:
            exposures.append(
                ExposureVolatility(
                    exposure="cash",
                    share=cash_share,
                    # Not an assumption. Cash does not move with the
                    # market, which is the whole reason to hold it.
                    volatility=0.0,
                    benchmarks=(),
                )
            )

        for name, share, benchmarks in (
            (
                "equities",
                (allocation.stocks + allocation.etfs) / 100.0,
                self.EQUITY_BENCHMARKS,
            ),
            (
                "crypto",
                allocation.crypto / 100.0,
                self.CRYPTO_BENCHMARKS,
            ),
        ):
            if share <= 0:
                continue

            measured = self._benchmark_volatility(market, benchmarks)

            if measured is None:
                # Held, but nothing here can say what its market did. It
                # stays out of the blend and out of the coverage, rather
                # than being counted as calm.
                continue

            volatility, used, benchmark_readings = measured

            exposures.append(
                ExposureVolatility(
                    exposure=name,
                    share=share,
                    volatility=volatility,
                    benchmarks=used,
                )
            )

            readings.extend(benchmark_readings)

        covered = sum(exposure.share for exposure in exposures)

        if covered < self.MINIMUM_COVERAGE:
            return None

        blended = (
            sum(exposure.share * exposure.volatility for exposure in exposures)
            / covered
        )

        return MarketRisk(
            volatility=round(blended, 4),
            exposures=tuple(exposures),
            covered_share=round(covered, 4),
            # The reading that most qualifies a figure drawn from all of
            # them: a benchmark whose provider did not answer outranks a
            # merely older one.
            reading=least_reliable(*readings),
        )

    @classmethod
    def risk_score(
        cls,
        market_risk: MarketRisk,
    ) -> float:
        """
        How far toward violent the account's own market has moved.

        Scored against the same threshold a single security's volatility
        is judged by. Where the line between calm and violent sits is a
        judgement this platform makes once; an account and a security
        moving 60% a year are both moving 60% a year.
        """

        return min(market_risk.volatility / RiskSignalService.VIOLENT, 1.0)

    @staticmethod
    def _benchmark_volatility(
        market: MarketSnapshot,
        benchmarks: tuple[str, ...],
    ) -> tuple[float, tuple[str, ...], list[Provenance | None]] | None:
        """
        The average measured volatility of the benchmarks that carry one.

        A benchmark whose series was too short to measure is left out
        rather than counted as calm. Where none of them carries a
        measurement there is nothing to average, and nothing is returned.
        """

        volatilities: list[float] = []
        used: list[str] = []
        readings: list[Provenance | None] = []

        for symbol in benchmarks:
            quote = market.quote(symbol)

            if quote is None or quote.realized_volatility is None:
                continue

            volatilities.append(quote.realized_volatility)
            used.append(quote.symbol)
            readings.append(quote.reading)

        if not volatilities:
            return None

        return (
            sum(volatilities) / len(volatilities),
            tuple(used),
            readings,
        )
