from app.committee.base import CommitteeMember
from app.domain.committee_context import CommitteeContext
from app.domain.committee_opinion import CommitteeOpinion


class MomentumCommittee(CommitteeMember):
    def evaluate(
        self,
        context: CommitteeContext,
    ) -> CommitteeOpinion:
        intelligence = context.intelligence

        if intelligence.outlook == "BULLISH":
            return CommitteeOpinion(
                member="Momentum",
                vote="BUY",
                confidence=intelligence.confidence,
                rationale=intelligence.summary,
            )

        if intelligence.outlook == "BEARISH":
            return CommitteeOpinion(
                member="Momentum",
                vote="SELL",
                confidence=intelligence.confidence,
                rationale=intelligence.summary,
            )

        return CommitteeOpinion(
            member="Momentum",
            vote="HOLD",
            confidence=intelligence.confidence,
            rationale=intelligence.summary,
        )
