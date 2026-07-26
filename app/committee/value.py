from app.committee.base import CommitteeMember
from app.domain.committee_context import CommitteeContext
from app.domain.committee_opinion import CommitteeOpinion


class ValueCommittee(CommitteeMember):
    def evaluate(
        self,
        context: CommitteeContext,
    ) -> CommitteeOpinion:
        if context.valuation is None:
            return CommitteeOpinion(
                member="Value",
                vote="HOLD",
                confidence=50,
                rationale="No valuation data available.",
            )

        pe = context.valuation.forward_pe

        if pe is None:
            return CommitteeOpinion(
                member="Value",
                vote="HOLD",
                confidence=50,
                rationale="Forward P/E unavailable.",
            )

        if pe < 18:
            return CommitteeOpinion(
                member="Value",
                vote="BUY",
                confidence=85,
                rationale="Forward P/E is attractive.",
            )

        if pe > 30:
            return CommitteeOpinion(
                member="Value",
                vote="HOLD",
                confidence=80,
                rationale="Forward P/E is elevated.",
            )

        return CommitteeOpinion(
            member="Value",
            vote="HOLD",
            confidence=70,
            rationale="Forward P/E is reasonable.",
        )
