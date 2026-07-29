from app.application.brain.perception.investor_perception import (
    InvestorPerception,
)
from app.application.brain.perception.portfolio_perception import (
    PortfolioPerception,
)
from app.domain.brain_context import BrainContext
from app.repositories.json_event_repository import (
    JsonEventRepository,
)
from app.services.committee_service import (
    CommitteeService,
)
from app.services.investor_strategy_service import (
    InvestorStrategyService,
)
from app.services.market_context_service import (
    MarketContextService,
)


class BrainContextBuilder:
    async def build(self) -> BrainContext:
        repository = JsonEventRepository()

        portfolio = await PortfolioPerception().execute()

        investor = InvestorPerception(
            repository=repository,
        ).execute(
            portfolio=portfolio,
        )

        recommendation = await CommitteeService(
            repository,
        ).evaluate()

        market = MarketContextService().build()

        investment_policy = InvestorStrategyService().load_policy()

        return BrainContext(
            portfolio=portfolio,
            recommendation=recommendation,
            observation=investor.observation,
            investor_dna=investor.investor_dna,
            market=market,
            investment_policy=investment_policy,
        )
