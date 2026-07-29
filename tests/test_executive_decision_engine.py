from app.domain.decision_state import DecisionState
from app.domain.executive_decision import DecisionEvidence
from app.reasoning.executive_decision_engine import ExecutiveDecisionEngine


def evidence(
    *,
    quality: int = 80,
    available_evidence: int = 80,
    valuation: int = 75,
    risk: int = 30,
    portfolio_fit: int = 75,
    actionable: bool = True,
    hard_reject: bool = False,
    analyst_veto: bool = False,
) -> DecisionEvidence:
    return DecisionEvidence(
        symbol="TEST",
        quality_score=quality,
        evidence_score=available_evidence,
        valuation_score=valuation,
        risk_score=risk,
        portfolio_fit_score=portfolio_fit,
        actionable_now=actionable,
        hard_reject=hard_reject,
        analyst_veto=analyst_veto,
        strengths=("Durable competitive advantage.",),
        risks=("Execution risk remains.",),
        missing_evidence=(),
        catalysts=("Revenue acceleration.",),
    )


def test_hard_policy_violation_is_rejected() -> None:
    decision = ExecutiveDecisionEngine().decide(
        evidence(hard_reject=True),
    )

    assert decision.state is DecisionState.REJECT
    assert decision.belongs_to_watchlist is False


def test_analyst_veto_blocks_recommendation() -> None:
    decision = ExecutiveDecisionEngine().decide(
        evidence(analyst_veto=True),
    )

    assert decision.state is DecisionState.REJECT


def test_excessive_risk_is_rejected() -> None:
    decision = ExecutiveDecisionEngine().decide(
        evidence(risk=90),
    )

    assert decision.state is DecisionState.REJECT


def test_low_quality_is_rejected() -> None:
    decision = ExecutiveDecisionEngine().decide(
        evidence(quality=20),
    )

    assert decision.state is DecisionState.REJECT


def test_limited_evidence_is_monitored() -> None:
    decision = ExecutiveDecisionEngine().decide(
        evidence(available_evidence=20),
    )

    assert decision.state is DecisionState.MONITOR
    assert decision.belongs_to_watchlist is True


def test_incomplete_research_is_investigated() -> None:
    decision = ExecutiveDecisionEngine().decide(
        evidence(
            quality=55,
            available_evidence=50,
        ),
    )

    assert decision.state is DecisionState.INVESTIGATE
    assert decision.belongs_to_watchlist is True


def test_good_company_with_unattractive_valuation_is_prepared() -> None:
    decision = ExecutiveDecisionEngine().decide(
        evidence(valuation=40),
    )

    assert decision.state is DecisionState.PREPARE
    assert decision.belongs_to_watchlist is True


def test_ready_case_waiting_for_trigger_is_prepared() -> None:
    decision = ExecutiveDecisionEngine().decide(
        evidence(actionable=False),
    )

    assert decision.state is DecisionState.PREPARE


def test_complete_actionable_case_is_recommended() -> None:
    decision = ExecutiveDecisionEngine().decide(
        evidence(),
    )

    assert decision.state is DecisionState.RECOMMEND
    assert decision.belongs_to_watchlist is True


def test_decision_contains_explanation() -> None:
    decision = ExecutiveDecisionEngine().decide(
        evidence(),
    )

    assert decision.rationale
    assert decision.key_strengths
    assert decision.key_risks
    assert decision.catalysts


def test_decisions_are_deterministic_except_for_timestamp() -> None:
    engine = ExecutiveDecisionEngine()
    inputs = evidence()

    first = engine.decide(inputs)
    second = engine.decide(inputs)

    assert first.model_dump(exclude={"decided_at"}) == second.model_dump(
        exclude={"decided_at"},
    )


def test_only_reject_is_excluded_from_watchlist() -> None:
    expected = {
        DecisionState.REJECT: False,
        DecisionState.MONITOR: True,
        DecisionState.INVESTIGATE: True,
        DecisionState.PREPARE: True,
        DecisionState.RECOMMEND: True,
    }

    for state, belongs_to_watchlist in expected.items():
        assert state.belongs_to_watchlist is belongs_to_watchlist
