from dataclasses import dataclass

from app.domain.committee_vote import CommitteeVote


@dataclass(frozen=True, slots=True)
class ExecutiveDecision:
    recommendation: str

    confidence: int

    votes: tuple[CommitteeVote, ...]

    rationale: str
