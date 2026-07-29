from app.domain.company_profile import (
    BusinessModel,
    CompanyLifecycle,
    CompanyProfile,
    Sector,
)
from app.services.research_strategy import (
    CorporateResearchStrategy,
)
from app.services.research_strategy_factory import (
    ResearchStrategyFactory,
)


def test_returns_corporate_strategy_for_standard_company() -> None:
    profile = CompanyProfile(
        business_model=BusinessModel.STANDARD_CORPORATE,
        lifecycle=CompanyLifecycle.MATURE,
        sector=Sector.TECHNOLOGY,
        industry="Software",
    )

    strategy = ResearchStrategyFactory().create(profile)

    assert isinstance(strategy, CorporateResearchStrategy)


def test_rejects_unsupported_business_model() -> None:
    profile = CompanyProfile(
        business_model=BusinessModel.BANK,
        lifecycle=CompanyLifecycle.MATURE,
        sector=Sector.FINANCIALS,
        industry="Banking",
    )

    try:
        ResearchStrategyFactory().create(profile)
    except ValueError as error:
        assert str(error) == ("No research strategy available for business model: bank")
    else:
        raise AssertionError("Expected unsupported business model to fail")
