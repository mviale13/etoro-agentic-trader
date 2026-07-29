from app.application.executive.executive_service import (
    ExecutiveService,
)
from app.brain import BrainBuilder
from tests.test_brain_context import (
    make_market,
    make_policy,
    make_portfolio,
)


def make_brain():
    return BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
    ).build()


def test_executive_decide_preserves_existing_api():
    decision = ExecutiveService().decide(
        symbol="AAPL",
        brain=make_brain(),
    )

    assert decision.symbol == "AAPL"
    assert decision.state is not None
    assert decision.rationale


def test_executive_evaluate_returns_complete_evaluation():
    evaluation = ExecutiveService().evaluate(
        symbol="AAPL",
        brain=make_brain(),
    )

    assert evaluation.decision.symbol == "AAPL"

    assert evaluation.thesis.symbol == "AAPL"
    assert evaluation.thesis.recommendation
    assert evaluation.thesis.summary
    assert 0.0 <= evaluation.thesis.confidence <= 1.0
    assert evaluation.thesis.expected_holding_period == "3-5 years"
    assert evaluation.thesis.created_at.tzinfo is not None

    assert evaluation.reasoning.portfolio is not None
    assert evaluation.reasoning.market is not None
    assert evaluation.reasoning.risk is not None

    assert len(evaluation.committee_opinions) == 2
