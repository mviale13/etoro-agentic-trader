"""Risk reasoning engine."""

from __future__ import annotations

from app.application.brain.reasoning.models.assessment import Evidence
from app.application.brain.reasoning.models.risk_assessment import (
    RiskAssessment,
)
from app.domain.brain_context import BrainContext
from app.domain.portfolio_snapshot import PortfolioSnapshot


class RiskReasoner:
    """Evaluates overall portfolio risk."""

    def assess(
        self,
        context: BrainContext,
    ) -> RiskAssessment:
        portfolio = context.portfolio

        liquidity = self._liquidity_risk(portfolio)
        concentration = self._concentration_risk(portfolio)

        market = 0.50
        drawdown = 0.50

        overall = (liquidity + concentration + market + drawdown) / 4.0

        risk_factors: list[str] = []
        mitigants: list[str] = []
        evidence: list[Evidence] = []

        if portfolio.allocation.cash < 10:
            risk_factors.append("Low cash buffer")

            evidence.append(
                Evidence(
                    description=(
                        f"Cash allocation is only {portfolio.allocation.cash:.1f}%."
                    ),
                    source="PortfolioSnapshot",
                    strength=0.95,
                )
            )
        else:
            mitigants.append("Healthy cash allocation")

        if portfolio.largest_position_pct > 25:
            risk_factors.append("High portfolio concentration")

            evidence.append(
                Evidence(
                    description=(
                        f"Largest holding represents "
                        f"{portfolio.largest_position_pct:.1f}% "
                        "of the portfolio."
                    ),
                    source="PortfolioSnapshot",
                    strength=0.90,
                )
            )

        return RiskAssessment(
            overall_risk_score=overall,
            market_risk_score=market,
            concentration_risk_score=concentration,
            liquidity_risk_score=liquidity,
            drawdown_risk_score=drawdown,
            confidence=0.80,
            risk_factors=tuple(risk_factors),
            mitigants=tuple(mitigants),
            evidence=tuple(evidence),
        )

    def _liquidity_risk(
        self,
        portfolio: PortfolioSnapshot,
    ) -> float:
        return max(0.0, min((10.0 - portfolio.allocation.cash) / 10.0, 1.0))

    def _concentration_risk(
        self,
        portfolio: PortfolioSnapshot,
    ) -> float:
        return min(portfolio.largest_position_pct / 100.0, 1.0)
