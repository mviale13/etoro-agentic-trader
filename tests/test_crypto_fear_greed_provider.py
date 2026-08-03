"""Reading the sentiment index that the platform credits to a real service."""

import asyncio
from datetime import UTC, datetime, timedelta

from app.domain.market_snapshot import MarketSnapshot
from app.providers.crypto_fear_greed_provider import CryptoFearGreedProvider
from app.services.market_intelligence_service import MarketIntelligenceService

PAYLOAD = {
    "data": [
        {
            "value": "28",
            "value_classification": "Fear",
            "timestamp": "1785715200",
        }
    ],
    "metadata": {"error": None},
}


class Provider(CryptoFearGreedProvider):
    """The real provider with the network call replaced, and counted."""

    def __init__(self, payload: object, tmp_path, fail: bool = False) -> None:
        from app.infrastructure.cache.json_cache import JsonCache

        super().__init__(cache=JsonCache(str(tmp_path)))
        self.calls = 0
        self._payload = payload
        self._fail = fail

    def _fetch(self) -> object:
        self.calls += 1

        if self._fail:
            raise OSError("the index could not be reached")

        return self._payload


def test_the_published_reading_is_what_is_reported(tmp_path) -> None:
    """
    This returned a hardcoded 72, "Greed", over "Source: Alternative.me".

    The service is real and the number was not — on the day this was
    rewritten the published index read 28, "Fear". A citation is what tells
    an investor the figure can be trusted.
    """

    snapshot = asyncio.run(Provider(PAYLOAD, tmp_path).snapshot())

    assert snapshot is not None
    assert snapshot.score == 28
    assert snapshot.label == "Fear"
    assert snapshot.source == "Alternative.me"
    assert snapshot.observed_at == datetime(2026, 8, 3, tzinfo=UTC)


def test_an_unreachable_index_reports_nothing(tmp_path) -> None:
    """Not the last mood it happened to see, which would read as current."""

    assert asyncio.run(Provider(PAYLOAD, tmp_path, fail=True).snapshot()) is None


def test_a_response_that_is_not_a_reading_is_not_read_as_one(tmp_path) -> None:
    for payload in ({}, {"data": []}, {"data": [{"value": "not a number"}]}):
        assert asyncio.run(Provider(payload, tmp_path).snapshot()) is None


def test_the_index_is_read_once_an_hour_not_once_a_question(tmp_path) -> None:
    provider = Provider(PAYLOAD, tmp_path)

    asyncio.run(provider.snapshot())
    asyncio.run(provider.snapshot())

    assert provider.calls == 1


def test_a_stale_reading_is_re_read_rather_than_replayed(tmp_path) -> None:
    provider = Provider(PAYLOAD, tmp_path)
    provider._ttl = timedelta(seconds=0)

    asyncio.run(provider.snapshot())
    asyncio.run(provider.snapshot())

    assert provider.calls == 2


def market(mood: str) -> MarketSnapshot:
    return MarketSnapshot(
        quotes=(),
        market_mood=mood,
        volatility="medium",
        summary="",
        timestamp=datetime.now(UTC),
    )


def test_an_outlook_without_sentiment_says_what_it_rests_on() -> None:
    """
    Two readings agreeing is what earns the higher confidence here.

    With sentiment unavailable there is nothing to agree with, so claiming
    a confirmation would report an observation never made.
    """

    intelligence = MarketIntelligenceService().build(market("negative"), None)

    assert intelligence.sentiment is None
    assert intelligence.outlook == "BEARISH"
    assert intelligence.confidence == 50
    assert "rests on market conditions alone" in intelligence.summary
