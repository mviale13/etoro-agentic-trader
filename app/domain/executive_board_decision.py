from pydantic import BaseModel, ConfigDict

from app.domain.committee_vote import CommitteeVote


class ExecutiveBoardDecision(BaseModel):
    """Legacy weighted-voting result produced by the Executive Board."""

    model_config = ConfigDict(frozen=True)

    recommendation: str
    confidence: int
    votes: tuple[CommitteeVote, ...] = ()
    rationale: str
