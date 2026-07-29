from datetime import datetime

from app.analysts.trend_analyst import TrendAnalyst
from app.domain.market_facts import MarketFact, MarketFacts
from app.domain.trend_opinion import TrendVerdict


def quote(
    symbol: str,
    change: float,
) -> MarketFact:
    return MarketFact(
        symbol=symbol,
        name=symbol,
        price=100.0,
        change_percent=change,
        source="test",
        as_of=datetime.now(),
    )


def market(
    spy: float | None,
    qqq: float | None,
    iwm: float | None,
) -> MarketFacts:
    instruments = []

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
        as_of=datetime.now(),
    )


def test_bullish_market() -> None:
    opinion = TrendAnalyst().analyze(
        market(
            spy=1.8,
            qqq=2.1,
            iwm=1.2,
        )
    )

    assert opinion.score == 100
    assert opinion.confidence == 1.0
    assert opinion.verdict is TrendVerdict.BULLISH


def test_neutral_market() -> None:
    opinion = TrendAnalyst().analyze(
        market(
            spy=0.2,
            qqq=-0.1,
            iwm=0.4,
        )
    )

    assert opinion.verdict is TrendVerdict.NEUTRAL


def test_bearish_market() -> None:
    opinion = TrendAnalyst().analyze(
        market(
            spy=-2.1,
            qqq=-1.5,
            iwm=-2.4,
        )
    )

    assert opinion.verdict is TrendVerdict.BEARISH


def test_partial_market_data() -> None:
    opinion = TrendAnalyst().analyze(
        market(
            spy=1.5,
            qqq=None,
            iwm=None,
        )
    )

    assert opinion.confidence == 1 / 3


def test_missing_market_data() -> None:
    opinion = TrendAnalyst().analyze(
        market(
            spy=None,
            qqq=None,
            iwm=None,
        )
    )

    assert opinion.score is None
    assert opinion.confidence == 0.0
    assert opinion.verdict is TrendVerdict.UNKNOWN
