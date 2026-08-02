"""Canonical composition root for the Artificial CIO Brain."""

from app.application.brain.perception.market_perception import (
    MarketPerception,
)
from app.application.brain.perception.memory_perception import (
    MemoryPerception,
)
from app.application.brain.perception.policy_perception import (
    PolicyPerception,
)
from app.application.brain.perception.portfolio_perception import (
    PortfolioPerception,
)
from app.application.brain.perception.security_perception import (
    SecurityPerception,
)
from app.brain.brain import Brain
from app.brain.brain_builder import BrainBuilder
from app.repositories.json_event_repository import JsonEventRepository


class BrainBuilderService:
    """
    Assemble the canonical immutable Brain from resolved perceptions.

    This service performs composition only.

    It does not:
    - execute reasoning
    - run committees
    - create recommendations
    - make investment decisions
    - render communication outputs
    """

    def __init__(
        self,
        security_perception: SecurityPerception | None = None,
        memory_perception: MemoryPerception | None = None,
    ) -> None:
        self._security_perception = security_perception or SecurityPerception()
        self._memory_perception = memory_perception or MemoryPerception(
            repository=JsonEventRepository(),
        )

    async def build(self) -> Brain:
        portfolio = await PortfolioPerception().execute()
        market = await MarketPerception().execute()
        investment_policy = PolicyPerception().execute()

        if investment_policy is None:
            raise ValueError(
                "No investment policy is configured. "
                "The Artificial CIO cannot reason without one."
            )

        evidence = await self._security_perception.execute(portfolio)
        decision_history = self._memory_perception.execute()

        return BrainBuilder(
            portfolio=portfolio,
            market=market,
            investment_policy=investment_policy,
            evidence=evidence,
            decision_history=decision_history,
        ).build()
