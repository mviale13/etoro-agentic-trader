from app.analysts.cash_flow_analyst import CashFlowAnalyst
from app.domain.cash_flow_opinion import CashFlowVerdict
from app.domain.company_facts import CompanyFacts


def excellent_company() -> CompanyFacts:
    return CompanyFacts(
        instrument_id=1,
        symbol="TEST",
        name="Test Company",
        asset_type="Stock",
        exchange="NASDAQ",
        current_price=100.0,
        daily_change_pct=0.0,
        market_cap=1_000_000_000.0,
        forward_pe=20.0,
        operating_cash_flow=100.0,
        free_cash_flow=50.0,
    )


def weak_company() -> CompanyFacts:
    return CompanyFacts(
        instrument_id=1,
        symbol="TEST",
        name="Test Company",
        asset_type="Stock",
        exchange="NASDAQ",
        current_price=100.0,
        daily_change_pct=0.0,
        market_cap=1_000_000_000.0,
        forward_pe=20.0,
        operating_cash_flow=-10.0,
        free_cash_flow=-5.0,
    )


def unknown_company() -> CompanyFacts:
    return CompanyFacts(
        instrument_id=1,
        symbol="TEST",
        name="Test Company",
        asset_type="Stock",
        exchange="NASDAQ",
        current_price=100.0,
        daily_change_pct=0.0,
        market_cap=1_000_000_000.0,
        forward_pe=20.0,
    )


def test_excellent_cash_flow() -> None:
    opinion = CashFlowAnalyst().analyze(excellent_company())

    assert opinion.score == 100
    assert opinion.verdict is CashFlowVerdict.EXCELLENT
    assert opinion.confidence == 1.0


def test_cash_flow_is_stated_in_readable_magnitudes() -> None:
    """A hundred-billion-dollar flow reads in billions, not to the penny."""

    company = CompanyFacts(
        instrument_id=1,
        symbol="TEST",
        name="Test Company",
        asset_type="Stock",
        exchange="NASDAQ",
        operating_cash_flow=146_723_995_648.0,
        free_cash_flow=-1_200_000_000.0,
    )

    evidence = CashFlowAnalyst().analyze(company).evidence

    assert "Operating cash flow is $146.7B." in evidence
    assert "Free cash flow is -$1.2B." in evidence


def test_weak_cash_flow() -> None:
    opinion = CashFlowAnalyst().analyze(weak_company())

    assert opinion.score == 0
    assert opinion.verdict is CashFlowVerdict.WEAK
    assert opinion.confidence == 1.0


def test_unknown_cash_flow() -> None:
    opinion = CashFlowAnalyst().analyze(unknown_company())

    assert opinion.score == 50
    assert opinion.verdict is CashFlowVerdict.UNKNOWN
    assert opinion.confidence == 0.0
    assert len(opinion.uncertainty) == 2
