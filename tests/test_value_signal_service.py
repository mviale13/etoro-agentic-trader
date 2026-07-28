from app.domain.company_facts import CompanyFacts
from app.services.value_signal_service import ValueSignalService


def company(pe: float | None) -> CompanyFacts:
    return CompanyFacts(
        instrument_id=1,
        symbol="MSFT",
        name="Microsoft",
        asset_type="Stock",
        exchange="NASDAQ",
        current_price=100,
        daily_change_pct=1,
        market_cap=None,
        forward_pe=pe,
        eps=None,
        dividend_yield=None,
        sector=None,
        industry=None,
    )


def test_expensive() -> None:
    signal = ValueSignalService().build(company(35))

    assert signal.valuation == "EXPENSIVE"


def test_fair() -> None:
    signal = ValueSignalService().build(company(22))

    assert signal.valuation == "FAIR"


def test_cheap() -> None:
    signal = ValueSignalService().build(company(14))

    assert signal.valuation == "CHEAP"


def test_unknown() -> None:
    signal = ValueSignalService().build(company(None))

    assert signal.valuation == "UNKNOWN"
