from dataclasses import dataclass

from app.domain.balance_sheet_opinion import BalanceSheetOpinion
from app.domain.cash_flow_opinion import CashFlowOpinion
from app.domain.growth_opinion import GrowthOpinion
from app.domain.profitability_opinion import ProfitabilityOpinion


@dataclass(frozen=True, slots=True)
class CompanyResearch:
    growth: GrowthOpinion
    profitability: ProfitabilityOpinion
    balance_sheet: BalanceSheetOpinion
    cash_flow: CashFlowOpinion
