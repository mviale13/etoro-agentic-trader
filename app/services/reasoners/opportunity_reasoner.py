from app.domain.brain_context import BrainContext
from app.domain.opportunity import Opportunity


class OpportunityReasoner:
    def analyze(
        self,
        context: BrainContext,
    ) -> list[Opportunity]:
        opportunities: list[Opportunity] = []

        policy = context.investment_policy

        if policy is None:
            return opportunities

        cash = context.portfolio.allocation.cash

        if cash <= policy.target.cash:
            return opportunities

        opportunities.append(
            Opportunity(
                symbol="BTC",
                action="BUY",
                score=92,
                policy_fit=95,
                committee_confidence=72,
                market_score=90,
                diversification_score=85,
                reason=("Matches your Investment Policy and excess cash allocation."),
            )
        )

        return opportunities
