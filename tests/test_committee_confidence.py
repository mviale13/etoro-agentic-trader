"""What a committee's position claims, and what silence is worth.

Every test here guards a defect this platform actually shipped. The
objects changed underneath them — a committee now states a stance over
referenced findings rather than a recommendation with a confidence
float — and the claims being guarded did not.
"""

from dataclasses import replace

from app.application.committees.committee_service import CommitteeService
from app.application.committees.investment_committee import (
    InvestmentCommittee,
)
from app.application.committees.risk_committee import RiskCommittee
from app.application.executive.decision_evidence_builder import (
    DecisionEvidenceBuilder,
)
from app.application.thesis.investment_thesis_builder import (
    InvestmentThesisBuilder,
)
from app.brain import BrainBuilder
from app.domain.committee.opinion import Stance
from app.domain.finding import Dimension, Finding, FindingLedger
from app.domain.risk_signal import RiskSignal
from tests.test_brain_context import (
    make_market,
    make_policy,
    make_portfolio,
)
from tests.test_security_evidence import make_company


def make_brain():
    return BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
    ).build()


def evidenced_brain(**company: object):
    """A brain that holds evidence about GOOD, and none about anything else."""

    return BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
        evidence={"GOOD": (make_company("GOOD", **company),)},  # type: ignore[arg-type]
    ).build()


def ledger_for(brain, symbol: str) -> FindingLedger:
    return DecisionEvidenceBuilder().ledger(symbol, brain)


def opinions():
    brain = make_brain()

    return CommitteeService().review(brain, "MSFT", ledger_for(brain, "MSFT"))


def test_a_committee_that_cannot_measure_holds_no_opinion() -> None:
    """
    Nothing records the position history a risk needs, so it is unmeasured.

    The Risk Committee said so, and then reported 0.0 confidence, which is
    itself a claim: as good as certain, of nothing. It now abstains, and
    an abstention carries no confidence at all.
    """

    brain = make_brain()

    opinion = RiskCommittee().review(brain, "MSFT", ledger_for(brain, "MSFT"))

    assert opinion.confidence is None
    assert opinion.stance is None
    assert not opinion.has_opinion


def test_an_abstention_is_never_a_neutral_position() -> None:
    """
    Silence and *we looked, and it argues neither way* are different claims.

    Returning HOLD on an unmeasured risk read as "risk is acceptable".
    The five-value stance vocabulary has no room for that distinction, so
    it lives outside it: an abstention is `stance=None`, never NEUTRAL.
    """

    brain = make_brain()

    opinion = RiskCommittee().review(brain, "MSFT", ledger_for(brain, "MSFT"))

    assert opinion.stance is not Stance.NEUTRAL
    assert opinion.abstained_because is not None
    assert "no position" in opinion.abstained_because


def test_silence_does_not_count_as_opposition() -> None:
    """
    An unmeasurable risk used to halve committee agreement.

    Averaging the Risk Committee's 0.0 with the Investment Committee's
    view reported 32% agreement beneath a RECOMMEND, when no committee
    had disagreed with anything.
    """

    stated = [opinion for opinion in opinions() if opinion.has_opinion]

    agreement = InvestmentThesisBuilder()._committee_confidence(opinions())

    assert stated == []
    assert agreement is None


def test_confidence_measures_the_reading_not_the_security() -> None:
    """
    Confidence used to be the score, so a bearish view was a tentative one.

    A committee reading well-evidenced adverse findings is not unsure. It
    is reading clearly and reaching a negative conclusion, and it must be
    able to state that plainly.
    """

    brain = evidenced_brain(quality="LOW", valuation="EXPENSIVE")

    ledger = FindingLedger.of(
        (
            Finding.adverse("Margins fell for four quarters.", Dimension.QUALITY),
            Finding.adverse("It trades far above its own range.", Dimension.VALUATION),
        )
    )

    opinion = InvestmentCommittee().review(brain, "GOOD", ledger)

    assert opinion.stance is Stance.STRONGLY_NEGATIVE
    assert opinion.confidence is not None

    # Every input the remit asks for was measured, so a firmly negative
    # view is stated firmly rather than discounted for being negative.
    assert opinion.confidence.completeness == 1.0
    assert opinion.confidence.level is not None


def test_the_committee_reviews_the_security_not_only_the_account() -> None:
    """
    Both committees used to read the portfolio and the market alone.

    Their opinions were therefore identical under every symbol, and told
    the Artificial CIO nothing about the case in front of it.
    """

    brain = evidenced_brain()

    bullish = InvestmentCommittee().review(
        brain,
        "GOOD",
        FindingLedger.of((Finding.favourable("Returns are wide.", Dimension.QUALITY),)),
    )

    bearish = InvestmentCommittee().review(
        brain,
        "GOOD",
        FindingLedger.of((Finding.adverse("Returns are thin.", Dimension.QUALITY),)),
    )

    assert bullish.stance is not bearish.stance


def test_a_security_with_no_evidence_gets_no_committee_view() -> None:
    """Reviewing a case on context alone is what this stopped doing."""

    brain = evidenced_brain()

    opinion = InvestmentCommittee().review(
        brain,
        "UNSEEN",
        ledger_for(brain, "UNSEEN"),
    )

    assert not opinion.has_opinion
    assert opinion.abstained_because is not None
    assert "UNSEEN" in opinion.abstained_because


def test_risk_speaks_to_the_security_whose_risk_was_measured() -> None:
    """
    Portfolio risk needs position history, which nothing records, so this
    committee abstained on every symbol — including securities whose own
    volatility and deepest fall had been measured from a year of prices.
    """

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
                evidence=(
                    Finding.adverse("It fell 61% from its high."),
                    Finding.adverse("It moves 94% a year."),
                ),
            ),
        ),
    )

    brain = BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
        evidence={"GOOD": (violent,)},
    ).build()

    opinion = RiskCommittee().review(brain, "GOOD", ledger_for(brain, "GOOD"))

    assert opinion.stance is Stance.STRONGLY_NEGATIVE
    assert opinion.confidence is not None
    assert opinion.confidence.opposing == 2


def test_a_committee_states_references_never_its_own_prose() -> None:
    """
    An opinion carrying its own wording could say what nobody read.

    Every reference must resolve in the ledger the committee was shown,
    which is the same ledger the decision keeps.
    """

    brain = evidenced_brain()

    ledger = FindingLedger.of(
        (
            Finding.favourable("Returns are wide.", Dimension.QUALITY),
            Finding.adverse("It is priced for perfection.", Dimension.VALUATION),
            # Outside this committee's remit, and therefore not its ground.
            Finding.adverse("It fell 61% from its high.", Dimension.RISK),
        )
    )

    opinion = InvestmentCommittee().review(brain, "GOOD", ledger)

    for ref in (*opinion.supporting, *opinion.opposing):
        assert ledger.resolve(ref) is not None

    assert ledger.statements_for(opinion.supporting) == ("Returns are wide.",)
    assert ledger.statements_for(opinion.opposing) == ("It is priced for perfection.",)


def test_a_committee_never_speaks_outside_its_remit() -> None:
    """The risk finding above belongs to the Risk Committee, and only to it."""

    brain = evidenced_brain()

    fell = Finding.adverse("It fell 61% from its high.", Dimension.RISK)

    ledger = FindingLedger.of(
        (Finding.favourable("Returns are wide.", Dimension.QUALITY), fell)
    )

    investment = InvestmentCommittee().review(brain, "GOOD", ledger)

    assert fell.ref not in investment.opposing
