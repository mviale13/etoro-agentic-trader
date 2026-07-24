from app.domain.sentiment_snapshot import SentimentSnapshot


class FearGreedProvider:
    async def snapshot(self) -> SentimentSnapshot:
        """
        Temporary deterministic implementation.

        This will later be replaced by a real API call.
        """
        return SentimentSnapshot(
            fear_greed=72,
            label="Greed",
        )
