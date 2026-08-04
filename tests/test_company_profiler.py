from app.domain.company_facts import CompanyFacts
from app.domain.company_profile import (
    BusinessModel,
    CompanyLifecycle,
    Sector,
)
from app.services.company_profiler import CompanyProfiler


def make_company(
    *,
    sector: str | None,
    industry: str | None,
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
        sector=sector,
        industry=industry,
    )


def test_profiler_normalizes_known_sector() -> None:
    company = make_company(
        sector="Technology",
        industry="Software",
    )

    profile = CompanyProfiler().profile(company)

    assert profile.business_model is BusinessModel.STANDARD_CORPORATE
    assert profile.lifecycle is CompanyLifecycle.MATURE
    assert profile.sector is Sector.TECHNOLOGY
    assert profile.industry == "Software"


def test_profiler_uses_other_for_unknown_sector() -> None:
    company = make_company(
        sector="Conglomerates",
        industry=None,
    )

    profile = CompanyProfiler().profile(company)

    assert profile.business_model is BusinessModel.STANDARD_CORPORATE
    assert profile.lifecycle is CompanyLifecycle.MATURE
    assert profile.sector is Sector.OTHER
    assert profile.industry is None


def test_profiler_handles_missing_sector() -> None:
    company = make_company(
        sector=None,
        industry="Unknown",
    )

    profile = CompanyProfiler().profile(company)

    assert profile.sector is Sector.OTHER
