from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CommitteeVote:
    committee: str
    recommendation: str
    confidence: int
    weight: float
    rationale: str
    evidence: tuple[str, ...] = ()
