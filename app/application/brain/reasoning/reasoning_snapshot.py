"""Immutable output of the cognitive reasoning layer."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.brain.reasoning.models.market_assessment import (
    MarketAssessment,
)
from app.application.brain.reasoning.models.portfolio_assessment import (
    PortfolioAssessment,
)
from app.application.brain.reasoning.models.risk_assessment import (
    RiskAssessment,
)


@dataclass(frozen=True, slots=True)
class ReasoningSnapshot:
    """
    Aggregates every reasoning output produced from a Brain.

    This object represents the Artificial CIO's understanding
    after all cognitive reasoners have completed.
    """

    portfolio: PortfolioAssessment

    market: MarketAssessment

    risk: RiskAssessment
