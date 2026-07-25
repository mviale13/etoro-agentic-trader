from app.domain.committee_decision import CommitteeDecision
from app.domain.committee_opinion import CommitteeOpinion
from app.renderers.committee_renderer import CommitteeRenderer


def test_committee_renderer(capsys):
    decision = CommitteeDecision(
        recommendation="BUY",
        confidence=82,
        buy_votes=2,
        hold_votes=1,
        sell_votes=0,
        opinions=(
            CommitteeOpinion(
                member="Momentum",
                vote="BUY",
                confidence=82,
                rationale="Strong trend.",
            ),
            CommitteeOpinion(
                member="Risk",
                vote="HOLD",
                confidence=70,
                rationale="Elevated volatility.",
            ),
            CommitteeOpinion(
                member="Value",
                vote="BUY",
                confidence=90,
                rationale="Attractive valuation.",
            ),
        ),
    )

    CommitteeRenderer.render(decision)

    output = capsys.readouterr().out

    assert "Investment Committee" in output
    assert "BUY" in output
    assert "Momentum" in output
    assert "Risk" in output
    assert "Value" in output
