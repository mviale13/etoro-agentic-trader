from app.domain.sentiment_snapshot import SentimentSnapshot


class CryptoFearGreedProvider:
    async def snapshot(self) -> SentimentSnapshot:
        return SentimentSnapshot(
            score=72,
            label="Greed",
            source="Alternative.me",
        )
