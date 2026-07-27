from dataclasses import dataclass


@dataclass(frozen=True)
class CommitteeStatistics:
    recommendations: int

    buy: int

    hold: int

    sell: int

    average_confidence: int
