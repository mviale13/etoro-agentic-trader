from app.domain.company_facts import CompanyFacts
from app.services.momentum_signal_service import MomentumSignalService


def company(
    daily_change_pct: float | None,
) -> CompanyFacts:
    return CompanyFacts(
        instrument_id=1004,
        symbol="MSFT",
        name="Microsoft",
        asset_type="Stock",
        exchange="NASDAQ",
        current_price=510.0,
        daily_change_pct=daily_change_pct,
        market_cap=None,
        forward_pe=None,
        eps=None,
        dividend_yield=None,
        sector=None,
        industry=None,
    )


def test_strong_positive_change_is_bullish() -> None:
    signal = MomentumSignalService().build(
        company(3.2),
    )

    assert signal.trend == "BULLISH"
    assert signal.strength == "STRONG"
    assert signal.confidence == 85


def test_moderate_positive_change_is_bullish() -> None:
    signal = MomentumSignalService().build(
        company(1.1),
    )

    assert signal.trend == "BULLISH"
    assert signal.strength == "MODERATE"


def test_strong_negative_change_is_bearish() -> None:
    signal = MomentumSignalService().build(
        company(-3.0),
    )

    assert signal.trend == "BEARISH"
    assert signal.strength == "STRONG"


def test_small_change_is_neutral() -> None:
    signal = MomentumSignalService().build(
        company(0.2),
    )

    assert signal.trend == "NEUTRAL"
    assert signal.strength == "WEAK"


def test_missing_change_is_unknown() -> None:
    signal = MomentumSignalService().build(
        company(None),
    )

    assert signal.trend == "UNKNOWN"
    assert signal.confidence == 20
