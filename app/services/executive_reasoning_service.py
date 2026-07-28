from app.domain.brain_context import BrainContext
from app.domain.insight import Insight
from app.services.executive_committee_service import (
    ExecutiveCommitteeService,
)


class ExecutiveReasoningService:
    def analyze(
        self,
        context: BrainContext,
    ) -> list[Insight]:
        # Collect committee votes.
        #
        # The InvestmentCaseBuilder will later transform these
        # votes into executive insights.
        ExecutiveCommitteeService().vote(
            context,
        )

        return []
