from app.committee.base import CommitteeMember
from app.domain.committee_context import CommitteeContext
from app.domain.committee_opinion import CommitteeOpinion


class DiversificationCommittee(CommitteeMember):
    def evaluate(
        self,
        context: CommitteeContext,
    ) -> CommitteeOpinion:
        portfolio = context.portfolio
        policy = context.policy

        if portfolio.largest_position_pct > policy.constraints.max_single_position:
            return CommitteeOpinion(
                member="Diversification",
                vote="HOLD",
                confidence=95,
                rationale=("Largest position exceeds policy limit."),
            )

        return CommitteeOpinion(
            member="Diversification",
            vote="BUY",
            confidence=85,
            rationale="Portfolio diversification is acceptable.",
        )
