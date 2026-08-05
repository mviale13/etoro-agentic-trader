from typing import Any

from app.analysts.balance_sheet_analyst import BalanceSheetAnalyst
from app.analysts.cash_flow_analyst import CashFlowAnalyst
from app.analysts.growth_analyst import GrowthAnalyst
from app.analysts.profitability_analyst import ProfitabilityAnalyst
from app.domain.company_facts import CompanyFacts
from app.domain.company_research import CompanyResearch
from app.domain.company_research_context import CompanyResearchContext
from app.domain.research_plan import AnalystKey
from app.services.analyst_registry import AnalystRegistry
from app.services.company_facts_analyst_adapter import CompanyFactsAnalystAdapter
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
        growth_analyst: GrowthAnalyst | None = None,
        profitability_analyst: ProfitabilityAnalyst | None = None,
        balance_sheet_analyst: BalanceSheetAnalyst | None = None,
        cash_flow_analyst: CashFlowAnalyst | None = None,
    ) -> None:
        self._profiler = profiler or CompanyProfiler()
        self._strategy_factory = strategy_factory or ResearchStrategyFactory()

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

    def analyze(
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

        return CompanyResearch(
            playbook=playbook,
            opinions=dict(zip(plan.analyst_keys, opinions, strict=True)),
        )
