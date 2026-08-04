from dataclasses import dataclass

from app.domain.balance_sheet_opinion import BalanceSheetOpinion
from app.domain.cash_flow_opinion import CashFlowOpinion
from app.domain.growth_opinion import GrowthOpinion
from app.domain.profitability_opinion import ProfitabilityOpinion


@dataclass(frozen=True, slots=True)
class CompanyResearch:
    """Complete fundamental research produced for a company.

    CompanyResearch is the aggregate root of the company research domain.
    It groups the conclusions of all specialist analysts into a single,
    immutable research package that can be consumed by committees,
    recommendation engines, or executive decision makers.

    Every company research contains exactly one opinion from each
    fundamental analyst.
    """

    growth: GrowthOpinion
    profitability: ProfitabilityOpinion
    balance_sheet: BalanceSheetOpinion
    cash_flow: CashFlowOpinion
