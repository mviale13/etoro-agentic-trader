"""Portfolio reasoning engine."""

from __future__ import annotations

from app.application.brain.reasoning.models.assessment import Evidence
from app.application.brain.reasoning.models.portfolio_assessment import (
    PortfolioAssessment,
)
from app.brain import Brain
from app.domain.brain_context import BrainContext
from app.domain.portfolio_snapshot import PortfolioSnapshot


class PortfolioReasoner:
    """
    Transform the Brain's portfolio knowledge into a structured assessment.

    New callers should provide a Brain. BrainContext remains temporarily
    supported while the existing application pipeline is migrated.
    """

    def assess(
        self,
        source: Brain | BrainContext,
    ) -> PortfolioAssessment:
        portfolio = self._portfolio_from(source)

        diversification = self._diversification_score(portfolio)
        concentration = self._concentration_risk(portfolio)
        liquidity = self._liquidity_score(portfolio)

        health = (
            diversification * 0.40 + (1.0 - concentration) * 0.35 + liquidity * 0.25
        )

        confidence = max(0.50, 1.0 - concentration)

        strengths: list[str] = []
        weaknesses: list[str] = []
        evidence: list[Evidence] = []

        if diversification >= 0.70:
            strengths.append("Well diversified portfolio")
            evidence.append(
                Evidence(
                    description=(
                        f"Portfolio contains {portfolio.positions} positions."
                    ),
                    source="PortfolioSnapshot",
                    strength=0.90,
                )
            )
        else:
            weaknesses.append("Limited diversification")

        if concentration >= 0.40:
            weaknesses.append("High concentration risk")
            evidence.append(
                Evidence(
                    description=(
                        "Largest holding represents "
                        f"{portfolio.largest_position_pct:.1f}% "
                        "of the portfolio."
                    ),
                    source="PortfolioSnapshot",
                    strength=0.95,
                )
            )

        if liquidity >= 0.20:
            strengths.append("Healthy liquidity")

        weaknesses.extend(portfolio.risk_flags)

        return PortfolioAssessment(
            health_score=health,
            diversification_score=diversification,
            concentration_risk=concentration,
            liquidity_score=liquidity,
            confidence=confidence,
            strengths=tuple(strengths),
            weaknesses=tuple(weaknesses),
            evidence=tuple(evidence),
        )

    def _portfolio_from(
        self,
        source: Brain | BrainContext,
    ) -> PortfolioSnapshot:
        if isinstance(source, Brain):
            return source.portfolio

        return source.portfolio

    def _diversification_score(
        self,
        portfolio: PortfolioSnapshot,
    ) -> float:
        return float(min(portfolio.positions / 20.0, 1.0))

    def _concentration_risk(
        self,
        portfolio: PortfolioSnapshot,
    ) -> float:
        return float(min(portfolio.largest_position_pct / 100.0, 1.0))

    def _liquidity_score(
        self,
        portfolio: PortfolioSnapshot,
    ) -> float:
        return float(min(portfolio.allocation.cash / 100.0, 1.0))
