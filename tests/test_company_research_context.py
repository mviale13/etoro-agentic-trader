from app.domain.company_facts import CompanyFacts
from app.domain.company_profile import (
    BusinessModel,
    CompanyLifecycle,
    CompanyProfile,
    Sector,
)
from app.domain.company_research_context import CompanyResearchContext


def test_company_research_context_groups_facts_and_profile() -> None:
    facts = CompanyFacts(
        instrument_id=1,
        symbol="JPM",
        name="JPMorgan Chase",
        asset_type="stock",
        exchange="NYSE",
        current_price=200.0,
        daily_change_pct=1.2,
        market_cap=600_000_000_000.0,
        forward_pe=12.0,
    )

    profile = CompanyProfile(
        business_model=BusinessModel.BANK,
        lifecycle=CompanyLifecycle.MATURE,
        sector=Sector.FINANCIALS,
        industry="diversified_bank",
    )

    context = CompanyResearchContext(
        facts=facts,
        profile=profile,
    )

    assert context.facts is facts
    assert context.profile is profile
