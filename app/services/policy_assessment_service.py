from app.domain.investment_policy import InvestmentPolicy
from app.domain.opportunity_facts import OpportunityFacts
from app.domain.policy_assessment import PolicyAssessment


class PolicyAssessmentService:
    def assess(
        self,
        policy: InvestmentPolicy,
        opportunity: OpportunityFacts,
        *,
        proposed_position_pct: float,
        current_crypto_pct: float,
    ) -> PolicyAssessment:
        rationale: list[str] = []

        if proposed_position_pct > policy.constraints.max_single_position:
            rationale.append(
                "Proposed position exceeds the maximum single-position limit."
            )

        if opportunity.asset_type == "crypto":
            projected_crypto_pct = current_crypto_pct + proposed_position_pct

            if projected_crypto_pct > policy.constraints.max_crypto:
                rationale.append(
                    "Projected crypto allocation exceeds the Investment Policy limit."
                )

        if rationale:
            return PolicyAssessment(
                aligned=False,
                status="VIOLATION",
                rationale=tuple(rationale),
            )

        return PolicyAssessment(
            aligned=True,
            status="ALIGNED",
            rationale=(
                "The opportunity respects the current Investment Policy limits.",
            ),
        )
