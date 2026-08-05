from app.domain.asset_class import AssetClass
from app.domain.company_facts import CompanyFacts
from app.domain.company_profile import (
    CompanyProfile,
    Sector,
)
from app.domain.company_research_context import CompanyResearchContext
from app.services.company_facts_analyst_adapter import CompanyFactsAnalystAdapter


class FakeCompanyFactsAnalyst:
    def __init__(self) -> None:
        self.received: CompanyFacts | None = None

    def analyze(self, company: CompanyFacts) -> str:
        self.received = company
        return "analyst opinion"


def make_context() -> CompanyResearchContext:
    facts = CompanyFacts(
        instrument_id=1004,
        symbol="MSFT",
        name="Microsoft",
        asset_type="Stock",
        exchange="NASDAQ",
        current_price=510.0,
        daily_change_pct=1.5,
        market_cap=3_800_000_000_000,
        forward_pe=35.0,
        eps=14.2,
        dividend_yield=0.72,
        sector="Technology",
        industry="Software",
    )

    profile = CompanyProfile(
        asset_class=AssetClass.STOCK,
        sector=Sector.TECHNOLOGY,
        industry="Software",
    )

    return CompanyResearchContext(
        facts=facts,
        profile=profile,
    )


def test_adapter_passes_company_facts_to_existing_analyst() -> None:
    analyst = FakeCompanyFactsAnalyst()
    adapter = CompanyFactsAnalystAdapter(analyst)
    context = make_context()

    opinion = adapter.analyze(context)

    assert opinion == "analyst opinion"
    assert analyst.received is context.facts
