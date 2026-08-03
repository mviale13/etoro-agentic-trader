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
from app.domain.decision_history import DecisionHistory
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
        history: DecisionHistory | None = None,
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
            # The one part of the case that is about this security rather
            # than about the account holding it.
            evidence_weighed=decision.evidence_weighed,
            previous_decisions=self._previous_decisions(
                history,
                decision,
            ),
        )

    @staticmethod
    def _previous_decisions(
        history: DecisionHistory | None,
        decision: ExecutiveDecision,
    ) -> str | None:
        """
        State what the Artificial CIO decided about this symbol before.

        Returns None when nothing was ever recorded. A symbol the CIO is
        judging for the first time has no history, and inventing one — "no
        change" — would report an observation that was never made.
        """

        if history is None or history.is_empty:
            return None

        run = history.current_run
        previous_state = run[-1].state
        since = run[0].decided_at.date().isoformat()
        occurrences = len(run)

        if previous_state is decision.state:
            if occurrences == 1:
                return (
                    f"{decision.state.value} was also the previous decision, "
                    f"recorded on {since}."
                )

            return (
                f"{decision.state.value} has been the decision since {since}, "
                f"across {occurrences} recorded decisions."
            )

        held = (
            f"recorded once, on {since}"
            if occurrences == 1
            else f"the decision since {since}, across {occurrences} recorded decisions"
        )

        return (
            f"Changed from {previous_state.value} to {decision.state.value}. "
            f"{previous_state.value} was {held}."
        )

    @staticmethod
    def _committee_confidence(
        committee_opinions: tuple[CommitteeOpinion, ...],
    ) -> float:
        # Only committees that formed a view are averaged. One that could
        # not counts as silence, not as opposition.
        stated = [
            opinion.confidence
            for opinion in committee_opinions
            if opinion.confidence is not None
        ]

        if not stated:
            return 0.0

        return max(0.0, min(1.0, sum(stated) / len(stated)))

    @staticmethod
    def _unique(
        values: tuple[str, ...] | list[str],
    ) -> tuple[str, ...]:
        return tuple(dict.fromkeys(value for value in values if value))
