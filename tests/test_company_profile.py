from app.domain.asset_class import AssetClass
from app.domain.company_profile import (
    CompanyProfile,
    Sector,
)


def test_company_profile_describes_business_context() -> None:
    profile = CompanyProfile(
        asset_class=AssetClass.STOCK,
        sector=Sector.FINANCIALS,
        industry="diversified_bank",
    )

    assert profile.asset_class is AssetClass.STOCK
    assert profile.sector is Sector.FINANCIALS
    assert profile.industry == "diversified_bank"


def test_company_profile_can_have_unknown_industry() -> None:
    profile = CompanyProfile(
        asset_class=AssetClass.STOCK,
        sector=Sector.OTHER,
        industry=None,
    )

    assert profile.industry is None
