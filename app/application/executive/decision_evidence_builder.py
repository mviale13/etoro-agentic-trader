"""Build Executive DecisionEvidence from the cognitive layer."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.brain.reasoning.reasoning_snapshot import (
    ReasoningSnapshot,
)
from app.application.committees.models.committee_opinion import (
    CommitteeOpinion,
    Recommendation,
)
from app.brain import Brain
from app.domain.executive_decision import DecisionEvidence


@dataclass(slots=True)
class DecisionEvidenceBuilder:
    """
    Translate cognitive outputs into Executive DecisionEvidence.

    The symbol belongs to the investment case being evaluated,
    not to the portfolio snapshot.
    """

    def build(
        self,
        symbol: str,
        brain: Brain,
        reasoning: ReasoningSnapshot,
        committee_opinions: tuple[CommitteeOpinion, ...],
    ) -> DecisionEvidence:
        portfolio = reasoning.portfolio
        market = reasoning.market
        risk = reasoning.risk

        investment = next(
            (
                opinion
                for opinion in committee_opinions
                if opinion.committee == "Investment Committee"
            ),
            None,
        )

        quality = int(portfolio.health_score * 100)

        evidence_score = int(
            (portfolio.confidence + market.confidence + risk.confidence) / 3.0 * 100
        )

        valuation = int(market.momentum_score * 100)

        portfolio_fit = int(
            (portfolio.health_score + (1.0 - risk.overall_risk_score)) / 2.0 * 100
        )

        strengths = tuple(
            dict.fromkeys(
                (
                    *portfolio.strengths,
                    *market.opportunities,
                )
            )
        )

        risks = tuple(
            dict.fromkeys(
                (
                    *portfolio.weaknesses,
                    *market.risks,
                    *risk.risk_factors,
                )
            )
        )

        catalysts = tuple(market.opportunities)

        return DecisionEvidence(
            symbol=symbol,
            quality_score=quality,
            evidence_score=evidence_score,
            valuation_score=valuation,
            risk_score=int(risk.overall_risk_score * 100),
            portfolio_fit_score=portfolio_fit,
            actionable_now=(
                investment is not None
                and investment.recommendation
                in (
                    Recommendation.BUY,
                    Recommendation.STRONG_BUY,
                )
            ),
            hard_reject=False,
            analyst_veto=False,
            strengths=strengths,
            risks=risks,
            missing_evidence=(),
            catalysts=catalysts,
        )
