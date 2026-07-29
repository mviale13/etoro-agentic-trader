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
        profile = self._profiler.profile(company)

        context = CompanyResearchContext(
            facts=company,
            profile=profile,
        )

        strategy = self._strategy_factory.create(profile)
        plan = strategy.create_plan()
        opinions = self._executor.execute(plan, context)

        opinions_by_key = dict(zip(plan.analyst_keys, opinions, strict=True))

        return CompanyResearch(
            growth=opinions_by_key[AnalystKey.GROWTH],
            profitability=opinions_by_key[AnalystKey.PROFITABILITY],
            balance_sheet=opinions_by_key[AnalystKey.BALANCE_SHEET],
            cash_flow=opinions_by_key[AnalystKey.CASH_FLOW],
        )
