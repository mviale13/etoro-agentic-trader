from app.committee.base import CommitteeMember
from app.domain.committee_context import CommitteeContext
from app.domain.committee_evidence import CommitteeEvidence
from app.domain.committee_opinion import CommitteeOpinion


class MomentumCommittee(CommitteeMember):
    def evaluate(
        self,
        context: CommitteeContext,
    ) -> CommitteeOpinion:
        intelligence = context.intelligence

        evidence = (
            CommitteeEvidence(
                title="Market outlook",
                value=intelligence.outlook,
            ),
            CommitteeEvidence(
                title="Confidence",
                value=str(intelligence.confidence),
            ),
        )

        if intelligence.outlook == "BULLISH":
            return CommitteeOpinion(
                member="Momentum",
                vote="BUY",
                confidence=intelligence.confidence,
                rationale=intelligence.summary,
                evidence=evidence,
            )

        if intelligence.outlook == "BEARISH":
            return CommitteeOpinion(
                member="Momentum",
                vote="SELL",
                confidence=intelligence.confidence,
                rationale=intelligence.summary,
                evidence=evidence,
            )

        return CommitteeOpinion(
            member="Momentum",
            vote="HOLD",
            confidence=intelligence.confidence,
            rationale=intelligence.summary,
            evidence=evidence,
        )
