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
    assert 0.0 <= thesis.confidence <= 1.0
    assert isinstance(thesis.strengths, tuple)
    assert isinstance(thesis.risks, tuple)
    assert isinstance(thesis.catalysts, tuple)
    assert isinstance(thesis.invalidation_conditions, tuple)
