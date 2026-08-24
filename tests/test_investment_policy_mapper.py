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
            "target_stocks_pct": 40,
            "target_etfs_pct": 15,
            "target_crypto_pct": 25,
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

    # Every target is the investor's own. All three non-cash targets
    # were hardcoded to zero here until the owner's ruling of
    # 2026-08-24, so the strategy page showed 0/0/0/5 and totalled 5%.
    assert policy.target.stocks == 40
    assert policy.target.etfs == 15
    assert policy.target.crypto == 25
    assert (
        policy.target.stocks
        + policy.target.etfs
        + policy.target.crypto
        + policy.target.cash
    ) == 100
    assert policy.constraints.max_single_position == 15
    assert policy.constraints.max_crypto == 25
    assert policy.constraints.rebalance_threshold == 5


def test_the_investors_own_loss_tolerance_reaches_the_policy() -> None:
    """
    The one figure the strategy collects about losses rather than about
    allocations. It was asked for, checked for completeness, and then read
    by nothing — so the account's drawdown had no yardstick but a default.
    """

    strategy = complete_strategy()
    strategy["objectives"] = {"maximum_acceptable_drawdown_pct": 20}

    policy = InvestmentPolicyMapper().map(strategy)

    assert policy.constraints.max_drawdown == 20.0


def test_an_unstated_tolerance_is_absent_rather_than_assumed() -> None:
    """Saying nothing is not the same as accepting any loss at all."""

    unstated = InvestmentPolicyMapper().map(complete_strategy())

    assert unstated.constraints.max_drawdown is None

    strategy = complete_strategy()
    strategy["objectives"] = {"maximum_acceptable_drawdown_pct": ""}

    assert InvestmentPolicyMapper().map(strategy).constraints.max_drawdown is None


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
