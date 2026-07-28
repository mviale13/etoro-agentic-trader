from app.domain.brain_context import BrainContext
from app.domain.committee_vote import CommitteeVote


class PortfolioCommittee:
    def vote(
        self,
        context: BrainContext,
    ) -> CommitteeVote:
        policy = context.investment_policy

        if policy is None:
            return CommitteeVote(
                committee="Portfolio",
                recommendation="WAIT",
                confidence=100,
                weight=0.30,
                rationale="Investment Policy missing.",
            )

        difference = context.portfolio.allocation.cash - policy.target.cash

        if difference > 5:
            return CommitteeVote(
                committee="Portfolio",
                recommendation="BUY",
                confidence=90,
                weight=0.30,
                rationale="Cash exceeds target allocation.",
            )

        return CommitteeVote(
            committee="Portfolio",
            recommendation="HOLD",
            confidence=75,
            weight=0.30,
            rationale="Portfolio is aligned with policy.",
        )
