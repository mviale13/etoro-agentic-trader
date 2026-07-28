from typing import Any

import pytest

from app.services.investment_policy_mapper import (
    InvestmentPolicyMapper,
)


def complete_strategy() -> dict[str, Any]:
    return {
        "investment_preferences": {
            "investor_type": "long_term",
        },
        "portfolio_policy": {
            "target_cash_pct": 20,
            "maximum_single_position_pct": 15,
            "maximum_crypto_pct": 25,
        },
    }


def test_maps_questionnaire_to_policy() -> None:
    policy = InvestmentPolicyMapper().map(
        complete_strategy(),
    )

    assert policy.risk_profile == "long_term"
    assert policy.target.cash == 20
    assert policy.constraints.max_single_position == 15
    assert policy.constraints.max_crypto == 25
    assert policy.constraints.rebalance_threshold == 5


def test_requires_target_cash() -> None:
    strategy = complete_strategy()
    strategy["portfolio_policy"]["target_cash_pct"] = None

    with pytest.raises(
        ValueError,
        match="target_cash_pct",
    ):
        InvestmentPolicyMapper().map(
            strategy,
        )
