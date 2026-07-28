from app.domain.investment_policy import (
    AllocationTarget,
    InvestmentConstraints,
    InvestmentPolicy,
)
from app.domain.opportunity_facts import OpportunityFacts
from app.services.policy_assessment_service import (
    PolicyAssessmentService,
)


def policy() -> InvestmentPolicy:
    return InvestmentPolicy(
        risk_profile="long_term",
        target=AllocationTarget(
            stocks=20,
            etfs=10,
            crypto=65,
            cash=5,
        ),
        constraints=InvestmentConstraints(
            max_single_position=20,
            max_crypto=65,
            rebalance_threshold=5,
        ),
    )


def test_crypto_opportunity_is_aligned() -> None:
    opportunity = OpportunityFacts(
        symbol="BTC",
        asset_type="crypto",
        current_price=100000,
        daily_change_percent=2,
        source="Yahoo Finance",
    )

    assessment = PolicyAssessmentService().assess(
        policy(),
        opportunity,
        proposed_position_pct=20,
        current_crypto_pct=0,
    )

    assert assessment.aligned is True
    assert assessment.status == "ALIGNED"


def test_rejects_position_above_limit() -> None:
    opportunity = OpportunityFacts(
        symbol="MSFT",
        asset_type="stock",
        current_price=500,
        daily_change_percent=1,
        source="Yahoo Finance",
    )

    assessment = PolicyAssessmentService().assess(
        policy(),
        opportunity,
        proposed_position_pct=25,
        current_crypto_pct=0,
    )

    assert assessment.aligned is False
    assert assessment.status == "VIOLATION"


def test_rejects_crypto_above_limit() -> None:
    opportunity = OpportunityFacts(
        symbol="BTC",
        asset_type="crypto",
        current_price=100000,
        daily_change_percent=2,
        source="Yahoo Finance",
    )

    assessment = PolicyAssessmentService().assess(
        policy(),
        opportunity,
        proposed_position_pct=20,
        current_crypto_pct=50,
    )

    assert assessment.aligned is False
    assert (
        "Projected crypto allocation exceeds "
        "the Investment Policy limit." in assessment.rationale
    )
