"""Portfolio reasoning engine."""

from __future__ import annotations

from app.application.brain.analysts import Analyst
from app.application.brain.reasoning.models.assessment import Evidence
from app.application.brain.reasoning.models.portfolio_assessment import (
    PortfolioAssessment,
)
from app.brain import Brain
from app.domain.portfolio_snapshot import PortfolioSnapshot


class PortfolioAnalyst(Analyst[PortfolioAssessment]):
    """Transform the Brain's portfolio knowledge into a structured assessment."""

    #: One term of `cognitive-confidence@1`: the floor under this
    #: analyst's concentration-derived confidence. Named for the
    #: provenance fingerprint.
    CONFIDENCE_FLOOR = 0.50

    def assess(
        self,
        source: Brain,
    ) -> PortfolioAssessment:
        portfolio = source.portfolio

        diversification = self._diversification_score(portfolio)
        concentration = self._concentration_risk(portfolio)
        liquidity = self._liquidity_score(portfolio)

        # Absent while any weighted term is absent. Renormalising the
        # remaining weights would answer a different question under the
        # same name, and a health score is read as complete.
        health = (
            None
            if liquidity is None
            else diversification * 0.40
            + (1.0 - concentration) * 0.35
            + liquidity * 0.25
        )

        confidence = max(self.CONFIDENCE_FLOOR, 1.0 - concentration)

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

        if liquidity is not None and liquidity >= 0.20:
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
    ) -> float | None:
        cash = portfolio.allocation.cash

        if cash is None:
            # Unreadable cash is not zero liquidity. Scoring it would
            # report the least liquid possible account for one nobody
            # measured.
            return None

        return float(min(cash / 100.0, 1.0))
