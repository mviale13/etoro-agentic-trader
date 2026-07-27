from app.domain.committee_decision import CommitteeDecision
from app.services.recommendation_coach import RecommendationCoach


def decision(vote: str):
    return CommitteeDecision(
        recommendation=vote,
        confidence=87,
        buy_votes=3,
        hold_votes=1,
        sell_votes=1,
        opinions=(),
    )


def test_buy():
    explanation = RecommendationCoach().explain(
        "MSFT",
        decision("BUY"),
    )

    assert "MSFT" in explanation
    assert "BUY" in explanation
    assert "87%" in explanation


def test_sell():
    explanation = RecommendationCoach().explain(
        "AAPL",
        decision("SELL"),
    )

    assert "AAPL" in explanation
    assert "SELL" in explanation
