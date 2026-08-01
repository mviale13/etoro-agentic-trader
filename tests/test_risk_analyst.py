from app.application.brain.reasoning.risk_analyst import RiskAnalyst


def test_risk_analyst_exists() -> None:
    assert RiskAnalyst() is not None
