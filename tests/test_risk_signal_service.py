"""Risk read out of a security's own price history."""

from app.domain.company_facts import CompanyFacts
from app.services.risk_signal_service import RiskSignalService


def company(
    volatility: float | None,
    drawdown: float | None,
) -> CompanyFacts:
    return CompanyFacts(
        instrument_id=1,
        symbol="MSFT",
        name="Microsoft",
        asset_type="Stock",
        exchange="NASDAQ",
        realized_volatility=volatility,
        max_drawdown=drawdown,
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
