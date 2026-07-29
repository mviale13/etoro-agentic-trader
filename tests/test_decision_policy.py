from app.application.executive.decision_policy import DecisionPolicy


def test_decision_policy_exists() -> None:
    assert DecisionPolicy() is not None
