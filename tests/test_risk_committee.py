from app.domain.risk_assessment import RiskAssessment
from app.services.committees.risk_committee import (
    RiskCommittee,
)


def test_high_risk_votes_hold() -> None:
    assessment = RiskAssessment(
        overall="HIGH",
        market="HIGH",
        concentration="LOW",
        liquidity="LOW",
        policy="UNKNOWN",
        rationale=("Market volatility is elevated.",),
    )

    vote = RiskCommittee().vote(
        assessment,
    )

    assert vote.recommendation == "HOLD"
    assert vote.confidence == 90
    assert "Market volatility is elevated." in vote.evidence


def test_low_risk_votes_buy() -> None:
    assessment = RiskAssessment(
        overall="LOW",
        market="LOW",
        concentration="LOW",
        liquidity="LOW",
        policy="UNKNOWN",
        rationale=(),
    )

    vote = RiskCommittee().vote(
        assessment,
    )

    assert vote.recommendation == "BUY"
    assert vote.confidence == 75
