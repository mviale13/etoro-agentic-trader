"""What the Artificial CIO does when a measurement is missing.

Every score here used to be filled in from somewhere else: an unknown
company quality became the portfolio's health score, an unknown valuation
became market momentum, and two thirds of the risk score were hardcoded
constants. Four unrelated companies reported the same quality, and that
number moved their ranking.
"""

from app.application.brain.reasoning.risk_analyst import RiskAnalyst
from app.cio import ArtificialCIO, DecisionEvidence, DecisionPolicy, DecisionState
from tests.test_brain_context import make_market, make_policy, make_portfolio
from tests.test_security_evidence import build_evidence, make_brain, make_company


def evidence(**overrides: object) -> DecisionEvidence:
    """A case that clears every gate, unless a test removes a measurement."""

    return DecisionEvidence(
        **{
            "symbol": "MSFT",
            "quality_score": 85,
            "evidence_score": 85,
            "valuation_score": 80,
            "risk_score": 20,
            "portfolio_fit_score": 80,
            "actionable_now": True,
            **overrides,
        }  # type: ignore[arg-type]
    )


def test_an_unknown_quality_is_absent_not_borrowed() -> None:
    """Quality used to fall back to the portfolio's health score."""

    brain = make_brain(
        evidence={"PARTIAL": (make_company("PARTIAL", quality="UNKNOWN"),)},
    )

    assert build_evidence(brain, "PARTIAL").quality_score is None


def test_an_unknown_valuation_is_absent_not_borrowed() -> None:
    """Valuation used to fall back to market momentum."""

    brain = make_brain(
        evidence={"PARTIAL": (make_company("PARTIAL", valuation="UNKNOWN"),)},
    )

    assert build_evidence(brain, "PARTIAL").valuation_score is None


def test_a_security_with_no_evidence_scores_nothing() -> None:
    unknown = build_evidence(make_brain(), "NOTHING")

    assert unknown.quality_score is None
    assert unknown.valuation_score is None
    assert unknown.missing_evidence


def test_an_unmeasured_quality_stops_the_case_at_research() -> None:
    decision = ArtificialCIO().decide(evidence(quality_score=None))

    assert decision.state is DecisionState.INVESTIGATE
    assert "not been measured" in decision.rationale


def test_an_unmeasured_valuation_cannot_reach_a_recommendation() -> None:
    decision = ArtificialCIO().decide(evidence(valuation_score=None))

    assert decision.state is DecisionState.PREPARE
    assert "valuation has not been measured" in decision.rationale


def test_a_fully_measured_case_still_reaches_a_recommendation() -> None:
    assert ArtificialCIO().decide(evidence()).state is DecisionState.RECOMMEND


def test_an_unmeasured_score_is_not_a_reason_to_reject() -> None:
    """Not knowing something is not the same as knowing it is bad."""

    decision = ArtificialCIO().decide(
        evidence(quality_score=None, risk_score=None),
    )

    assert decision.state is not DecisionState.REJECT


def test_a_measured_breach_still_rejects() -> None:
    policy = DecisionPolicy()

    rejected = ArtificialCIO().decide(
        evidence(risk_score=policy.maximum_acceptable_risk + 1),
    )

    assert rejected.state is DecisionState.REJECT


def test_conviction_averages_only_what_was_measured() -> None:
    """An absent score must not be averaged in as a zero."""

    complete = ArtificialCIO().decide(evidence(valuation_score=80))
    partial = ArtificialCIO().decide(evidence(valuation_score=None))

    # Both rest on the same measured scores; the partial case is capped by
    # the state it can reach, never dragged down by counting a gap as zero.
    assert partial.conviction >= complete.conviction - 5


def test_risk_reports_what_it_cannot_measure() -> None:
    assessment = RiskAnalyst().assess(_brain())

    assert assessment.market_risk_score is None
    assert assessment.drawdown_risk_score is None
    assert assessment.liquidity_risk_score is not None
    assert assessment.concentration_risk_score is not None

    assert any("Market risk" in item for item in assessment.unmeasured)
    assert any("Drawdown" in item for item in assessment.unmeasured)


def test_overall_risk_is_absent_while_a_component_is_missing() -> None:
    """
    Averaging the measured half would report "risk: 0" for an account whose
    market and drawdown exposure nobody has looked at — and a zero flatters
    the case, because low risk is scored as conviction.
    """

    assert RiskAnalyst().assess(_brain()).overall_risk_score is None


def test_unmeasured_risk_cannot_reach_a_recommendation() -> None:
    decision = ArtificialCIO().decide(evidence(risk_score=None))

    assert decision.state is DecisionState.PREPARE
    assert "risk has not been measured" in decision.rationale


def test_unmeasured_risk_reaches_the_investor_as_missing_evidence() -> None:
    missing = build_evidence(make_brain(), "MSFT").missing_evidence

    assert any("Market risk" in item for item in missing)


def _brain():
    from app.brain import BrainBuilder

    return BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
    ).build()
