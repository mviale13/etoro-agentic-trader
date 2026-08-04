from dataclasses import dataclass

from app.application.brain.reasoning.models.capacity_assessment import (
    CapacityAssessment,
)
from app.application.brain.reasoning.models.risk_assessment import RiskAssessment
from app.domain.executive_brief import ExecutiveBrief
from app.domain.insight import Insight
from app.domain.investor_dna import InvestorDNA
from app.domain.observation import Observation
from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.domain.recommendation import Recommendation


@dataclass(frozen=True)
class BrainSnapshot:
    portfolio: PortfolioSnapshot
    recommendation: Recommendation
    observation: Observation
    investor_dna: InvestorDNA
    summary: str
    insights: list[Insight]
    focus: str = "portfolio"
    brief: ExecutiveBrief | None = None

    #: How this account can lose money, measured. Not a judgement about
    #: any security and not a recommendation — which is why it belongs in
    #: what the Brain knows, unlike the executive brief beside it.
    risk: RiskAssessment | None = None

    #: How much room the account has to act, measured against the policy.
    #: A comparison of two facts the investor already stated or the broker
    #: already reported — not a judgement about any security.
    capacity: CapacityAssessment | None = None
