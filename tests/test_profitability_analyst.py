from app.analysts.profitability_analyst import ProfitabilityAnalyst
from app.domain.company_facts import CompanyFacts
from app.domain.profitability_opinion import ProfitabilityVerdict


def company(
    gross_margin: float | None,
    operating_margin: float | None,
    net_margin: float | None,
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
        gross_margin=gross_margin,
        operating_margin=operating_margin,
        net_margin=net_margin,
        eps=14.2,
        dividend_yield=0.0072,
        sector="Technology",
        industry="Software",
    )


def test_excellent_profitability() -> None:
    opinion = ProfitabilityAnalyst().analyze(
        company(
            gross_margin=0.72,
            operating_margin=0.34,
            net_margin=0.27,
        )
    )

    assert opinion.score == 100
    assert opinion.confidence == 1.0
    assert opinion.verdict is ProfitabilityVerdict.EXCELLENT
    assert opinion.evidence == (
        "Gross margin is 72.0%.",
        "Operating margin is 34.0%.",
        "Net margin is 27.0%.",
    )
    assert opinion.uncertainty == ()


def test_strong_profitability() -> None:
    opinion = ProfitabilityAnalyst().analyze(
        company(
            gross_margin=0.45,
            operating_margin=0.23,
            net_margin=0.12,
        )
    )

    assert opinion.score == 85
    assert opinion.confidence == 1.0
    assert opinion.verdict is ProfitabilityVerdict.STRONG


def test_adequate_profitability() -> None:
    opinion = ProfitabilityAnalyst().analyze(
        company(
            gross_margin=0.30,
            operating_margin=0.10,
            net_margin=0.05,
        )
    )

    assert 50 <= opinion.score < 75
    assert opinion.confidence == 1.0
    assert opinion.verdict is ProfitabilityVerdict.ADEQUATE


def test_weak_profitability() -> None:
    opinion = ProfitabilityAnalyst().analyze(
        company(
            gross_margin=0.15,
            operating_margin=-0.05,
            net_margin=-0.08,
        )
    )

    assert opinion.score == 13
    assert opinion.confidence == 1.0
    assert opinion.verdict is ProfitabilityVerdict.WEAK


def test_partial_profitability_data_reduces_confidence() -> None:
    opinion = ProfitabilityAnalyst().analyze(
        company(
            gross_margin=0.45,
            operating_margin=None,
            net_margin=0.12,
        )
    )

    assert opinion.score == 85
    assert opinion.confidence == 2 / 3
    assert opinion.verdict is ProfitabilityVerdict.STRONG
    assert opinion.uncertainty == ("Operating margin data is unavailable.",)


def test_missing_profitability_data_is_unknown() -> None:
    opinion = ProfitabilityAnalyst().analyze(
        company(
            gross_margin=None,
            operating_margin=None,
            net_margin=None,
        )
    )

    assert opinion.score == 50
    assert opinion.confidence == 0.0
    assert opinion.verdict is ProfitabilityVerdict.UNKNOWN
    assert opinion.evidence == ()
    assert opinion.uncertainty == (
        "Gross margin data is unavailable.",
        "Operating margin data is unavailable.",
        "Net margin data is unavailable.",
    )
