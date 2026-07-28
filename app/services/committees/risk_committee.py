from app.domain.committee_vote import CommitteeVote
from app.domain.risk_assessment import RiskAssessment


class RiskCommittee:
    def vote(
        self,
        assessment: RiskAssessment,
    ) -> CommitteeVote:
        if assessment.overall == "HIGH":
            return CommitteeVote(
                committee="Risk",
                recommendation="HOLD",
                confidence=90,
                weight=0.30,
                rationale=(
                    "Current risk conditions do not support increasing exposure."
                ),
                evidence=assessment.rationale,
            )

        if assessment.overall == "MEDIUM":
            return CommitteeVote(
                committee="Risk",
                recommendation="HOLD",
                confidence=70,
                weight=0.30,
                rationale=(
                    "Risk conditions require caution before increasing exposure."
                ),
                evidence=assessment.rationale,
            )

        return CommitteeVote(
            committee="Risk",
            recommendation="BUY",
            confidence=75,
            weight=0.30,
            rationale=("Current risk conditions are within acceptable limits."),
            evidence=assessment.rationale,
        )
