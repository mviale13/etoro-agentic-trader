"""Coordinates the cognitive reasoning layer."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.application.brain.reasoning.market_reasoner import MarketReasoner
from app.application.brain.reasoning.portfolio_analyst import PortfolioAnalyst
from app.application.brain.reasoning.reasoning_snapshot import (
    ReasoningSnapshot,
)
from app.application.brain.reasoning.risk_reasoner import RiskReasoner
from app.brain import Brain


@dataclass(slots=True)
class ReasoningService:
    """
    Runs every cognitive analyst and reasoner.

    Brain
        ↓
    PortfolioAnalyst
    MarketReasoner
    RiskReasoner
        ↓
    ReasoningSnapshot
    """

    portfolio_analyst: PortfolioAnalyst = field(default_factory=PortfolioAnalyst)

    market_reasoner: MarketReasoner = field(default_factory=MarketReasoner)

    risk_reasoner: RiskReasoner = field(default_factory=RiskReasoner)

    def reason(
        self,
        brain: Brain,
    ) -> ReasoningSnapshot:
        return ReasoningSnapshot(
            portfolio=self.portfolio_analyst.assess(brain),
            market=self.market_reasoner.assess(brain),
            risk=self.risk_reasoner.assess(brain),
        )
