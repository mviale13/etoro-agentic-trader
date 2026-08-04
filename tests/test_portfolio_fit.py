"""Whether a security fits this portfolio — a question about the pair."""

from dataclasses import replace

from app.application.executive.portfolio_fit import PortfolioFit
from app.domain.investment_policy import (
    AllocationTarget,
    InvestmentConstraints,
    InvestmentPolicy,
)
from app.domain.portfolio_position import PortfolioPosition
from app.domain.portfolio_snapshot import Allocation, PortfolioSnapshot


def make_policy(
    cash_target: float = 5.0,
    max_single_position: float = 20.0,
) -> InvestmentPolicy:
    return InvestmentPolicy(
        risk_profile="balanced",
        target=AllocationTarget(
            stocks=50.0,
            etfs=25.0,
            crypto=20.0,
            cash=cash_target,
        ),
        constraints=InvestmentConstraints(
            max_single_position=max_single_position,
            max_crypto=65.0,
            rebalance_threshold=5.0,
        ),
    )


def make_portfolio(
    cash: float = 50.0,
    holdings: tuple[PortfolioPosition, ...] = (),
) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        allocation=Allocation(
            cash=cash,
            stocks=0.0,
            etfs=0.0,
            crypto=0.0,
            unclassified=100.0 - cash,
        ),
        total_value=100_000.0,
        positions=len(holdings),
        largest_position=holdings[0].symbol if holdings else None,
        largest_position_pct=0.0,
        risk_flags=(),
        holdings=holdings,
    )


def holding(symbol: str, market_value_usd: float) -> PortfolioPosition:
    return PortfolioPosition(
        symbol=symbol,
        quantity=1.0,
        invested_usd=market_value_usd,
        market_value_usd=market_value_usd,
        unrealized_pnl_usd=0.0,
    )


def test_fit_distinguishes_two_securities_in_the_same_portfolio() -> None:
    """
    The whole point, and what the old score could never do.

    Fit was computed from diversification and policy drift alone, so every
    candidate in a given cycle received an identical number and none could
    pass or fail on its own merits.
    """

    portfolio = make_portfolio(holdings=(holding("CROWDED", 19_000.0),))

    crowded = PortfolioFit().measure("CROWDED", portfolio, make_policy())
    fresh = PortfolioFit().measure("ROOMY", portfolio, make_policy())

    assert crowded is not None and fresh is not None
    assert crowded < fresh


def test_a_security_at_the_position_limit_has_no_room_left() -> None:
    portfolio = make_portfolio(holdings=(holding("FULL", 20_000.0),))

    fit = PortfolioFit().measure("FULL", portfolio, make_policy())

    assert fit is not None
    assert fit < 60


def test_an_unheld_security_has_the_whole_limit_available() -> None:
    fit = PortfolioFit().measure(
        "NEW",
        make_portfolio(cash=100.0),
        make_policy(),
    )

    assert fit == 100


def test_cash_above_its_target_is_room_to_act_not_a_reason_to_refuse() -> None:
    """
    This is the inversion that blocked every recommendation.

    The account sat 97% in cash against a 5% target. That drift was scored
    as a portfolio failing, folded into "fit", and used to refuse the only
    action that would have corrected it.
    """

    deployed = PortfolioFit().measure("NEW", make_portfolio(cash=5.0), make_policy())
    sitting = PortfolioFit().measure("NEW", make_portfolio(cash=97.0), make_policy())

    assert deployed is not None and sitting is not None
    assert sitting > deployed


def test_an_account_at_its_cash_target_has_nothing_spare_to_fund_with() -> None:
    """A new position would have to be funded by selling an existing one."""

    portfolio = make_portfolio(cash=5.0)

    assert PortfolioFit()._funding_room(portfolio, make_policy()) == 0.0


def test_fit_is_absent_rather_than_guessed_when_the_policy_states_no_limits() -> None:
    policy = replace(
        make_policy(),
        target=AllocationTarget(stocks=0.0, etfs=0.0, crypto=0.0, cash=100.0),
        constraints=InvestmentConstraints(
            max_single_position=0.0,
            max_crypto=0.0,
            rebalance_threshold=0.0,
        ),
    )

    assert PortfolioFit().measure("ANY", make_portfolio(), policy) is None


def test_an_empty_account_cannot_be_measured_for_concentration() -> None:
    portfolio = replace(make_portfolio(), total_value=0.0)

    assert PortfolioFit()._concentration_room("ANY", portfolio, make_policy()) is None


def test_crypto_fit_narrows_as_the_policy_ceiling_fills() -> None:
    """
    The policy caps crypto. Fit could not see it while nothing was classified.

    A ceiling compared against a partly-identified portfolio understates
    what is already held, so the term applies only to a fully classified
    account.
    """

    from app.domain.asset_class import AssetClass

    empty = make_portfolio(cash=50.0)
    loaded = replace(
        empty,
        allocation=replace(empty.allocation, crypto=60.0, unclassified=0.0),
    )

    room = PortfolioFit().measure("BTC", loaded, make_policy(), AssetClass.CRYPTO)
    without = PortfolioFit().measure("BTC", loaded, make_policy())

    assert room is not None and without is not None
    assert room < without


def test_an_unclassified_account_is_not_scored_against_the_crypto_ceiling() -> None:
    from app.domain.asset_class import AssetClass

    portfolio = make_portfolio(cash=50.0)

    assert portfolio.allocation.unclassified > 0
    assert (
        PortfolioFit()._asset_class_room(
            AssetClass.CRYPTO,
            portfolio,
            make_policy(),
        )
        is None
    )
