"""Each holding's measured market exposure, read off the Brain."""

from app.application.change_feed.holding_exposures import holding_exposures
from app.domain.market_sensitivity import MarketSensitivity
from app.domain.risk_signal import RiskSignal
from tests.test_security_evidence import make_brain, make_company, make_holding


def sensitivity(beta: float = 1.2) -> MarketSensitivity:
    return MarketSensitivity(
        beta=beta,
        correlation=0.8,
        observations=250,
        benchmark="SPY",
    )


def risk_with(measured: MarketSensitivity | None) -> RiskSignal:
    return RiskSignal(
        level="MODERATE",
        volatility=0.30,
        max_drawdown=0.20,
        confidence=80,
        evidence=(),
        market_sensitivity=measured,
    )


def test_a_measured_holding_carries_its_sensitivity_and_weight() -> None:
    brain = make_brain(
        evidence={
            "NVDA": (make_company("NVDA", risk=risk_with(sensitivity(1.84))),),
        },
        holdings=(make_holding("NVDA", market_value_usd=12_300.0),),
    )

    exposures = holding_exposures(brain)

    assert len(exposures) == 1

    exposure = exposures[0]

    assert exposure.symbol == "NVDA"
    # 12,300 of the fixture portfolio's 100,000.
    assert exposure.weight_pct == 12.3
    assert exposure.sensitivity is not None
    assert exposure.sensitivity.beta == 1.84
    assert exposure.sensitivity.benchmark == "SPY"


def test_an_unmeasured_holding_is_listed_with_its_absence() -> None:
    """
    A holding without evidence stays on the list.

    Dropping it would let a feed line name only the measured holdings and
    read as "the rest are untouched" — which nothing measured. The count
    of unmeasured holdings is itself part of the honest statement.
    """

    brain = make_brain(
        evidence={},
        holdings=(make_holding("UUUU"),),
    )

    exposures = holding_exposures(brain)

    assert len(exposures) == 1
    assert exposures[0].symbol == "UUUU"
    assert exposures[0].sensitivity is None


def test_evidence_without_a_risk_signal_is_an_unmeasured_exposure() -> None:
    brain = make_brain(
        evidence={"MSFT": (make_company("MSFT", risk=None),)},
        holdings=(make_holding("MSFT"),),
    )

    assert holding_exposures(brain)[0].sensitivity is None


def test_a_risk_signal_without_sensitivity_is_an_unmeasured_exposure() -> None:
    brain = make_brain(
        evidence={"MSFT": (make_company("MSFT", risk=risk_with(None)),)},
        holdings=(make_holding("MSFT"),),
    )

    assert holding_exposures(brain)[0].sensitivity is None


def test_an_account_with_no_holdings_reports_no_exposures() -> None:
    assert holding_exposures(make_brain()) == ()
