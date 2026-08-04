from app.domain.committee_member_weight import CommitteeMemberWeight
from app.domain.committee_opinion import CommitteeOpinion
from app.services.weighted_vote_service import (
    WeightedVoteService,
)


def test_scores():
    opinions = [
        CommitteeOpinion(
            member="Momentum",
            vote="BUY",
            confidence=90,
            rationale="",
        ),
        CommitteeOpinion(
            member="Risk",
            vote="SELL",
            confidence=80,
            rationale="",
        ),
    ]

    weights = [
        CommitteeMemberWeight(
            member="Momentum",
            accuracy=90,
            weight=1.2,
        ),
        CommitteeMemberWeight(
            member="Risk",
            accuracy=80,
            weight=0.8,
        ),
    ]

    scores = WeightedVoteService().score(
        opinions,
        weights,
    )

    assert scores["BUY"] == 108
    assert scores["SELL"] == 64
