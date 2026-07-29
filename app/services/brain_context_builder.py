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
from app.services.investor_dna_service import (
    InvestorDNAService,
)
from app.services.investor_observation_service import (
    InvestorObservationService,
)
from app.services.investor_strategy_service import (
    InvestorStrategyService,
)
from app.services.market_context_service import (
    MarketContextService,
)
from app.services.memory_service import MemoryService
from app.services.pattern_engine import PatternEngine
from app.services.signal_service import SignalService


class BrainContextBuilder:
    async def build(self) -> BrainContext:
        repository = JsonEventRepository()

        portfolio = await PortfolioPerception().execute()

        signals = SignalService().analyze(
            current=portfolio,
            previous=None,
        )

        observation = InvestorObservationService().observe(
            signals,
        )

        memories = MemoryService(
            repository,
        ).history()

        patterns = PatternEngine().analyze(
            memories,
        )

        investor_dna = InvestorDNAService().analyze(
            patterns,
        )

        recommendation = await CommitteeService(
            repository,
        ).evaluate()

        market = MarketContextService().build()

        investment_policy = InvestorStrategyService().load_policy()

        return BrainContext(
            portfolio=portfolio,
            recommendation=recommendation,
            observation=observation,
            investor_dna=investor_dna,
            market=market,
            investment_policy=investment_policy,
        )
