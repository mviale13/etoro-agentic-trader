from app.domain.investment_policy import (
    AllocationTarget,
    InvestmentConstraints,
    InvestmentPolicy,
)
from app.domain.portfolio_snapshot import (
    Allocation,
    PortfolioSnapshot,
)
from app.services.policy_analyzer import PolicyAnalyzer


def build_policy() -> InvestmentPolicy:
    return InvestmentPolicy(
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


def test_policy_analysis_detects_non_compliance():
    portfolio = PortfolioSnapshot(
        allocation=Allocation(
            stocks=40,
            etfs=20,
            crypto=30,
            cash=10,
            unclassified=0,
        ),
        total_value=100_000,
        positions=5,
        largest_position=None,
        largest_position_pct=0,
        risk_flags=(),
    )

    analysis = PolicyAnalyzer().analyze(
        portfolio,
        build_policy(),
    )

    stocks = analysis.allocation("stocks")
    crypto = analysis.allocation("crypto")

    assert analysis.compliant is False
    assert stocks is not None
    assert stocks.difference == -20
    assert crypto is not None
    assert crypto.difference == 20


def test_policy_analysis_detects_compliance():
    portfolio = PortfolioSnapshot(
        allocation=Allocation(
            stocks=58,
            etfs=22,
            crypto=10,
            cash=10,
            unclassified=0,
        ),
        total_value=100_000,
        positions=5,
        largest_position=None,
        largest_position_pct=0,
        risk_flags=(),
    )

    analysis = PolicyAnalyzer().analyze(
        portfolio,
        build_policy(),
    )

    assert analysis.compliant is True


def test_largest_deviation_returns_most_off_target_asset():
    portfolio = PortfolioSnapshot(
        allocation=Allocation(
            stocks=40,
            etfs=20,
            crypto=30,
            cash=10,
            unclassified=0,
        ),
        total_value=100_000,
        positions=5,
        largest_position=None,
        largest_position_pct=0,
        risk_flags=(),
    )

    analysis = PolicyAnalyzer().analyze(
        portfolio,
        build_policy(),
    )

    largest = analysis.largest_deviation()

    assert largest is not None
    assert largest.asset == "stocks"
    assert abs(largest.difference) == 20