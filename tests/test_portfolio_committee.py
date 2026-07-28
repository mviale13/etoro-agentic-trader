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
from app.services.committees.portfolio_committee import (
    PortfolioCommittee,
)


def test_buy_vote_when_cash_above_target() -> None:
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

    vote = PortfolioCommittee().vote(
        context,
    )

    assert vote.recommendation == "BUY"
