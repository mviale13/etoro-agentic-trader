from app.committee.base import CommitteeMember
from app.domain.committee_context import CommitteeContext
from app.domain.committee_opinion import CommitteeOpinion


class CashCommittee(CommitteeMember):
    def evaluate(
        self,
        context: CommitteeContext,
    ) -> CommitteeOpinion:
        current_cash = context.portfolio.allocation.cash
        target_cash = context.policy.target.cash
        threshold = context.policy.constraints.rebalance_threshold

        difference = current_cash - target_cash

        if difference > threshold:
            return CommitteeOpinion(
                member="Cash",
                vote="BUY",
                confidence=90,
                rationale=(
                    f"Cash allocation is {current_cash:.1f}%, "
                    f"above the {target_cash:.1f}% target."
                ),
            )

        if difference < -threshold:
            return CommitteeOpinion(
                member="Cash",
                vote="HOLD",
                confidence=90,
                rationale=(
                    f"Cash allocation is {current_cash:.1f}%, "
                    f"below the {target_cash:.1f}% target."
                ),
            )

        return CommitteeOpinion(
            member="Cash",
            vote="HOLD",
            confidence=80,
            rationale="Cash allocation is within the rebalance threshold.",
        )
