"""What a committee's confidence claims, and what silence is worth."""

from app.application.brain.reasoning import ReasoningService
from app.application.committees.committee_service import CommitteeService
from app.application.committees.investment_committee import (
    InvestmentCommittee,
)
from app.application.committees.models.committee_opinion import Recommendation
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

    return CommitteeService().review(brain, ReasoningService().reason(brain), "MSFT")


def test_a_committee_that_cannot_measure_holds_no_opinion() -> None:
    """
    Portfolio risk is not measurable — nothing records position history.

    The Risk Committee said so, and then reported 0.0 confidence, which is
    itself a claim: as good as certain, of nothing.
    """

    brain = make_brain()
    reasoning = ReasoningService().reason(brain)

    assert reasoning.risk.overall_risk_score is None

    opinion = RiskCommittee().review(brain, reasoning, "MSFT")

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

    assert stated == []
    assert agreement is None


def evidenced_brain(**company: object):
    """A brain that holds evidence about GOOD, and none about anything else."""

    from tests.test_security_evidence import make_company

    return BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
        evidence={"GOOD": (make_company("GOOD", **company),)},  # type: ignore[arg-type]
    ).build()


def test_confidence_is_not_the_recommendation_in_disguise() -> None:
    """
    Confidence used to be the score, so a bearish view was a tentative one.

    A committee reading a weak portfolio and weak momentum is not unsure —
    it is reading well-evidenced assessments and reaching a negative
    conclusion, which it should be able to state plainly.
    """

    brain = evidenced_brain(recommendation="SELL")
    reasoning = ReasoningService().reason(brain)

    opinion = InvestmentCommittee().review(brain, reasoning, "GOOD")

    assert opinion.confidence is not None
    assert opinion.recommendation is Recommendation.REDUCE
    assert opinion.confidence > 0.5


def test_the_committee_reviews_the_security_not_only_the_account() -> None:
    """
    Both committees used to read the portfolio and the market alone.

    Their opinions were therefore identical under every symbol, and told
    the Artificial CIO nothing about the case in front of it.
    """

    buy = evidenced_brain(recommendation="BUY")
    sell = evidenced_brain(recommendation="SELL")

    bullish = InvestmentCommittee().review(
        buy,
        ReasoningService().reason(buy),
        "GOOD",
    )
    bearish = InvestmentCommittee().review(
        sell,
        ReasoningService().reason(sell),
        "GOOD",
    )

    assert bullish.recommendation is not bearish.recommendation


def test_a_security_with_no_evidence_gets_no_committee_view() -> None:
    """Reviewing a case on context alone is what this stopped doing."""

    brain = evidenced_brain()

    opinion = InvestmentCommittee().review(
        brain,
        ReasoningService().reason(brain),
        "UNSEEN",
    )

    assert opinion.confidence is None
    assert "UNSEEN" in opinion.summary


def test_risk_speaks_to_the_security_whose_risk_was_measured() -> None:
    """
    Portfolio risk needs position history, which nothing records, so this
    committee abstained on every symbol — including securities whose own
    volatility and deepest fall had been measured from a year of prices.
    """

    from dataclasses import replace

    from app.domain.risk_signal import RiskSignal
    from tests.test_security_evidence import make_company

    violent = make_company("GOOD")
    violent = replace(
        violent,
        signals=replace(
            violent.signals,
            risk=RiskSignal(
                level="SEVERE",
                volatility=0.94,
                max_drawdown=0.61,
                confidence=90,
                evidence=(),
            ),
        ),
    )

    brain = BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
        evidence={"GOOD": (violent,)},
    ).build()

    opinion = RiskCommittee().review(brain, ReasoningService().reason(brain), "GOOD")

    assert opinion.confidence == 0.90
    assert opinion.recommendation is Recommendation.SELL
