"""Coordinates the cognitive reasoning layer."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.application.brain.reasoning.market_reasoner import MarketReasoner
from app.application.brain.reasoning.portfolio_reasoner import PortfolioReasoner
from app.application.brain.reasoning.reasoning_snapshot import (
    ReasoningSnapshot,
)
from app.application.brain.reasoning.risk_reasoner import RiskReasoner
from app.brain import Brain


@dataclass(slots=True)
class ReasoningService:
    """
    Runs every cognitive reasoner.

    Brain
        ↓
    PortfolioReasoner
    MarketReasoner
    RiskReasoner
        ↓
    ReasoningSnapshot
    """

    portfolio_reasoner: PortfolioReasoner = field(default_factory=PortfolioReasoner)

    market_reasoner: MarketReasoner = field(default_factory=MarketReasoner)

    risk_reasoner: RiskReasoner = field(default_factory=RiskReasoner)

    def reason(
        self,
        brain: Brain,
    ) -> ReasoningSnapshot:
        return ReasoningSnapshot(
            portfolio=self.portfolio_reasoner.assess(brain),
            market=self.market_reasoner.assess(brain),
            risk=self.risk_reasoner.assess(brain),
        )
