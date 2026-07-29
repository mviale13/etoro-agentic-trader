"""Executive Committee orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.application.brain.reasoning.reasoning_snapshot import (
    ReasoningSnapshot,
)
from app.application.committees.investment_committee import (
    InvestmentCommittee,
)
from app.application.committees.models.committee_opinion import (
    CommitteeOpinion,
)
from app.application.committees.risk_committee import (
    RiskCommittee,
)
from app.brain import Brain


@dataclass(slots=True)
class CommitteeService:
    investment: InvestmentCommittee = field(default_factory=InvestmentCommittee)

    risk: RiskCommittee = field(default_factory=RiskCommittee)

    def review(
        self,
        brain: Brain,
        reasoning: ReasoningSnapshot,
    ) -> tuple[CommitteeOpinion, ...]:

        return (
            self.investment.review(
                brain,
                reasoning,
            ),
            self.risk.review(
                brain,
                reasoning,
            ),
        )
