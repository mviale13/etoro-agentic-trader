from app.application.brain.reasoning import ReasoningService
from app.application.committees.committee_service import CommitteeService
from app.brain import BrainBuilder
from tests.test_brain_context import (
    make_market,
    make_policy,
    make_portfolio,
)


def test_committees_review_reasoning():

    brain = BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
    ).build()

    reasoning = ReasoningService().reason(brain)

    opinions = CommitteeService().review(
        brain,
        reasoning,
    )

    assert len(opinions) == 2

    assert opinions[0].committee == "Investment Committee"

    assert opinions[1].committee == "Risk Committee"
