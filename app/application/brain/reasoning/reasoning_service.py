"""Coordinates the cognitive reasoning layer."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.application.brain.reasoning.behavior_analyst import BehaviorAnalyst
from app.application.brain.reasoning.brain_reasoner import BrainReasoner
from app.application.brain.reasoning.market_analyst import MarketAnalyst
from app.application.brain.reasoning.opportunity_analyst import (
    OpportunityAnalyst,
)
from app.application.brain.reasoning.portfolio_analyst import PortfolioAnalyst
from app.application.brain.reasoning.reasoning_snapshot import (
    ReasoningSnapshot,
)
from app.application.brain.reasoning.risk_analyst import RiskAnalyst
from app.brain import Brain


@dataclass(slots=True)
class ReasoningService(BrainReasoner):
    """
    Canonical implementation of the BrainReasoner.

    Brain
        ↓
    PortfolioAnalyst
    MarketAnalyst
    RiskAnalyst
    BehaviorAnalyst
        ↓
    OpportunityAnalyst
        ↓
    ReasoningSnapshot

    The OpportunityAnalyst synthesizes the specialist assessments, so it runs
    once they have completed.

    Responsibilities:
    - Coordinate cognitive analysts.
    - Produce an immutable ReasoningSnapshot.

    This service must never:
    - Fetch external data.
    - Mutate the Brain.
    - Make investment decisions.
    - Render UI.
    """

    portfolio_analyst: PortfolioAnalyst = field(default_factory=PortfolioAnalyst)

    market_analyst: MarketAnalyst = field(default_factory=MarketAnalyst)

    risk_analyst: RiskAnalyst = field(default_factory=RiskAnalyst)

    behavior_analyst: BehaviorAnalyst = field(default_factory=BehaviorAnalyst)

    opportunity_analyst: OpportunityAnalyst = field(default_factory=OpportunityAnalyst)

    def reason(
        self,
        brain: Brain,
    ) -> ReasoningSnapshot:
        """Run all analysts and produce the canonical reasoning snapshot."""

        portfolio = self.portfolio_analyst.assess(brain)
        market = self.market_analyst.assess(brain)
        risk = self.risk_analyst.assess(brain)
        behavior = self.behavior_analyst.assess(brain)

        opportunity = self.opportunity_analyst.assess(
            portfolio=portfolio,
            market=market,
            risk=risk,
            behavior=behavior,
        )

        return ReasoningSnapshot(
            portfolio=portfolio,
            market=market,
            risk=risk,
            behavior=behavior,
            opportunity=opportunity,
        )
