from app.application.brain.perception.investor_perception import (
    InvestorPerception,
)
from app.application.brain.perception.policy_perception import (
    PolicyPerception,
)
from app.application.brain.perception.portfolio_perception import (
    PortfolioPerception,
)
from app.application.brain.perception.recommendation_perception import (
    RecommendationPerception,
)
from app.domain.brain_context import BrainContext
from app.repositories.json_event_repository import (
    JsonEventRepository,
)
from app.services.market_context_service import MarketContextService


class BrainContextBuilder:
    async def build(self) -> BrainContext:
        repository = JsonEventRepository()

        portfolio = await PortfolioPerception().execute()

        investor = InvestorPerception(
            repository=repository,
        ).execute(
            portfolio=portfolio,
        )

        recommendation = await RecommendationPerception(
            repository=repository,
        ).execute()

        # The legacy BrainContext carries a MarketContext. The canonical
        # MarketPerception now produces a MarketSnapshot for the Brain
        # pipeline, so this legacy path keeps its own market source.
        market = MarketContextService().build()

        investment_policy = PolicyPerception().execute()

        return BrainContext(
            portfolio=portfolio,
            recommendation=recommendation,
            observation=investor.observation,
            investor_dna=investor.investor_dna,
            market=market,
            investment_policy=investment_policy,
        )
