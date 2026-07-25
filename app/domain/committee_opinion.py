from dataclasses import dataclass


@dataclass(frozen=True)
class CommitteeOpinion:
    member: str
    vote: str
    confidence: int
    rationale: str
