from app.domain.sentiment_snapshot import SentimentSnapshot


def test_sentiment_snapshot():
    sentiment = SentimentSnapshot(
        fear_greed=72,
        label="Greed",
    )

    assert sentiment.fear_greed == 72
    assert sentiment.label == "Greed"
