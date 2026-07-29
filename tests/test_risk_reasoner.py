from app.application.brain.reasoning.risk_reasoner import RiskReasoner


def test_risk_reasoner_exists() -> None:
    assert RiskReasoner() is not None
