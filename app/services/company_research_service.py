from typing import Any

from app.analysts.balance_sheet_analyst import BalanceSheetAnalyst
from app.analysts.cash_flow_analyst import CashFlowAnalyst
from app.analysts.growth_analyst import GrowthAnalyst
from app.analysts.profitability_analyst import ProfitabilityAnalyst
from app.domain.company_facts import CompanyFacts
from app.domain.company_research import CompanyResearch
from app.domain.company_research_context import CompanyResearchContext
from app.domain.playbook import InvestmentPlaybook
from app.domain.research_plan import AnalystKey
from app.services.analyst_registry import AnalystRegistry
from app.services.company_facts_analyst_adapter import CompanyFactsAnalystAdapter
from app.services.company_knowledge_service import (
    CompanyKnowledgeService,
    KnowledgeOutcome,
)
from app.services.company_profiler import CompanyProfiler
from app.services.research_executor import ResearchExecutor
from app.services.research_strategy_factory import ResearchStrategyFactory


class CompanyResearchService:
    def __init__(
        self,
        *,
        profiler: Any | None = None,
        strategy_factory: Any | None = None,
        executor: ResearchExecutor | Any | None = None,
        knowledge_service: Any | None = None,
        growth_analyst: GrowthAnalyst | None = None,
        profitability_analyst: ProfitabilityAnalyst | None = None,
        balance_sheet_analyst: BalanceSheetAnalyst | None = None,
        cash_flow_analyst: CashFlowAnalyst | None = None,
    ) -> None:
        self._profiler = profiler or CompanyProfiler()
        self._strategy_factory = strategy_factory or ResearchStrategyFactory()

        # Cache-first and on demand. Acquisition and extraction stay
        # behind this interface: nothing in the research pipeline calls a
        # regulator or a model directly, and a company whose latest
        # document is already read costs one small lookup.
        self._knowledge = knowledge_service or CompanyKnowledgeService()

        if executor is not None:
            self._executor = executor
            return

        registry = AnalystRegistry(
            {
                AnalystKey.GROWTH: CompanyFactsAnalystAdapter(
                    growth_analyst or GrowthAnalyst()
                ),
                AnalystKey.PROFITABILITY: CompanyFactsAnalystAdapter(
                    profitability_analyst or ProfitabilityAnalyst()
                ),
                AnalystKey.BALANCE_SHEET: CompanyFactsAnalystAdapter(
                    balance_sheet_analyst or BalanceSheetAnalyst()
                ),
                AnalystKey.CASH_FLOW: CompanyFactsAnalystAdapter(
                    cash_flow_analyst or CashFlowAnalyst()
                ),
            }
        )
        self._executor = ResearchExecutor(registry)

    async def analyze(
        self,
        company: CompanyFacts,
    ) -> CompanyResearch:
        """
        Read this security the way its own playbook says it should be read.

        Security → profile → playbook → plan → analysts, in that order and
        with nothing skipped. A security whose playbook asks for no company
        analysts still produces research: the playbook explaining why none
        were asked is the answer, and it is a better one than silence.
        """

        profile = self._profiler.profile(company)

        playbook = self._strategy_factory.playbook(profile)

        context = CompanyResearchContext(
            facts=company,
            profile=profile,
        )

        plan = self._strategy_factory.create(profile).create_plan()

        opinions = self._executor.execute(plan, context) if plan.analyst_keys else ()

        acquired = await self._structural_knowledge(playbook, company.symbol)

        return CompanyResearch(
            playbook=playbook,
            opinions=dict(zip(plan.analyst_keys, opinions, strict=True)),
            knowledge=acquired.knowledge if acquired is not None else None,
            knowledge_state=acquired.state.value if acquired is not None else None,
        )

    async def _structural_knowledge(
        self,
        playbook: InvestmentPlaybook,
        symbol: str,
    ) -> KnowledgeOutcome | None:
        """
        The company's own account of itself, where there is a company.

        Only asked for securities whose playbook expects company
        accounts. A token and a fund do not publish them, and asking
        anyway is not merely wasteful — ticker namespaces collide, and
        `BTC` resolves against the SEC to a trust that issues shares
        tracking Bitcoin. That trust files a real annual report about a
        real business, and reading it would have attached a fund's
        segments to a cryptocurrency.

        A failure here thins the analysis; it never stops it, because the
        financial analysts read figures that do not depend on it.
        """

        if not playbook.analysts:
            return None

        return await self._knowledge.knowledge(symbol)
