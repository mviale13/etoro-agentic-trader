from app.domain.committee_vote import CommitteeVote
from app.domain.opportunity_facts import OpportunityFacts


class OpportunityCommittee:
    def vote(
        self,
        facts: OpportunityFacts,
    ) -> CommitteeVote:
        confidence = 50
        evidence: list[str] = []

        if facts.daily_change_percent > 2:
            confidence += 20
            evidence.append("Strong positive daily momentum.")

        if facts.asset_type == "crypto":
            confidence += 5
            evidence.append("Digital asset supported.")

        recommendation = "BUY" if confidence >= 70 else "HOLD"

        return CommitteeVote(
            committee="Opportunity",
            recommendation=recommendation,
            confidence=confidence,
            weight=0.25,
            rationale=("Opportunity evaluated using current market characteristics."),
            evidence=tuple(evidence),
        )
