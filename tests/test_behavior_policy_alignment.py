"""Policy alignment is measured, not assumed."""

from dataclasses import replace

from app.application.brain.reasoning.behavior_analyst import BehaviorAnalyst
from app.application.brain.reasoning.reasoning_service import ReasoningService
from app.brain import Brain, BrainBuilder
from app.domain.investment_policy import (
    AllocationTarget,
    InvestmentConstraints,
    InvestmentPolicy,
)
from tests.test_brain_context import (
    make_market,
    make_policy,
    make_portfolio,
)


def make_brain(
    *,
    cash: float = 20.0,
    largest_position_pct: float = 18.0,
    largest_position: str | None = "MSFT",
    policy: InvestmentPolicy | None = None,
) -> Brain:
    base = make_portfolio()

    portfolio = replace(
        base,
        allocation=replace(base.allocation, cash=cash),
        largest_position=largest_position,
        largest_position_pct=largest_position_pct,
    )

    return BrainBuilder(
        portfolio=portfolio,
        market=make_market(),
        investment_policy=policy or make_policy(),
    ).build()


def policy_with(
    *,
    max_single_position: float = 20.0,
    target_cash: float = 15.0,
    rebalance_threshold: float = 5.0,
) -> InvestmentPolicy:
    return InvestmentPolicy(
        risk_profile="balanced",
        target=AllocationTarget(
            stocks=50.0,
            etfs=25.0,
            crypto=10.0,
            cash=target_cash,
        ),
        constraints=InvestmentConstraints(
            max_single_position=max_single_position,
            max_crypto=15.0,
            rebalance_threshold=rebalance_threshold,
        ),
    )


def test_a_compliant_portfolio_is_fully_aligned() -> None:
    brain = make_brain(
        cash=15.0,
        largest_position_pct=10.0,
        policy=policy_with(),
    )

    assessment = BehaviorAnalyst().assess(brain)

    assert assessment.policy_alignment_score == 1.0
    assert not assessment.observed_biases


def test_breaching_the_position_limit_reduces_alignment() -> None:
    compliant = BehaviorAnalyst().assess(
        make_brain(cash=15.0, largest_position_pct=10.0, policy=policy_with())
    )

    breaching = BehaviorAnalyst().assess(
        make_brain(cash=15.0, largest_position_pct=30.0, policy=policy_with())
    )

    assert breaching.policy_alignment_score < compliant.policy_alignment_score
    assert "Largest position exceeds the policy limit" in breaching.observed_biases


def test_cash_drift_beyond_the_rebalance_band_reduces_alignment() -> None:
    within_band = BehaviorAnalyst().assess(
        make_brain(cash=18.0, largest_position_pct=10.0, policy=policy_with())
    )

    drifted = BehaviorAnalyst().assess(
        make_brain(cash=90.0, largest_position_pct=10.0, policy=policy_with())
    )

    assert drifted.policy_alignment_score < within_band.policy_alignment_score
    assert (
        "Cash allocation has drifted beyond its rebalance band"
        in drifted.observed_biases
    )


def test_alignment_cites_the_limit_it_measured_against() -> None:
    assessment = BehaviorAnalyst().assess(
        make_brain(largest_position_pct=45.0, policy=policy_with())
    )

    descriptions = " ".join(item.description for item in assessment.evidence)

    # The investor can see the actual figure and the limit it breached.
    assert "45.0%" in descriptions
    assert "20.0%" in descriptions


def test_alignment_score_stays_within_bounds() -> None:
    assessment = BehaviorAnalyst().assess(
        make_brain(
            cash=100.0,
            largest_position_pct=99.0,
            policy=policy_with(),
        )
    )

    assert 0.0 <= assessment.policy_alignment_score <= 1.0


def test_reasoning_produces_all_five_assessments() -> None:
    snapshot = ReasoningService().reason(make_brain())

    assert snapshot.portfolio is not None
    assert snapshot.market is not None
    assert snapshot.risk is not None
    assert snapshot.behavior is not None
    assert snapshot.opportunity is not None


def test_opportunity_reflects_policy_alignment() -> None:
    """Behaviour feeds the opportunity synthesis, not just the brief."""

    aligned = ReasoningService().reason(
        make_brain(cash=15.0, largest_position_pct=10.0, policy=policy_with())
    )

    breaching = ReasoningService().reason(
        make_brain(cash=15.0, largest_position_pct=60.0, policy=policy_with())
    )

    assert (
        breaching.opportunity.portfolio_fit_score
        < aligned.opportunity.portfolio_fit_score
    )
