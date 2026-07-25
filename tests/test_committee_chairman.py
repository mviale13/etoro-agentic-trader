from app.committee.chairman import CommitteeChairman
from app.domain.committee_opinion import CommitteeOpinion


def opinion(vote: str, confidence: int):
    return CommitteeOpinion(
        member="Test",
        vote=vote,
        confidence=confidence,
        rationale="Because.",
    )


def test_majority_buy():
    decision = CommitteeChairman().decide(
        [
            opinion("BUY", 80),
            opinion("BUY", 90),
            opinion("SELL", 60),
        ]
    )

    assert decision.recommendation == "BUY"
    assert decision.confidence == 77

    assert decision.buy_votes == 2
    assert decision.sell_votes == 1
    assert decision.hold_votes == 0

    assert len(decision.opinions) == 3


def test_majority_hold():
    decision = CommitteeChairman().decide(
        [
            opinion("HOLD", 70),
            opinion("HOLD", 80),
            opinion("BUY", 90),
        ]
    )

    assert decision.recommendation == "HOLD"

    assert decision.buy_votes == 1
    assert decision.hold_votes == 2
    assert decision.sell_votes == 0
