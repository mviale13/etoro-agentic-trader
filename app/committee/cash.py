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

        if current_cash is None:
            # This committee's entire question is cash against target. With
            # no cash reading it abstains in words rather than voting the
            # neutral option, which would be indistinguishable from having
            # looked and found nothing worth acting on.
            return CommitteeOpinion(
                member="Cash",
                vote="HOLD",
                confidence=0,
                rationale=(
                    "Cash allocation could not be read, so this committee "
                    "has no view; nothing here says the allocation is at, "
                    "above or below its target."
                ),
                abstained_because=(
                    "the broker stated no cash figure, so there is nothing "
                    "to compare against the target"
                ),
            )

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
