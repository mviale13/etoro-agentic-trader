import pytest

from app.cio import (
    ArtificialCIO,
    DecisionEvidence,
    DecisionState,
    InvestmentCase,
    InvestmentCaseEventType,
)


def evidence(
    *,
    symbol: str = "MSFT",
    valuation: int = 75,
    actionable: bool = True,
) -> DecisionEvidence:
    return DecisionEvidence(
        symbol=symbol,
        quality_score=85,
        evidence_score=85,
        valuation_score=valuation,
        risk_score=25,
        portfolio_fit_score=80,
        actionable_now=actionable,
        evidence_weighed=("Durable competitive advantage.",),
        risks=("Valuation risk.",),
        catalysts=("Cloud growth acceleration.",),
    )


def test_artificial_cio_creates_first_decision() -> None:
    investment_case = InvestmentCase(
        symbol="MSFT",
        company_name="Microsoft",
    )

    result = ArtificialCIO().evaluate(
        investment_case,
        evidence(),
    )

    assert result.state is DecisionState.RECOMMEND
    assert result.belongs_to_watchlist is True
    assert len(result.timeline) == 1
    assert result.timeline[0].event_type is InvestmentCaseEventType.CASE_CREATED


def test_artificial_cio_records_decision_change() -> None:
    cio = ArtificialCIO()
    investment_case = InvestmentCase(symbol="MSFT")

    prepared = cio.evaluate(
        investment_case,
        evidence(valuation=40),
    )
    recommended = cio.evaluate(
        prepared,
        evidence(valuation=75),
    )

    assert prepared.state is DecisionState.PREPARE
    assert recommended.state is DecisionState.RECOMMEND

    latest_event = recommended.timeline[-1]

    assert latest_event.event_type is InvestmentCaseEventType.DECISION_CHANGED
    assert latest_event.previous_state is DecisionState.PREPARE
    assert latest_event.new_state is DecisionState.RECOMMEND


def test_artificial_cio_records_reaffirmed_decision() -> None:
    cio = ArtificialCIO()
    investment_case = InvestmentCase(symbol="MSFT")

    first = cio.evaluate(
        investment_case,
        evidence(),
    )
    second = cio.evaluate(
        first,
        evidence(),
    )

    assert second.timeline[-1].event_type is InvestmentCaseEventType.DECISION_REAFFIRMED


def test_rejected_case_is_not_watchlisted() -> None:
    rejected_evidence = evidence().model_copy(
        update={"hard_reject": True},
    )

    result = ArtificialCIO().evaluate(
        InvestmentCase(symbol="MSFT"),
        rejected_evidence,
    )

    assert result.state is DecisionState.REJECT
    assert result.belongs_to_watchlist is False


def test_symbol_mismatch_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="symbol must match",
    ):
        ArtificialCIO().evaluate(
            InvestmentCase(symbol="MSFT"),
            evidence(symbol="NVDA"),
        )
