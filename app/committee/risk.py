from app.committee.base import CommitteeMember
from app.domain.committee_context import CommitteeContext
from app.domain.committee_opinion import CommitteeOpinion


class RiskCommittee(CommitteeMember):
    def evaluate(
        self,
        context: CommitteeContext,
    ) -> CommitteeOpinion:
        volatility = context.intelligence.market.volatility

        if volatility == "high":
            return CommitteeOpinion(
                member="Risk",
                vote="HOLD",
                confidence=90,
                rationale="High market volatility.",
            )

        if volatility == "medium":
            return CommitteeOpinion(
                member="Risk",
                vote="HOLD",
                confidence=75,
                rationale="Moderate market volatility.",
            )

        return CommitteeOpinion(
            member="Risk",
            vote="BUY",
            confidence=80,
            rationale="Low market volatility.",
        )
