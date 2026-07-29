"""Build a durable investment thesis from executive evaluation outputs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.application.brain.reasoning.reasoning_snapshot import (
    ReasoningSnapshot,
)
from app.application.committees.models.committee_opinion import (
    CommitteeOpinion,
)
from app.domain.executive_decision import ExecutiveDecision
from app.domain.thesis.investment_thesis import InvestmentThesis


@dataclass(slots=True)
class InvestmentThesisBuilder:
    """Translate reasoning, committee opinions and a decision into a thesis."""

    default_holding_period: str = "3-5 years"

    def build(
        self,
        symbol: str,
        reasoning: ReasoningSnapshot,
        committee_opinions: tuple[CommitteeOpinion, ...],
        decision: ExecutiveDecision,
    ) -> InvestmentThesis:
        portfolio = reasoning.portfolio
        market = reasoning.market
        risk = reasoning.risk

        confidence = self._committee_confidence(
            committee_opinions,
        )

        strengths = self._unique(
            (
                *portfolio.strengths,
                *market.opportunities,
            )
        )

        risks = self._unique(
            (
                *portfolio.weaknesses,
                *market.risks,
                *risk.risk_factors,
            )
        )

        catalysts = self._unique(
            market.opportunities,
        )

        invalidation_conditions = self._unique(
            (
                *portfolio.weaknesses,
                *market.risks,
                *risk.risk_factors,
            )
        )

        return InvestmentThesis(
            symbol=symbol,
            recommendation=decision.state.value,
            confidence=confidence,
            summary=decision.rationale,
            strengths=strengths,
            risks=risks,
            catalysts=catalysts,
            invalidation_conditions=invalidation_conditions,
            expected_holding_period=self.default_holding_period,
            created_at=datetime.now(UTC),
        )

    @staticmethod
    def _committee_confidence(
        committee_opinions: tuple[CommitteeOpinion, ...],
    ) -> float:
        if not committee_opinions:
            return 0.0

        confidence = sum(opinion.confidence for opinion in committee_opinions) / len(
            committee_opinions
        )

        return max(0.0, min(1.0, confidence))

    @staticmethod
    def _unique(
        values: tuple[str, ...] | list[str],
    ) -> tuple[str, ...]:
        return tuple(dict.fromkeys(value for value in values if value))
