from app.domain.brain_context import BrainContext
from app.domain.committee_vote import CommitteeVote
from app.services.committees.portfolio_committee import (
    PortfolioCommittee,
)


class ExecutiveCommitteeService:
    def vote(
        self,
        context: BrainContext,
    ) -> list[CommitteeVote]:
        return [
            PortfolioCommittee().vote(
                context,
            ),
        ]
