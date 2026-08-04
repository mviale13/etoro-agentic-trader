from app.domain.committee_vote import CommitteeVote
from app.services.executive_board_service import (
    ExecutiveBoardService,
)


def test_weighted_majority_buy() -> None:
    votes = (
        CommitteeVote(
            committee="Portfolio",
            recommendation="BUY",
            confidence=90,
            weight=0.3,
            rationale="Cash is above target.",
        ),
        CommitteeVote(
            committee="Market",
            recommendation="BUY",
            confidence=80,
            weight=0.3,
            rationale="Market conditions are supportive.",
        ),
        CommitteeVote(
            committee="Opportunity",
            recommendation="HOLD",
            confidence=65,
            weight=0.4,
            rationale="The opportunity needs more evidence.",
        ),
    )

    decision = ExecutiveBoardService().decide(
        votes,
    )

    assert decision.recommendation == "BUY"
    assert decision.confidence == 85


def test_highest_weight_recommendation_wins() -> None:
    votes = (
        CommitteeVote(
            committee="Portfolio",
            recommendation="BUY",
            confidence=95,
            weight=0.2,
            rationale="Cash is available.",
        ),
        CommitteeVote(
            committee="Risk",
            recommendation="HOLD",
            confidence=80,
            weight=0.5,
            rationale="Risk is elevated.",
        ),
        CommitteeVote(
            committee="Market",
            recommendation="BUY",
            confidence=75,
            weight=0.3,
            rationale="Market conditions are supportive.",
        ),
    )

    decision = ExecutiveBoardService().decide(
        votes,
    )

    assert decision.recommendation == "HOLD"
    assert decision.confidence == 80


def test_no_votes_defaults_to_hold() -> None:
    decision = ExecutiveBoardService().decide(
        (),
    )

    assert decision.recommendation == "HOLD"
    assert decision.confidence == 0
