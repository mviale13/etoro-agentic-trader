from app.domain.investment_policy import (
    AllocationTarget,
    InvestmentConstraints,
    InvestmentPolicy,
)
from app.domain.policy_analysis import AllocationDifference
from app.domain.portfolio_snapshot import (
    Allocation,
    PortfolioSnapshot,
)
from app.services.policy_analyzer import PolicyAnalyzer


def test_policy_analysis_detects_non_compliance():
    portfolio = PortfolioSnapshot(
        allocation=Allocation(
            stocks=40,
            etfs=20,
            crypto=30,
            cash=10,
            unclassified=0,
        ),
        total_value=100000,
        positions=5,
        largest_position=None,
        largest_position_pct=0,
        risk_flags=(),
    )

    policy = InvestmentPolicy(
        risk_profile="moderate",
        target=AllocationTarget(
            stocks=60,
            etfs=20,
            crypto=10,
            cash=10,
        ),
        constraints=InvestmentConstraints(
            max_single_position=15,
            max_crypto=20,
            rebalance_threshold=5,
        ),
    )

    analysis = PolicyAnalyzer().analyze(
        portfolio,
        policy,
    )

    assert analysis.compliant is False
    assert analysis.stocks.difference == -20
    assert analysis.crypto.difference == 20