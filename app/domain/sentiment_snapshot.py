from dataclasses import dataclass


@dataclass(frozen=True)
class SentimentSnapshot:
    score: int
    label: str
    source: str
