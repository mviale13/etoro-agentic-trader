from dataclasses import dataclass


@dataclass(frozen=True)
class CommitteeMemberPerformance:
    member: str
    completed: int
    successful: int
    accuracy: int
