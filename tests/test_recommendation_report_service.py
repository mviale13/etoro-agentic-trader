from app.domain.committee_decision import CommitteeDecision
from app.domain.committee_evidence import CommitteeEvidence
from app.domain.committee_opinion import CommitteeOpinion
from app.services.recommendation_report_service import (
    RecommendationReportService,
)


def test_render_report():
    opinion = CommitteeOpinion(
        member="Momentum",
        vote="BUY",
        confidence=90,
        rationale="Strong trend.",
        evidence=(
            CommitteeEvidence(
                title="Market outlook",
                value="BULLISH",
            ),
        ),
    )

    report = RecommendationReportService().render(
        symbol="MSFT",
        decision=CommitteeDecision(
            recommendation="BUY",
            confidence=90,
            buy_votes=1,
            hold_votes=0,
            sell_votes=0,
            opinions=(opinion,),
        ),
    )

    assert "Recommendation Report" in report
    assert "MSFT" in report
    assert "Momentum" in report
    assert "Market outlook" in report
