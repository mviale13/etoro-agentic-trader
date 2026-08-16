from app.domain.company_facts import CompanyFacts
from app.services.quality_signal_service import QualitySignalService
from tests.conftest import admissible_market_cap


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
        market_cap_magnitude=(
            admissible_market_cap(market_cap) if market_cap is not None else None
        ),
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
    """Two of three factors passed, with the third read and failed.

    The dividend must be *read* for a band to be authorised at all
    since `quality-authority@1`; a company that pays none reads 0.0,
    which is a measured failure and not an absence.
    """

    signal = QualitySignalService().build(
        company(
            20_000_000_000,
            5.0,
            0.0,
        )
    )

    assert signal.quality == "MEDIUM"


def test_an_unreadable_factor_withholds_the_band() -> None:
    """The #140 defect: a partial question set cannot judge a business."""

    signal = QualitySignalService().build(company(20_000_000_000, 5.0, None))

    assert signal.quality == "UNKNOWN"
    assert signal.earned == 2
    assert signal.available == 2
    assert signal.basis is not None
    assert "dividend could not be read" in signal.basis


def test_low_quality() -> None:
    signal = QualitySignalService().build(
        company(
            2_000_000_000,
            -1.5,
            0.0,
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
