from datetime import UTC, datetime

from app.domain.decision import Decision
from app.domain.market_snapshot import MarketSnapshot
from app.domain.policy_analysis import (
    AllocationDifference,
    PolicyAnalysis,
)
from app.services.decision_engine import DecisionEngine


def build_market(mood: str) -> MarketSnapshot:
    return MarketSnapshot(
        quotes=(),
        market_mood=mood,
        volatility="medium",
        summary="Test market snapshot.",
        timestamp=datetime.now(UTC),
    )


def build_policy_analysis(
    *,
    compliant: bool,
) -> PolicyAnalysis:
    return PolicyAnalysis(
        allocations=(
            AllocationDifference(
                asset="stocks",
                current=60,
                target=60,
                difference=0,
            ),
            AllocationDifference(
                asset="etfs",
                current=20,
                target=20,
                difference=0,
            ),
            AllocationDifference(
                asset="crypto",
                current=10,
                target=10,
                difference=0,
            ),
            AllocationDifference(
                asset="cash",
                current=10,
                target=10,
                difference=0,
            ),
        ),
        compliant=compliant,
    )


def test_non_compliant_portfolio_requires_rebalance():
    decision = DecisionEngine().evaluate(
        build_policy_analysis(compliant=False),
        build_market("positive"),
    )

    assert isinstance(decision, Decision)
    assert decision.action == "REBALANCE"
    assert decision.priority == "HIGH"
    assert decision.confidence == 100
    assert decision.explanation == "Your portfolio is outside your investment policy."


def test_compliant_portfolio_and_negative_market_recommends_waiting():
    decision = DecisionEngine().evaluate(
        build_policy_analysis(compliant=True),
        build_market("negative"),
    )

    assert decision.action == "WAIT"
    assert decision.priority == "MEDIUM"
    assert decision.confidence == 90
    assert decision.explanation == "Markets are currently weak. Waiting is recommended."


def test_compliant_portfolio_and_positive_market_recommends_holding():
    decision = DecisionEngine().evaluate(
        build_policy_analysis(compliant=True),
        build_market("positive"),
    )

    assert decision.action == "HOLD"
    assert decision.priority == "LOW"
    assert decision.confidence == 85
    assert decision.explanation == "Your portfolio is aligned with your policy."
