from app.domain.policy_assessment import PolicyAssessment
from app.services.committees.policy_committee import (
    PolicyCommittee,
)


def test_aligned_policy_votes_buy() -> None:
    assessment = PolicyAssessment(
        aligned=True,
        status="ALIGNED",
        rationale=("The opportunity respects policy limits.",),
    )

    vote = PolicyCommittee().vote(
        assessment,
    )

    assert vote.recommendation == "BUY"
    assert vote.confidence == 95


def test_policy_violation_votes_hold() -> None:
    assessment = PolicyAssessment(
        aligned=False,
        status="VIOLATION",
        rationale=("Position exceeds policy limit.",),
    )

    vote = PolicyCommittee().vote(
        assessment,
    )

    assert vote.recommendation == "HOLD"
    assert vote.confidence == 100
