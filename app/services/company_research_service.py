from app.analysts.balance_sheet_analyst import BalanceSheetAnalyst
from app.analysts.cash_flow_analyst import CashFlowAnalyst
from app.analysts.growth_analyst import GrowthAnalyst
from app.analysts.profitability_analyst import ProfitabilityAnalyst
from app.domain.company_facts import CompanyFacts
from app.domain.company_research import CompanyResearch


class CompanyResearchService:
    def __init__(
        self,
        *,
        growth_analyst: GrowthAnalyst | None = None,
        profitability_analyst: ProfitabilityAnalyst | None = None,
        balance_sheet_analyst: BalanceSheetAnalyst | None = None,
        cash_flow_analyst: CashFlowAnalyst | None = None,
    ) -> None:
        self._growth_analyst = growth_analyst or GrowthAnalyst()
        self._profitability_analyst = profitability_analyst or ProfitabilityAnalyst()
        self._balance_sheet_analyst = balance_sheet_analyst or BalanceSheetAnalyst()
        self._cash_flow_analyst = cash_flow_analyst or CashFlowAnalyst()

    def analyze(
        self,
        company: CompanyFacts,
    ) -> CompanyResearch:
        return CompanyResearch(
            growth=self._growth_analyst.analyze(company),
            profitability=self._profitability_analyst.analyze(company),
            balance_sheet=self._balance_sheet_analyst.analyze(company),
            cash_flow=self._cash_flow_analyst.analyze(company),
        )
