from app.domain.brain_context import BrainContext
from app.domain.committee_vote import CommitteeVote
from app.domain.executive_board_decision import ExecutiveBoardDecision
from app.domain.market_facts import MarketFacts
from app.domain.market_opportunity import MarketOpportunity
from app.domain.portfolio_facts import PortfolioFacts
from app.services.committees.market_committee import (
    MarketCommittee,
)
from app.services.committees.opportunity_committee import (
    OpportunityCommittee,
)
from app.services.committees.policy_committee import (
    PolicyCommittee,
)
from app.services.committees.portfolio_committee import (
    PortfolioCommittee,
)
from app.services.committees.risk_committee import (
    RiskCommittee,
)
from app.services.executive_board_service import (
    ExecutiveBoardService,
)
from app.services.facts.opportunity_facts_service import (
    OpportunityFactsService,
)
from app.services.policy_assessment_service import (
    PolicyAssessmentService,
)
from app.services.risk_assessment_service import (
    RiskAssessmentService,
)


class ExecutiveMeetingService:
    def analyze(
        self,
        *,
        opportunity: MarketOpportunity,
        context: BrainContext,
        portfolio_facts: PortfolioFacts,
        market_facts: MarketFacts,
        proposed_position_pct: float,
    ) -> ExecutiveBoardDecision:
        policy = context.investment_policy

        if policy is None:
            raise ValueError("Investment Policy is required for an Executive Meeting.")

        opportunity_facts = OpportunityFactsService().build(
            opportunity,
            market_facts,
        )

        risk_assessment = RiskAssessmentService().assess(
            portfolio_facts,
            market_facts,
        )

        policy_assessment = PolicyAssessmentService().assess(
            policy,
            opportunity_facts,
            proposed_position_pct=(proposed_position_pct),
            current_crypto_pct=(context.portfolio.allocation.crypto),
        )

        votes: tuple[CommitteeVote, ...] = (
            PortfolioCommittee().vote(
                context,
            ),
            MarketCommittee().vote(
                market_facts,
            ),
            OpportunityCommittee().vote(
                opportunity_facts,
            ),
            RiskCommittee().vote(
                risk_assessment,
            ),
            PolicyCommittee().vote(
                policy_assessment,
            ),
        )

        return ExecutiveBoardService().decide(
            votes,
        )
