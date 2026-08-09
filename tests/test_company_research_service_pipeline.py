import asyncio
from datetime import UTC, datetime

from app.domain.asset_class import AssetClass
from app.domain.company_facts import CompanyFacts
from app.domain.company_profile import (
    CompanyProfile,
    Sector,
)
from app.domain.company_research_context import CompanyResearchContext
from app.domain.playbook import PLAYBOOKS, InvestmentPlaybook, PlaybookKind
from app.domain.provenance import Provenance
from app.domain.research_plan import AnalystKey, ResearchPlan
from app.services.company_knowledge_service import (
    KnowledgeOutcome,
    KnowledgeState,
)
from app.services.company_research_service import CompanyResearchService
from app.services.research_strategy import ResearchStrategy


class FakeProfiler:
    def __init__(self, profile: CompanyProfile) -> None:
        self.profile_result = profile
        self.received: CompanyFacts | None = None

    def profile(self, company: CompanyFacts) -> CompanyProfile:
        self.received = company
        return self.profile_result


class FakeStrategy(ResearchStrategy):
    def __init__(self, plan: ResearchPlan) -> None:
        self.plan = plan

    def create_plan(self) -> ResearchPlan:
        return self.plan


class FakeStrategyFactory:
    def __init__(self, strategy: ResearchStrategy) -> None:
        self.strategy = strategy
        self.received: CompanyProfile | None = None

    def playbook(self, profile: CompanyProfile) -> InvestmentPlaybook:
        self.received = profile
        return PLAYBOOKS[PlaybookKind.SOFTWARE]

    def create(self, profile: CompanyProfile) -> ResearchStrategy:
        self.received = profile
        return self.strategy


class FakeExecutor:
    def __init__(self, opinions: list[object]) -> None:
        self.opinions = opinions
        self.received_plan: ResearchPlan | None = None
        self.received_context: CompanyResearchContext | None = None

    def execute(
        self,
        plan: ResearchPlan,
        context: CompanyResearchContext,
    ) -> list[object]:
        self.received_plan = plan
        self.received_context = context
        return self.opinions


class KnowledgeStub:
    """No document is fetched and no model is called in a unit test."""

    def __init__(self) -> None:
        self.asked: list[str] = []

    def established(self, symbol: str) -> KnowledgeOutcome:
        self.asked.append(symbol)

        return KnowledgeOutcome(state=KnowledgeState.UNAVAILABLE)


def make_company() -> CompanyFacts:
    return CompanyFacts(
        instrument_id=1,
        symbol="TEST",
        name="Test Company",
        asset_type="stock",
        exchange="NASDAQ",
        current_price=100.0,
        daily_change_pct=0.01,
        market_cap=1_000_000_000.0,
        forward_pe=20.0,
        fundamentals_reading=Provenance(
            source="Yahoo Finance",
            observed_at=datetime.now(UTC),
        ),
    )


def test_company_research_service_uses_research_pipeline() -> None:
    company = make_company()

    profile = CompanyProfile(
        asset_class=AssetClass.STOCK,
        sector=Sector.TECHNOLOGY,
        industry="Software",
    )

    plan = ResearchPlan(
        objective="Evaluate long-term investment attractiveness.",
        questions=("Can earnings continue growing?",),
        analyst_keys=(
            AnalystKey.GROWTH,
            AnalystKey.PROFITABILITY,
            AnalystKey.BALANCE_SHEET,
            AnalystKey.CASH_FLOW,
        ),
    )

    growth = object()
    profitability = object()
    balance_sheet = object()
    cash_flow = object()

    profiler = FakeProfiler(profile)
    strategy = FakeStrategy(plan)
    strategy_factory = FakeStrategyFactory(strategy)
    executor = FakeExecutor(
        [
            growth,
            profitability,
            balance_sheet,
            cash_flow,
        ]
    )

    knowledge = KnowledgeStub()

    service = CompanyResearchService(
        profiler=profiler,
        strategy_factory=strategy_factory,
        executor=executor,
        knowledge_service=knowledge,
    )

    result = asyncio.run(service.analyze(company))

    assert profiler.received is company
    assert strategy_factory.received is profile
    assert executor.received_plan is plan
    assert executor.received_context == CompanyResearchContext(
        facts=company,
        profile=profile,
    )

    # Keyed by the analyst that produced it, in the order the plan asked.
    # Named fields could not express a security read any other way, which
    # is why every security was read the same way.
    assert result.opinion(AnalystKey.GROWTH) is growth
    assert result.opinion(AnalystKey.PROFITABILITY) is profitability
    assert result.opinion(AnalystKey.BALANCE_SHEET) is balance_sheet
    assert result.opinion(AnalystKey.CASH_FLOW) is cash_flow

    # And it carries the playbook that chose them.
    assert result.playbook.kind is PlaybookKind.SOFTWARE

    # Structural knowledge is asked for through its own service, so
    # nothing in the research pipeline reaches a regulator or a model.
    assert knowledge.asked == ["TEST"]
    assert result.knowledge_state == KnowledgeState.UNAVAILABLE.value
