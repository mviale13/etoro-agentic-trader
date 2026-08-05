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
from app.domain.decision_history import DecisionHistory, RecordedScores
from app.domain.executive_decision import DecisionEvidence, ExecutiveDecision
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
        history: DecisionHistory | None = None,
        evidence: DecisionEvidence | None = None,
    ) -> InvestmentThesis:
        portfolio = reasoning.portfolio
        market = reasoning.market
        risk = reasoning.risk

        confidence = self._committee_confidence(
            committee_opinions,
        )

        # The security's own, as the Artificial CIO weighed them. These used
        # to be the portfolio's strengths and the market's opportunities,
        # which are the same under every symbol, so one investment case read
        # exactly like the next.
        strengths = self._unique(decision.key_strengths)

        risks = self._unique(decision.key_risks)

        context_risks = self._unique(decision.context_risks)

        context_strengths = self._unique(
            (
                *portfolio.strengths,
                *market.opportunities,
                *reasoning.opportunity.opportunities,
            )
        )

        # The security's own, dated, as the Artificial CIO carried them.
        # These used to be the market's opportunities, which are the same
        # under every symbol — so "Stable market conditions" was offered as
        # the reason to act on MSFT, and on everything else. Those are
        # context, and they are stated as context above.
        catalysts = self._unique(decision.catalysts)

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
            conviction=decision.conviction,
            summary=decision.rationale,
            strengths=strengths,
            risks=risks,
            catalysts=catalysts,
            invalidation_conditions=invalidation_conditions,
            expected_holding_period=self.default_holding_period,
            created_at=datetime.now(UTC),
            evidence_weighed=decision.evidence_weighed,
            context_strengths=context_strengths,
            context_risks=context_risks,
            evidence_as_of=decision.evidence_as_of,
            trend=(
                history.trend_against(decision.state) if history is not None else None
            ),
            conviction_change=(
                history.conviction_change_against(
                    decision.conviction,
                    self._scores(evidence),
                )
                if history is not None
                else None
            ),
        )

    @staticmethod
    def _scores(evidence: DecisionEvidence | None) -> RecordedScores:
        """Today's scores in the shape the record keeps them."""

        if evidence is None:
            return RecordedScores()

        return RecordedScores(
            quality=evidence.quality_score,
            evidence=evidence.evidence_score,
            valuation=evidence.valuation_score,
            safety=evidence.safety_score,
            portfolio_fit=evidence.portfolio_fit_score,
        )

    @staticmethod
    def _committee_confidence(
        committee_opinions: tuple[CommitteeOpinion, ...],
    ) -> float | None:
        """
        How far the committees that spoke agreed, or nothing at all.

        A committee that could not form a view counts as silence, not as
        opposition. When none of them could, the answer is that agreement
        was not measured — reporting 0% would say they disagreed.
        """

        stated = [
            opinion.confidence
            for opinion in committee_opinions
            if opinion.confidence is not None
        ]

        if not stated:
            return None

        return max(0.0, min(1.0, sum(stated) / len(stated)))

    @staticmethod
    def _unique(
        values: tuple[str, ...] | list[str],
    ) -> tuple[str, ...]:
        return tuple(dict.fromkeys(value for value in values if value))
