from app.analysts.balance_sheet_analyst import BalanceSheetAnalyst
from app.domain.balance_sheet_opinion import BalanceSheetVerdict
from app.domain.company_facts import CompanyFacts


def company(
    debt_to_equity: float | None,
    current_ratio: float | None,
) -> CompanyFacts:
    return CompanyFacts(
        instrument_id=1004,
        symbol="MSFT",
        name="Microsoft",
        asset_type="Stock",
        exchange="NASDAQ",
        current_price=510.0,
        daily_change_pct=1.5,
        market_cap=3_800_000_000_000,
        forward_pe=35.0,
        debt_to_equity=debt_to_equity,
        current_ratio=current_ratio,
        eps=14.2,
        dividend_yield=0.0072,
        sector="Technology",
        industry="Software",
    )


def test_excellent_balance_sheet() -> None:
    opinion = BalanceSheetAnalyst().analyze(company(0.20, 2.50))

    assert opinion.score == 100
    assert opinion.confidence == 1.0
    assert opinion.verdict is BalanceSheetVerdict.EXCELLENT


def test_strong_balance_sheet() -> None:
    opinion = BalanceSheetAnalyst().analyze(company(0.45, 1.70))

    assert opinion.score == 85
    assert opinion.verdict is BalanceSheetVerdict.STRONG


def test_adequate_balance_sheet() -> None:
    opinion = BalanceSheetAnalyst().analyze(company(0.90, 1.30))

    assert opinion.score == 70
    assert opinion.verdict is BalanceSheetVerdict.ADEQUATE


def test_weak_balance_sheet() -> None:
    opinion = BalanceSheetAnalyst().analyze(company(2.50, 0.80))

    assert opinion.score == 0
    assert opinion.verdict is BalanceSheetVerdict.WEAK


def test_partial_data() -> None:
    opinion = BalanceSheetAnalyst().analyze(company(0.40, None))

    assert opinion.score == 85
    assert opinion.confidence == 0.5
    assert opinion.uncertainty == ("Current ratio data is unavailable.",)


def test_unknown() -> None:
    opinion = BalanceSheetAnalyst().analyze(company(None, None))

    assert opinion.score is None
    assert opinion.confidence == 0.0
    assert opinion.verdict is BalanceSheetVerdict.UNKNOWN
