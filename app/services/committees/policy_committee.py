from app.domain.committee_vote import CommitteeVote
from app.domain.policy_assessment import PolicyAssessment


class PolicyCommittee:
    def vote(
        self,
        assessment: PolicyAssessment,
    ) -> CommitteeVote:
        if not assessment.aligned:
            return CommitteeVote(
                committee="Policy",
                recommendation="HOLD",
                confidence=100,
                weight=0.25,
                rationale=("The proposed investment violates the Investment Policy."),
                evidence=assessment.rationale,
            )

        return CommitteeVote(
            committee="Policy",
            recommendation="BUY",
            confidence=95,
            weight=0.25,
            rationale=(
                "The proposed investment is aligned with the Investment Policy."
            ),
            evidence=assessment.rationale,
        )
