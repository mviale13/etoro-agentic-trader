from datetime import datetime

from app.analysts.market.equity_trend_analyst import EquityTrendAnalyst
from app.domain.equity_trend_opinion import EquityTrendVerdict
from app.domain.market_facts import MarketFact, MarketFacts


def quote(
    symbol: str,
    change_percent: float,
) -> MarketFact:
    timestamp = datetime.now()

    return MarketFact(
        symbol=symbol,
        name=symbol,
        price=100.0,
        change_percent=change_percent,
        source="test",
        as_of=timestamp,
    )


def market(
    *,
    spy: float | None,
    qqq: float | None,
    iwm: float | None,
) -> MarketFacts:
    timestamp = datetime.now()
    instruments: list[MarketFact] = []

    if spy is not None:
        instruments.append(quote("SPY", spy))

    if qqq is not None:
        instruments.append(quote("QQQ", qqq))

    if iwm is not None:
        instruments.append(quote("IWM", iwm))

    return MarketFacts(
        instruments=tuple(instruments),
        vix=None,
        source="test",
        as_of=timestamp,
    )


def test_bullish_equity_trend() -> None:
    opinion = EquityTrendAnalyst().analyze(
        market(
            spy=1.8,
            qqq=2.1,
            iwm=1.2,
        )
    )

    assert opinion.score == 100
    assert opinion.confidence == 1.0
    assert opinion.verdict is EquityTrendVerdict.BULLISH
    assert opinion.evidence == (
        "SPY changed 1.8%.",
        "QQQ changed 2.1%.",
        "IWM changed 1.2%.",
    )
    assert opinion.uncertainty == ()


def test_neutral_equity_trend() -> None:
    opinion = EquityTrendAnalyst().analyze(
        market(
            spy=0.2,
            qqq=-0.1,
            iwm=0.4,
        )
    )

    assert opinion.score == 63
    assert opinion.confidence == 1.0
    assert opinion.verdict is EquityTrendVerdict.NEUTRAL


def test_bearish_equity_trend() -> None:
    opinion = EquityTrendAnalyst().analyze(
        market(
            spy=-2.1,
            qqq=-1.5,
            iwm=-2.4,
        )
    )

    assert opinion.score == 0
    assert opinion.confidence == 1.0
    assert opinion.verdict is EquityTrendVerdict.BEARISH


def test_partial_equity_trend_data_reduces_confidence() -> None:
    opinion = EquityTrendAnalyst().analyze(
        market(
            spy=1.5,
            qqq=None,
            iwm=None,
        )
    )

    assert opinion.score == 100
    assert opinion.confidence == 1 / 3
    assert opinion.verdict is EquityTrendVerdict.BULLISH
    assert opinion.evidence == ("SPY changed 1.5%.",)
    assert opinion.uncertainty == (
        "QQQ daily change data is unavailable.",
        "IWM daily change data is unavailable.",
    )


def test_missing_equity_trend_data_is_unknown() -> None:
    opinion = EquityTrendAnalyst().analyze(
        market(
            spy=None,
            qqq=None,
            iwm=None,
        )
    )

    assert opinion.score == 50
    assert opinion.confidence == 0.0
    assert opinion.verdict is EquityTrendVerdict.UNKNOWN
    assert opinion.evidence == ()
    assert opinion.uncertainty == (
        "SPY daily change data is unavailable.",
        "QQQ daily change data is unavailable.",
        "IWM daily change data is unavailable.",
    )
