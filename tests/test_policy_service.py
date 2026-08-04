from app.services.policy_service import PolicyService


def test_policy_loads():
    policy = PolicyService().load()

    assert policy.risk_profile == "moderate"
    assert policy.target.stocks == 60
    assert policy.target.crypto == 10
    assert policy.constraints.max_crypto == 20
