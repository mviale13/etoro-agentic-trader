"""The market as this account meets it, not the market in general."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from app.domain.market_snapshot import MarketQuote, MarketSnapshot
from app.domain.portfolio_snapshot import Allocation, PortfolioSnapshot
from app.domain.provenance import Provenance
from app.services.market_risk_service import MarketRiskService
from app.services.risk_signal_service import RiskSignalService

NOW = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)


def quote(
    symbol: str,
    volatility: float | None,
    reading: Provenance | None = None,
) -> MarketQuote:
    return MarketQuote(
        symbol=symbol,
        name=symbol,
        price=100.0,
        change_percent=0.5,
        realized_volatility=volatility,
        reading=reading or Provenance(source="Yahoo Finance", observed_at=NOW),
    )


def market(*quotes: MarketQuote) -> MarketSnapshot:
    return MarketSnapshot(
        quotes=quotes,
        market_mood="neutral",
        volatility="medium",
        summary="Markets are broadly neutral today.",
        timestamp=NOW,
    )


def equities(volatility: float = 0.18) -> tuple[MarketQuote, ...]:
    return tuple(
        quote(symbol, volatility) for symbol in MarketRiskService.EQUITY_BENCHMARKS
    )


def crypto(volatility: float = 0.60) -> tuple[MarketQuote, ...]:
    return tuple(
        quote(symbol, volatility) for symbol in MarketRiskService.CRYPTO_BENCHMARKS
    )


def account(
    cash: float = 0.0,
    stocks: float = 0.0,
    etfs: float = 0.0,
    crypto_pct: float = 0.0,
    unclassified: float = 0.0,
) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        allocation=Allocation(
            cash=cash,
            stocks=stocks,
            etfs=etfs,
            crypto=crypto_pct,
            unclassified=unclassified,
        ),
        total_value=50_000.0,
        positions=3,
        largest_position="MSFT",
        largest_position_pct=1.0,
        risk_flags=(),
    )


def test_an_account_in_cash_carries_no_market_risk() -> None:
    """
    Measured, not assumed. Cash does not move with the market, which is
    the whole reason to hold it — and a platform that reported market risk
    for a wholly uninvested account would be describing a market rather
    than an investor.
    """

    measured = MarketRiskService().measure(
        market(*equities(), *crypto()),
        account(cash=100.0),
    )

    assert measured is not None
    assert measured.volatility == 0.0
    assert MarketRiskService.risk_score(measured) == 0.0


def test_the_blend_follows_what_the_account_actually_holds() -> None:
    """
    The same market, two accounts. What the index did is not what this
    investor is exposed to.
    """

    calm = MarketRiskService().measure(
        market(*equities(0.20), *crypto(0.80)),
        account(cash=50.0, stocks=50.0),
    )

    violent = MarketRiskService().measure(
        market(*equities(0.20), *crypto(0.80)),
        account(cash=50.0, crypto_pct=50.0),
    )

    assert calm is not None and violent is not None
    assert calm.volatility == 0.10
    assert violent.volatility == 0.40


def test_equity_exposure_averages_the_broad_indices() -> None:
    measured = MarketRiskService().measure(
        market(quote("SPY", 0.15), quote("QQQ", 0.21), quote("IWM", 0.24)),
        account(stocks=60.0, etfs=40.0),
    )

    assert measured is not None
    assert measured.volatility == 0.20
    assert measured.exposures[0].benchmarks == ("SPY", "QQQ", "IWM")


def test_a_benchmark_with_no_measured_volatility_is_left_out() -> None:
    """A series too short to measure is not a calm one."""

    measured = MarketRiskService().measure(
        market(quote("SPY", None), quote("QQQ", 0.30), quote("IWM", 0.30)),
        account(stocks=100.0),
    )

    assert measured is not None
    assert measured.volatility == 0.30
    assert measured.exposures[0].benchmarks == ("QQQ", "IWM")


def test_holdings_with_no_benchmark_are_excluded_and_counted() -> None:
    """
    A commodity holding has no benchmark here. Counting it as calm would
    report a figure covering the whole account when it covers less.
    """

    measured = MarketRiskService().measure(
        market(*equities(0.20)),
        account(cash=50.0, stocks=40.0, unclassified=10.0),
    )

    assert measured is not None

    # Blended over the 90% it can describe, not over the whole account.
    assert measured.volatility == round(0.40 * 0.20 / 0.90, 4)
    assert measured.covered_share == 0.90
    assert round(measured.uncovered_share, 4) == 0.10


def test_too_little_of_the_account_to_describe_is_not_described() -> None:
    """
    Below the coverage floor a blended figure would be read as covering
    the account, when most of the account is holdings it says nothing
    about.
    """

    assert (
        MarketRiskService().measure(
            market(*equities(0.20)),
            account(stocks=20.0, unclassified=80.0),
        )
        is None
    )


def test_a_market_that_could_not_be_read_leaves_market_risk_unmeasured() -> None:
    """What a provider that did not answer looks like from here."""

    assert (
        MarketRiskService().measure(
            market(quote("SPY", None), quote("QQQ", None), quote("IWM", None)),
            account(stocks=100.0),
        )
        is None
    )


def test_the_least_reliable_benchmark_reading_qualifies_the_figure() -> None:
    """
    A benchmark whose provider did not answer outranks a merely older
    one, and the figure is dated by what most qualifies it.
    """

    degraded = Provenance(
        source="Yahoo Finance",
        observed_at=NOW,
        last_known=True,
    )

    measured = MarketRiskService().measure(
        market(
            quote("SPY", 0.20, reading=degraded),
            quote("QQQ", 0.20, Provenance(source="Yahoo Finance", observed_at=NOW)),
            quote(
                "IWM",
                0.20,
                Provenance(source="Yahoo Finance", observed_at=NOW - timedelta(days=2)),
            ),
        ),
        account(stocks=100.0),
    )

    assert measured is not None
    assert measured.reading == degraded


def test_the_score_uses_the_same_violent_threshold_as_a_security() -> None:
    """
    An account and a security moving 60% a year are both moving 60% a
    year. Where the line between calm and violent sits is a judgement
    this platform makes once.
    """

    measured = MarketRiskService().measure(
        market(*crypto(RiskSignalService.VIOLENT)),
        account(crypto_pct=100.0),
    )

    assert measured is not None
    assert MarketRiskService.risk_score(measured) == 1.0

    half = replace(measured, volatility=RiskSignalService.VIOLENT / 2)

    assert MarketRiskService.risk_score(half) == 0.5


def test_a_market_more_violent_than_violent_is_still_bounded() -> None:
    measured = MarketRiskService().measure(
        market(*crypto(1.40)),
        account(crypto_pct=100.0),
    )

    assert measured is not None
    assert MarketRiskService.risk_score(measured) == 1.0
