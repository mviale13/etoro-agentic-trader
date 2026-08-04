from dataclasses import dataclass


@dataclass(frozen=True)
class LearningInsight:
    member: str
    recommendation: str
    reason: str
