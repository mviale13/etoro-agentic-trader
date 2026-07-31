"""Canonical composition root for the Artificial CIO Brain."""

from app.application.brain.perception.market_perception import (
    MarketPerception,
)
from app.application.brain.perception.policy_perception import (
    PolicyPerception,
)
from app.application.brain.perception.portfolio_perception import (
    PortfolioPerception,
)
from app.brain.brain import Brain
from app.brain.brain_builder import BrainBuilder


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

    async def build(self) -> Brain:
        portfolio = await PortfolioPerception().execute()
        market = await MarketPerception().execute()
        investment_policy = PolicyPerception().execute()

        if investment_policy is None:
            raise ValueError(
                "No investment policy is configured. "
                "The Artificial CIO cannot reason without one."
            )

        return BrainBuilder(
            portfolio=portfolio,
            market=market,
            investment_policy=investment_policy,
        ).build()
