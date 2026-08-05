from app.application.executive.executive_service import (
    ExecutiveService,
)
from app.brain import BrainBuilder
from tests.test_brain_context import (
    make_market,
    make_policy,
    make_portfolio,
)


def test_investment_thesis_is_built_from_executive_pipeline():
    brain = BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
    ).build()

    thesis = (
        ExecutiveService()
        .evaluate(
            symbol="MSFT",
            brain=brain,
        )
        .thesis
    )

    assert thesis.symbol == "MSFT"
    assert thesis.recommendation
    assert thesis.summary
    assert thesis.confidence is None
    assert isinstance(thesis.strengths, tuple)
    assert isinstance(thesis.risks, tuple)
    assert isinstance(thesis.catalysts, tuple)
    assert isinstance(thesis.invalidation_conditions, tuple)


def test_catalysts_are_the_securitys_own_and_context_stays_context() -> None:
    """
    The thesis carries the dated catalyst the decision carried.

    It used to build its own from the market's opportunities, which are
    identical under every symbol — so the line answering "why this, now"
    was "Stable market conditions" for MSFT and for everything else. Those
    opportunities are still weighed; they are stated as the account and
    market context they are.
    """

    from datetime import UTC, datetime

    from app.application.brain.reasoning import ReasoningService
    from app.application.thesis.investment_thesis_builder import (
        InvestmentThesisBuilder,
    )
    from app.cio.decision_state import DecisionState
    from app.domain.executive_decision import ExecutiveDecision

    brain = BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
    ).build()

    reasoning = ReasoningService().reason(brain)

    decision = ExecutiveDecision(
        symbol="MSFT",
        state=DecisionState.PREPARE,
        conviction=60,
        rationale="Quality clears; price does not.",
        catalysts=("Reports earnings in 6 days (Aug 11).",),
        decided_at=datetime(2026, 8, 5, tzinfo=UTC),
    )

    thesis = InvestmentThesisBuilder().build(
        symbol="MSFT",
        reasoning=reasoning,
        committee_opinions=(),
        decision=decision,
    )

    assert thesis.catalysts == ("Reports earnings in 6 days (Aug 11).",)

    # The defect, named: this is what used to be offered as MSFT's catalyst.
    assert "Stable market conditions" in reasoning.market.opportunities

    for opportunity in reasoning.market.opportunities:
        assert opportunity in thesis.context_strengths
        assert opportunity not in thesis.catalysts

    for opportunity in reasoning.opportunity.opportunities:
        assert opportunity in thesis.context_strengths
        assert opportunity not in thesis.catalysts
