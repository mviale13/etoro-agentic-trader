from dataclasses import dataclass


@dataclass(frozen=True)
class SentimentSnapshot:
    fear_greed: int
    label: str
