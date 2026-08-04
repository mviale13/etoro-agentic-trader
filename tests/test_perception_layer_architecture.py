"""Architecture tests for the MOVRvest perception layer."""

from app.application.brain.perception import (
    InvestorPerception,
    MarketPerception,
    MemoryPerception,
    PolicyPerception,
    PortfolioPerception,
)


def test_portfolio_perception_is_defined_in_perception_layer() -> None:
    assert PortfolioPerception.__module__ == (
        "app.application.brain.perception.portfolio_perception"
    )


def test_market_perception_is_defined_in_perception_layer() -> None:
    assert MarketPerception.__module__ == (
        "app.application.brain.perception.market_perception"
    )


def test_investor_perception_is_defined_in_perception_layer() -> None:
    assert InvestorPerception.__module__ == (
        "app.application.brain.perception.investor_perception"
    )


def test_policy_perception_is_defined_in_perception_layer() -> None:
    assert PolicyPerception.__module__ == (
        "app.application.brain.perception.policy_perception"
    )


def test_memory_perception_is_defined_in_perception_layer() -> None:
    assert MemoryPerception.__module__ == (
        "app.application.brain.perception.memory_perception"
    )
