from dataclasses import dataclass


@dataclass(frozen=True)
class CommitteePerformance:
    recommendations: int
    completed: int
    successful: int
    accuracy: int
