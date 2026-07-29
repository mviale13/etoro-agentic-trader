from datetime import datetime

from app.analysts.market.market_breadth_analyst import MarketBreadthAnalyst
from app.domain.market_breadth_opinion import MarketBreadthVerdict
from app.domain.market_facts import MarketFact, MarketFacts


def quote(
    symbol: str,
    change_percent: float,
) -> MarketFact:
    now = datetime.now()

    return MarketFact(
        symbol=symbol,
        name=symbol,
        price=100.0,
        change_percent=change_percent,
        source="test",
        as_of=now,
    )


def market(
    *,
    spy: float | None,
    qqq: float | None,
    iwm: float | None,
    dia: float | None,
) -> MarketFacts:
    instruments: list[MarketFact] = []

    if spy is not None:
        instruments.append(quote("SPY", spy))

    if qqq is not None:
        instruments.append(quote("QQQ", qqq))

    if iwm is not None:
        instruments.append(quote("IWM", iwm))

    if dia is not None:
        instruments.append(quote("DIA", dia))

    now = datetime.now()

    return MarketFacts(
        instruments=tuple(instruments),
        vix=None,
        source="test",
        as_of=now,
    )


def test_strong_market_breadth() -> None:
    opinion = MarketBreadthAnalyst().analyze(
        market(
            spy=1.0,
            qqq=0.8,
            iwm=1.5,
            dia=0.6,
        )
    )

    assert opinion.score == 100
    assert opinion.confidence == 1.0
    assert opinion.verdict is MarketBreadthVerdict.STRONG


def test_mixed_market_breadth() -> None:
    opinion = MarketBreadthAnalyst().analyze(
        market(
            spy=1.0,
            qqq=0.8,
            iwm=-0.6,
            dia=-0.3,
        )
    )

    assert opinion.score == 50
    assert opinion.confidence == 1.0
    assert opinion.verdict is MarketBreadthVerdict.MIXED


def test_weak_market_breadth() -> None:
    opinion = MarketBreadthAnalyst().analyze(
        market(
            spy=-1.0,
            qqq=-0.8,
            iwm=-1.5,
            dia=-0.6,
        )
    )

    assert opinion.score == 0
    assert opinion.confidence == 1.0
    assert opinion.verdict is MarketBreadthVerdict.WEAK


def test_partial_market_breadth() -> None:
    opinion = MarketBreadthAnalyst().analyze(
        market(
            spy=1.0,
            qqq=None,
            iwm=None,
            dia=None,
        )
    )

    assert opinion.score == 100
    assert opinion.confidence == 0.25
    assert opinion.verdict is MarketBreadthVerdict.STRONG


def test_unknown_market_breadth() -> None:
    opinion = MarketBreadthAnalyst().analyze(
        market(
            spy=None,
            qqq=None,
            iwm=None,
            dia=None,
        )
    )

    assert opinion.score == 50
    assert opinion.confidence == 0.0
    assert opinion.verdict is MarketBreadthVerdict.UNKNOWN
