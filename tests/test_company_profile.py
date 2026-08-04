from app.domain.company_profile import (
    BusinessModel,
    CompanyLifecycle,
    CompanyProfile,
    Sector,
)


def test_company_profile_describes_business_context() -> None:
    profile = CompanyProfile(
        business_model=BusinessModel.BANK,
        lifecycle=CompanyLifecycle.MATURE,
        sector=Sector.FINANCIALS,
        industry="diversified_bank",
    )

    assert profile.business_model is BusinessModel.BANK
    assert profile.lifecycle is CompanyLifecycle.MATURE
    assert profile.sector is Sector.FINANCIALS
    assert profile.industry == "diversified_bank"


def test_company_profile_can_have_unknown_industry() -> None:
    profile = CompanyProfile(
        business_model=BusinessModel.STANDARD_CORPORATE,
        lifecycle=CompanyLifecycle.MATURE,
        sector=Sector.OTHER,
        industry=None,
    )

    assert profile.industry is None
