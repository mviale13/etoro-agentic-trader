from app.domain.company_facts import CompanyFacts
from app.services.quality_signal_service import QualitySignalService


def company(
    market_cap: float | None,
    eps: float | None,
    dividend: float | None,
) -> CompanyFacts:
    return CompanyFacts(
        instrument_id=1,
        symbol="MSFT",
        name="Microsoft",
        asset_type="Stock",
        exchange="NASDAQ",
        current_price=500,
        daily_change_pct=1.2,
        market_cap=market_cap,
        forward_pe=30,
        eps=eps,
        dividend_yield=dividend,
        sector=None,
        industry=None,
    )


def test_high_quality() -> None:
    signal = QualitySignalService().build(
        company(
            3_000_000_000_000,
            12.5,
            0.008,
        )
    )

    assert signal.quality == "HIGH"


def test_medium_quality() -> None:
    signal = QualitySignalService().build(
        company(
            20_000_000_000,
            5.0,
            None,
        )
    )

    assert signal.quality == "MEDIUM"


def test_low_quality() -> None:
    signal = QualitySignalService().build(
        company(
            2_000_000_000,
            -1.5,
            None,
        )
    )

    assert signal.quality == "LOW"


def test_unknown_quality() -> None:
    signal = QualitySignalService().build(
        company(
            None,
            None,
            None,
        )
    )

    assert signal.quality == "UNKNOWN"
