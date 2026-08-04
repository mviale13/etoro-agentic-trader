"""What the capacity analyst can say about the account's room to act."""

from dataclasses import replace

from app.application.brain.reasoning.capacity_analyst import CapacityAnalyst
from app.brain import Brain, BrainBuilder
from app.domain.investment_policy import InvestmentPolicy
from app.domain.portfolio_snapshot import PortfolioSnapshot
from tests.test_brain_context import make_market, make_policy, make_portfolio


def make_brain(
    portfolio: PortfolioSnapshot | None = None,
    policy: InvestmentPolicy | None = None,
) -> Brain:
    return BrainBuilder(
        portfolio=portfolio or make_portfolio(),
        market=make_market(),
        investment_policy=policy or make_policy(),
    ).build()


def test_funding_room_is_the_cash_above_the_policy_target() -> None:
    """20% cash against a 15% target leaves 5 points, $5,000, to deploy."""

    capacity = CapacityAnalyst().assess(make_brain())

    assert capacity.cash_actual_pct == 20.0
    assert capacity.cash_target_pct == 15.0
    assert capacity.funding_room_pct == 5.0
    assert capacity.funding_room_usd == 5_000.0


def test_an_account_at_its_cash_target_has_no_funding_room() -> None:
    """At or below target, room is a measured zero — not an absence."""

    portfolio = make_portfolio()
    portfolio = replace(
        portfolio,
        allocation=replace(portfolio.allocation, cash=10.0),
    )

    capacity = CapacityAnalyst().assess(make_brain(portfolio=portfolio))

    assert capacity.funding_room_pct == 0.0
    assert capacity.funding_room_usd == 0.0


def test_a_policy_without_a_usable_cash_target_leaves_room_unmeasured() -> None:
    policy = make_policy()
    policy = replace(policy, target=replace(policy.target, cash=100.0))

    capacity = CapacityAnalyst().assess(make_brain(policy=policy))

    assert capacity.cash_target_pct is None
    assert capacity.funding_room_pct is None
    assert capacity.funding_room_usd is None
    assert any("cash target" in item for item in capacity.unmeasured)


def test_single_position_headroom_is_the_signed_distance_to_the_limit() -> None:
    """MSFT at 18% under a 20% limit has 2 points of headroom."""

    capacity = CapacityAnalyst().assess(make_brain())

    assert capacity.single_position_limit_pct == 20.0
    assert capacity.largest_position == "MSFT"
    assert capacity.largest_position_pct == 18.0
    assert capacity.single_position_headroom_pct == 2.0


def test_a_holding_over_its_limit_is_a_measured_breach_not_a_zero() -> None:
    portfolio = replace(make_portfolio(), largest_position_pct=26.0)

    capacity = CapacityAnalyst().assess(make_brain(portfolio=portfolio))

    assert capacity.single_position_headroom_pct == -6.0


def test_an_empty_account_has_the_whole_limit_ahead_of_it() -> None:
    portfolio = replace(
        make_portfolio(),
        positions=0,
        largest_position=None,
        largest_position_pct=0.0,
    )

    capacity = CapacityAnalyst().assess(make_brain(portfolio=portfolio))

    assert capacity.largest_position is None
    assert capacity.largest_position_pct is None
    assert capacity.single_position_headroom_pct == 20.0


def test_crypto_headroom_is_measured_against_the_policy_ceiling() -> None:
    """10% crypto under a 15% ceiling leaves 5 points of room."""

    capacity = CapacityAnalyst().assess(make_brain())

    assert capacity.crypto_limit_pct == 15.0
    assert capacity.crypto_actual_pct == 10.0
    assert capacity.crypto_headroom_pct == 5.0


def test_an_unclassified_account_leaves_crypto_room_unmeasured() -> None:
    """A ceiling compared against a partly-identified portfolio lies."""

    portfolio = make_portfolio()
    portfolio = replace(
        portfolio,
        allocation=replace(
            portfolio.allocation,
            stocks=45.0,
            unclassified=5.0,
        ),
    )

    capacity = CapacityAnalyst().assess(make_brain(portfolio=portfolio))

    assert capacity.crypto_limit_pct == 15.0
    assert capacity.crypto_actual_pct is None
    assert capacity.crypto_headroom_pct is None
    assert any("unclassified" in item for item in capacity.unmeasured)


def test_a_valueless_account_states_room_in_points_but_not_dollars() -> None:
    portfolio = replace(make_portfolio(), total_value=0.0)

    capacity = CapacityAnalyst().assess(make_brain(portfolio=portfolio))

    assert capacity.funding_room_pct == 5.0
    assert capacity.funding_room_usd is None
    assert any("dollars" in item for item in capacity.unmeasured)
