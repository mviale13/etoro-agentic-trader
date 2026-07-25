import asyncio

from app.providers.crypto_fear_greed_provider import (
    CryptoFearGreedProvider,
)


def test_provider_returns_snapshot():
    snapshot = asyncio.run(CryptoFearGreedProvider().snapshot())

    assert snapshot.score == 72
    assert snapshot.label == "Greed"
    assert snapshot.source == "Alternative.me"
