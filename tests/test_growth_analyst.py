from app.analysts.growth_analyst import GrowthAnalyst
from app.domain.company_facts import CompanyFacts
from app.domain.growth_opinion import GrowthVerdict


def company(
    revenue_growth: float | None,
    earnings_growth: float | None,
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
        revenue_growth=revenue_growth,
        earnings_growth=earnings_growth,
        eps=14.2,
        dividend_yield=0.0072,
        sector="Technology",
        industry="Software",
    )


def test_strong_growth() -> None:
    opinion = GrowthAnalyst().analyze(
        company(
            revenue_growth=0.25,
            earnings_growth=0.35,
        )
    )

    assert opinion.score == 92
    assert opinion.confidence == 1.0
    assert opinion.verdict is GrowthVerdict.STRONG
    assert opinion.evidence == (
        "Revenue growth is 25.0%.",
        "Earnings growth is 35.0%.",
    )
    assert opinion.uncertainty == ()


def test_moderate_growth() -> None:
    opinion = GrowthAnalyst().analyze(
        company(
            revenue_growth=0.12,
            earnings_growth=0.08,
        )
    )

    assert opinion.score == 62
    assert opinion.confidence == 1.0
    assert opinion.verdict is GrowthVerdict.MODERATE


def test_declining_growth() -> None:
    opinion = GrowthAnalyst().analyze(
        company(
            revenue_growth=-0.15,
            earnings_growth=-0.05,
        )
    )

    assert opinion.score == 12
    assert opinion.confidence == 1.0
    assert opinion.verdict is GrowthVerdict.DECLINING


def test_partial_growth_data_reduces_confidence() -> None:
    opinion = GrowthAnalyst().analyze(
        company(
            revenue_growth=0.22,
            earnings_growth=None,
        )
    )

    assert opinion.score == 85
    assert opinion.confidence == 0.5
    assert opinion.verdict is GrowthVerdict.STRONG
    assert opinion.uncertainty == ("Earnings growth data is unavailable.",)


def test_missing_growth_data_is_unknown() -> None:
    opinion = GrowthAnalyst().analyze(
        company(
            revenue_growth=None,
            earnings_growth=None,
        )
    )

    assert opinion.score == 50
    assert opinion.confidence == 0.0
    assert opinion.verdict is GrowthVerdict.UNKNOWN
    assert opinion.evidence == ()
    assert opinion.uncertainty == (
        "Revenue growth data is unavailable.",
        "Earnings growth data is unavailable.",
    )
