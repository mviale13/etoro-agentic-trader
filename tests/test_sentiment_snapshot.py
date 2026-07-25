from app.domain.sentiment_snapshot import SentimentSnapshot


def test_sentiment_snapshot():
    sentiment = SentimentSnapshot(
        score=72,
        label="Greed",
        source="Alternative.me",
    )

    assert sentiment.score == 72
    assert sentiment.label == "Greed"
    assert sentiment.source == "Alternative.me"
