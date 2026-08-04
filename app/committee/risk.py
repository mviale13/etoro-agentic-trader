from app.committee.base import CommitteeMember
from app.domain.committee_context import CommitteeContext
from app.domain.committee_evidence import CommitteeEvidence
from app.domain.committee_opinion import CommitteeOpinion


class RiskCommittee(CommitteeMember):
    def evaluate(
        self,
        context: CommitteeContext,
    ) -> CommitteeOpinion:

        volatility = context.intelligence.market.volatility

        evidence = (
            CommitteeEvidence(
                title="Cash allocation",
                value=f"{context.portfolio.allocation.cash:.1f}%",
            ),
            CommitteeEvidence(
                title="Risk flags",
                value=str(len(context.portfolio.risk_flags)),
            ),
            CommitteeEvidence(
                title="Volatility",
                value=volatility,
            ),
        )

        if volatility == "high":
            return CommitteeOpinion(
                member="Risk",
                vote="HOLD",
                confidence=90,
                rationale="High market volatility.",
                evidence=evidence,
            )

        if volatility == "medium":
            return CommitteeOpinion(
                member="Risk",
                vote="HOLD",
                confidence=75,
                rationale="Moderate market volatility.",
                evidence=evidence,
            )

        return CommitteeOpinion(
            member="Risk",
            vote="BUY",
            confidence=80,
            rationale="Low market volatility.",
            evidence=evidence,
        )
