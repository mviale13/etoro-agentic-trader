"""What a committee's confidence claims, and what silence is worth."""

from app.application.brain.reasoning import ReasoningService
from app.application.committees.committee_service import CommitteeService
from app.application.committees.investment_committee import (
    InvestmentCommittee,
)
from app.application.committees.risk_committee import RiskCommittee
from app.application.thesis.investment_thesis_builder import (
    InvestmentThesisBuilder,
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


def opinions():
    brain = make_brain()

    return CommitteeService().review(brain, ReasoningService().reason(brain))


def test_a_committee_that_cannot_measure_holds_no_opinion() -> None:
    """
    Portfolio risk is not measurable — nothing records position history.

    The Risk Committee said so, and then reported 0.0 confidence, which is
    itself a claim: as good as certain, of nothing.
    """

    brain = make_brain()
    reasoning = ReasoningService().reason(brain)

    assert reasoning.risk.overall_risk_score is None

    opinion = RiskCommittee().review(brain, reasoning)

    assert opinion.confidence is None
    assert not opinion.has_opinion


def test_silence_does_not_count_as_opposition() -> None:
    """
    An unmeasurable risk used to halve committee agreement.

    Averaging the Risk Committee's 0.0 with the Investment Committee's view
    reported 32% agreement beneath a RECOMMEND, when no committee had
    disagreed with anything.
    """

    stated = [
        opinion.confidence for opinion in opinions() if opinion.confidence is not None
    ]

    agreement = InvestmentThesisBuilder()._committee_confidence(opinions())

    assert len(stated) == 1
    assert agreement == stated[0]


def test_confidence_is_not_the_recommendation_in_disguise() -> None:
    """
    Confidence used to be the score, so a bearish view was a tentative one.

    A committee reading a weak portfolio and weak momentum is not unsure —
    it is reading well-evidenced assessments and reaching a negative
    conclusion, which it should be able to state plainly.
    """

    brain = make_brain()
    reasoning = ReasoningService().reason(brain)

    opinion = InvestmentCommittee().review(brain, reasoning)

    score = (
        reasoning.portfolio.health_score * 0.60 + reasoning.market.momentum_score * 0.40
    )

    assert opinion.confidence is not None
    assert opinion.confidence != score
    assert opinion.confidence > score
