from dataclasses import dataclass


@dataclass(frozen=True)
class CommitteeMemberStatistics:
    member: str

    recommendations: int

    buy: int

    hold: int

    sell: int

    average_confidence: int
