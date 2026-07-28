from types import SimpleNamespace
from typing import cast

from app.domain.brain_context import BrainContext
from app.domain.investment_policy import (
    AllocationTarget,
    InvestmentConstraints,
    InvestmentPolicy,
)
from app.domain.portfolio_snapshot import (
    Allocation,
    PortfolioSnapshot,
)
from app.services.reasoners.opportunity_reasoner import (
    OpportunityReasoner,
)


def test_generates_opportunity() -> None:
    portfolio = PortfolioSnapshot(
        allocation=Allocation(
            cash=100,
            stocks=0,
            etfs=0,
            crypto=0,
            unclassified=0,
        ),
        total_value=100000,
        total_value_eur=92000,
        positions=0,
        largest_position=None,
        largest_position_pct=0,
        risk_flags=(),
    )

    policy = InvestmentPolicy(
        risk_profile="long_term",
        target=AllocationTarget(
            stocks=0,
            etfs=0,
            crypto=0,
            cash=5,
        ),
        constraints=InvestmentConstraints(
            max_single_position=20,
            max_crypto=65,
            rebalance_threshold=5,
        ),
    )

    context = cast(
        BrainContext,
        SimpleNamespace(
            portfolio=portfolio,
            investment_policy=policy,
        ),
    )

    opportunities = OpportunityReasoner().analyze(
        context,
    )

    assert len(opportunities) == 1
    assert opportunities[0].symbol == "BTC"
    assert opportunities[0].action == "BUY"


def test_returns_no_opportunity_without_excess_cash() -> None:
    portfolio = PortfolioSnapshot(
        allocation=Allocation(
            cash=5,
            stocks=0,
            etfs=0,
            crypto=0,
            unclassified=95,
        ),
        total_value=100000,
        total_value_eur=92000,
        positions=1,
        largest_position="OTHER",
        largest_position_pct=95,
        risk_flags=(),
    )

    policy = InvestmentPolicy(
        risk_profile="long_term",
        target=AllocationTarget(
            stocks=0,
            etfs=0,
            crypto=0,
            cash=5,
        ),
        constraints=InvestmentConstraints(
            max_single_position=20,
            max_crypto=65,
            rebalance_threshold=5,
        ),
    )

    context = cast(
        BrainContext,
        SimpleNamespace(
            portfolio=portfolio,
            investment_policy=policy,
        ),
    )

    opportunities = OpportunityReasoner().analyze(
        context,
    )

    assert opportunities == []
