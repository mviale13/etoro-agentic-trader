"""Behavior reasoning engine."""

from __future__ import annotations

from app.application.brain.reasoning.models.assessment import Evidence
from app.application.brain.reasoning.models.behavior_assessment import (
    BehaviorAssessment,
)
from app.domain.brain_context import BrainContext
from app.domain.portfolio_snapshot import PortfolioSnapshot


class BehaviorReasoner:
    """Evaluates investor behaviour and potential biases."""

    def assess(
        self,
        context: BrainContext,
    ) -> BehaviorAssessment:
        portfolio = context.portfolio

        discipline = self._discipline_score(portfolio)
        consistency = 0.80
        emotional_risk = self._emotional_risk(portfolio)
        policy_alignment = 0.80

        biases: list[str] = []
        positives: list[str] = []
        evidence: list[Evidence] = []

        if portfolio.allocation.cash > 40:
            biases.append("Possible hesitation to deploy capital")
            evidence.append(
                Evidence(
                    description=(
                        f"Cash allocation is {portfolio.allocation.cash:.1f}%."
                    ),
                    source="PortfolioSnapshot",
                    strength=0.90,
                )
            )
        else:
            positives.append("Capital is largely invested")

        if portfolio.positions >= 10:
            positives.append("Well diversified portfolio")

        if portfolio.largest_position_pct > 25:
            biases.append("Potential concentration bias")
            evidence.append(
                Evidence(
                    description=(
                        f"Largest holding represents "
                        f"{portfolio.largest_position_pct:.1f}% "
                        "of the portfolio."
                    ),
                    source="PortfolioSnapshot",
                    strength=0.85,
                )
            )

        return BehaviorAssessment(
            discipline_score=discipline,
            consistency_score=consistency,
            emotional_risk_score=emotional_risk,
            policy_alignment_score=policy_alignment,
            confidence=0.75,
            observed_biases=tuple(biases),
            positive_behaviors=tuple(positives),
            evidence=tuple(evidence),
        )

    def _discipline_score(
        self,
        portfolio: PortfolioSnapshot,
    ) -> float:
        if portfolio.positions >= 10:
            return 0.90
        if portfolio.positions >= 5:
            return 0.70
        return 0.40

    def _emotional_risk(
        self,
        portfolio: PortfolioSnapshot,
    ) -> float:
        if portfolio.allocation.cash > 40:
            return 0.70
        if portfolio.allocation.cash > 20:
            return 0.50
        return 0.20
