"""Canonical composition root for the Artificial CIO Brain."""

from collections.abc import Sequence

from app.application.brain.perception.market_perception import (
    MarketPerception,
)
from app.application.brain.perception.memory_perception import (
    MemoryPerception,
)
from app.application.brain.perception.opportunity_perception import (
    OpportunityPerception,
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
        opportunity_perception: OpportunityPerception | None = None,
        candidate_limit: int = 0,
    ) -> None:
        self._security_perception = security_perception or SecurityPerception()
        self._memory_perception = memory_perception or MemoryPerception(
            repository=JsonEventRepository(),
        )
        self._opportunity_perception = opportunity_perception or OpportunityPerception()

        # Evidencing a candidate costs a fundamentals request against a
        # rate-limited provider, so a cycle that will not research candidates
        # does not pay for them. Research asks for a budget explicitly.
        self._candidate_limit = candidate_limit

    async def build(
        self,
        focus_symbols: Sequence[str] = (),
    ) -> Brain:
        """
        Assemble the Brain, evidencing anything the caller names.

        A caller that asks about one symbol needs that symbol evidenced.
        Without it the Artificial CIO judged the security on portfolio and
        market context alone, and reached a different verdict from the one
        the research pipeline reached about the same ticker.
        """

        portfolio = await PortfolioPerception().execute()
        market = await MarketPerception().execute()
        investment_policy = PolicyPerception().execute()

        if investment_policy is None:
            raise ValueError(
                "No investment policy is configured. "
                "The Artificial CIO cannot reason without one."
            )

        candidates = await self._opportunity_perception.execute(portfolio)

        evidence = await self._security_perception.execute(
            portfolio,
            candidates=candidates,
            candidate_limit=self._candidate_limit,
            focus_symbols=focus_symbols,
        )

        decision_history = self._memory_perception.execute()

        return BrainBuilder(
            portfolio=portfolio,
            market=market,
            investment_policy=investment_policy,
            evidence=evidence,
            candidates=candidates,
            decision_history=decision_history,
        ).build()
