from dataclasses import dataclass


@dataclass(frozen=True)
class CommitteeMemberWeight:
    member: str
    weight: float
    accuracy: int
