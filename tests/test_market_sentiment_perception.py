"""Sentiment reaching the Brain, and staying about what it describes."""

import asyncio
from datetime import UTC, datetime

from app.application.brain.perception.market_perception import MarketPerception
from app.application.brain.reasoning.market_analyst import MarketAnalyst
from app.brain import BrainBuilder
from app.domain.asset_class import AssetClass
from app.domain.market_snapshot import MarketData, MarketQuote, MarketSnapshot
from app.domain.provenance import Provenance
from app.domain.sentiment_snapshot import SentimentSnapshot
from tests.test_brain_context import make_policy, make_portfolio

NOW = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)


def reading() -> SentimentSnapshot:
    return SentimentSnapshot(
        score=28,
        label="Fear",
        subject=AssetClass.CRYPTO,
        reading=Provenance(source="Alternative.me", observed_at=NOW),
    )


class MarketStub:
    async def snapshot(self) -> MarketData:
        return MarketData(
            quotes=(
                MarketQuote(
                    symbol="SPY",
                    name="S&P 500 ETF",
                    price=600.0,
                    change_percent=1.2,
                    reading=Provenance(source="Yahoo Finance", observed_at=NOW),
                ),
            ),
            vix=16.0,
        )


class SentimentStub:
    def __init__(
        self,
        snapshot: SentimentSnapshot | None = None,
        failure: Exception | None = None,
    ) -> None:
        self._snapshot = snapshot
        self._failure = failure

    async def snapshot(self) -> SentimentSnapshot | None:
        if self._failure is not None:
            raise self._failure

        return self._snapshot


class ArchiveStub:
    """Records nothing. These tests are about the reading, not the record."""

    def record(self, snapshot: MarketSnapshot) -> object:
        return None


def perceive(sentiment: SentimentStub) -> MarketSnapshot:
    return asyncio.run(
        MarketPerception(
            provider=MarketStub(),
            sentiment_provider=sentiment,
            archive=ArchiveStub(),
        ).execute()
    )


def test_the_brain_can_finally_see_a_sentiment_reading() -> None:
    """
    It lived on the legacy committee path, where it set the outlook for
    the whole market, and the canonical pipeline could not see it at all.
    """

    market = perceive(SentimentStub(reading()))

    assert market.sentiment is not None
    assert market.sentiment.score == 28
    assert market.sentiment.subject is AssetClass.CRYPTO


def test_an_index_that_could_not_be_read_costs_the_reading_not_the_cycle() -> None:
    unread = perceive(SentimentStub(None))
    failed = perceive(SentimentStub(failure=OSError("the index is unreachable")))

    assert unread.sentiment is None
    assert failed.sentiment is None

    # The market itself still arrives.
    assert unread.quotes and failed.quotes


def test_sentiment_never_moves_the_market_scores() -> None:
    """
    The scores describe nine instruments; the reading describes one asset
    class. Folding one into the other lets a crypto mood move an equity
    reading.
    """

    without = MarketAnalyst().assess(brain(perceive(SentimentStub(None))))
    with_fear = MarketAnalyst().assess(brain(perceive(SentimentStub(reading()))))

    assert with_fear.momentum_score == without.momentum_score
    assert with_fear.volatility_score == without.volatility_score
    assert with_fear.trend == without.trend
    assert with_fear.regime == without.regime


def test_the_reading_reaches_reasoning_naming_what_it_describes() -> None:
    assessment = MarketAnalyst().assess(brain(perceive(SentimentStub(reading()))))

    stated = next(
        item for item in assessment.evidence if "sentiment" in item.description
    )

    assert stated.description == (
        "Crypto sentiment reads 28 (Fear), which describes crypto only."
    )

    # Cited to the service that published it, not to the snapshot.
    assert "Alternative.me" in stated.source


def brain(market: MarketSnapshot):
    return BrainBuilder(
        portfolio=make_portfolio(),
        market=market,
        investment_policy=make_policy(),
    ).build()
