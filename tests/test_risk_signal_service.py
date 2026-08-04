"""Risk read out of a security's own price history."""

from app.domain.company_facts import CompanyFacts
from app.domain.market_sensitivity import MarketSensitivity
from app.services.risk_signal_service import RiskSignalService


def company(
    volatility: float | None,
    drawdown: float | None,
    sensitivity: MarketSensitivity | None = None,
) -> CompanyFacts:
    return CompanyFacts(
        instrument_id=1,
        symbol="MSFT",
        name="Microsoft",
        asset_type="Stock",
        exchange="NASDAQ",
        realized_volatility=volatility,
        max_drawdown=drawdown,
        market_sensitivity=sensitivity,
    )


def sensitivity(beta: float = 1.8) -> MarketSensitivity:
    return MarketSensitivity(
        beta=beta,
        correlation=0.72,
        observations=240,
        benchmark="SPY",
    )


def test_a_calm_security_is_low_risk() -> None:
    signal = RiskSignalService().build(company(0.14, 0.08))

    assert signal.level == "LOW"
    assert signal.volatility == 0.14
    assert signal.max_drawdown == 0.08
    assert any("14.0%" in finding.statement for finding in signal.evidence)


def test_a_violent_security_is_severe_risk() -> None:
    assert RiskSignalService().build(company(0.85, 0.55)).level == "SEVERE"


def test_the_higher_of_the_two_readings_decides() -> None:
    """Calm day-to-day, but it has already fallen by half."""

    assert RiskSignalService().build(company(0.12, 0.52)).level == "HIGH"


def test_a_security_without_history_reports_unknown_risk() -> None:
    signal = RiskSignalService().build(company(None, None))

    assert signal.level == "UNKNOWN"
    assert signal.volatility is None
    assert signal.max_drawdown is None
    assert any("not measured" in finding.statement for finding in signal.evidence)


def test_one_reading_is_still_a_measurement() -> None:
    signal = RiskSignalService().build(company(0.45, None))

    assert signal.level == "HIGH"
    assert signal.confidence < 90
    assert len(signal.evidence) == 1


def test_market_sensitivity_is_carried_and_reported() -> None:
    signal = RiskSignalService().build(company(0.14, 0.08, sensitivity(1.8)))

    assert signal.market_sensitivity is not None
    assert signal.market_sensitivity.beta == 1.8
    assert any("1.80×" in finding.statement for finding in signal.evidence)


def test_a_high_beta_does_not_move_the_risk_band() -> None:
    """How hard it swings with the market is a different risk from how hard
    it swings; the band stays the security's own volatility and drawdown."""

    calm = RiskSignalService().build(company(0.14, 0.08))
    calm_but_high_beta = RiskSignalService().build(
        company(0.14, 0.08, sensitivity(2.5))
    )

    assert calm.level == calm_but_high_beta.level == "LOW"


def test_sensitivity_is_reported_even_without_a_risk_band() -> None:
    """It needs only aligned returns, not the series the band comes from."""

    signal = RiskSignalService().build(company(None, None, sensitivity(1.2)))

    assert signal.level == "UNKNOWN"
    assert signal.market_sensitivity is not None
    assert any("1.20×" in finding.statement for finding in signal.evidence)
