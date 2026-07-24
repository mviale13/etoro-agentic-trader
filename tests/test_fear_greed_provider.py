import asyncio

from app.providers.fear_greed_provider import FearGreedProvider


def test_provider_returns_snapshot():
    snapshot = asyncio.run(FearGreedProvider().snapshot())

    assert snapshot.fear_greed == 72
    assert snapshot.label == "Greed"
