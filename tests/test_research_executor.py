from app.domain.company_facts import CompanyFacts
from app.domain.company_profile import (
    BusinessModel,
    CompanyLifecycle,
    CompanyProfile,
    Sector,
)
from app.domain.company_research_context import CompanyResearchContext
from app.domain.research_plan import AnalystKey, ResearchPlan
from app.services.analyst_registry import AnalystRegistry
from app.services.research_executor import ResearchExecutor


class FakeGrowthAnalyst:
    def __init__(self) -> None:
        self.calls = 0

    def analyze(self, context: CompanyResearchContext) -> str:
        self.calls += 1
        assert context.facts.symbol == "MSFT"
        return "growth opinion"


class FakeCashFlowAnalyst:
    def __init__(self) -> None:
        self.calls = 0

    def analyze(self, context: CompanyResearchContext) -> str:
        self.calls += 1
        assert context.facts.symbol == "MSFT"
        return "cash flow opinion"


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
        business_model=BusinessModel.STANDARD_CORPORATE,
        lifecycle=CompanyLifecycle.MATURE,
        sector=Sector.TECHNOLOGY,
        industry="Software",
    )

    return CompanyResearchContext(
        facts=facts,
        profile=profile,
    )


def test_executor_runs_plan_and_collects_opinions() -> None:
    growth = FakeGrowthAnalyst()
    cash = FakeCashFlowAnalyst()

    registry = AnalystRegistry(
        analysts={
            AnalystKey.GROWTH: growth,
            AnalystKey.CASH_FLOW: cash,
        }
    )

    plan = ResearchPlan(
        objective="Test",
        questions=(
            "Growth?",
            "Cash flow?",
        ),
        analyst_keys=(
            AnalystKey.GROWTH,
            AnalystKey.CASH_FLOW,
        ),
    )

    executor = ResearchExecutor(registry)

    opinions = executor.execute(
        plan=plan,
        context=make_context(),
    )

    assert opinions == [
        "growth opinion",
        "cash flow opinion",
    ]

    assert growth.calls == 1
    assert cash.calls == 1
