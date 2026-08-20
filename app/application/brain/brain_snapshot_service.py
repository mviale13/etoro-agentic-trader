"""Compose the factual brain snapshot served to the dashboard."""

from __future__ import annotations

from app.application.brain.brain_builder_service import BrainBuilderService
from app.application.brain.perception.investor_perception import (
    InvestorPerception,
)
from app.application.brain.perception.recommendation_perception import (
    RecommendationPerception,
)
from app.application.brain.reasoning.capacity_analyst import CapacityAnalyst
from app.application.brain.reasoning.risk_analyst import RiskAnalyst
from app.domain.brain_snapshot import BrainSnapshot
from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.repositories.json_event_repository import JsonEventRepository


class BrainSnapshotService:
    """
    Assemble what is currently true about the investor.

    This service answers "what do we know?" and nothing more. Investment
    judgement belongs to the Artificial CIO and is served separately, because
    evaluating every holding is far too slow to sit behind a page load.
    """

    def __init__(
        self,
        brain_builder: BrainBuilderService | None = None,
    ) -> None:
        self._brain_builder = brain_builder or BrainBuilderService()

    async def build(self) -> BrainSnapshot:
        repository = JsonEventRepository()

        brain = await self._brain_builder.build()

        investor = InvestorPerception(
            repository=repository,
        ).execute(
            portfolio=brain.portfolio,
        )

        recommendation = await RecommendationPerception(
            repository=repository,
        ).execute()

        return BrainSnapshot(
            portfolio=brain.portfolio,
            recommendation=recommendation,
            observation=investor.observation,
            investor_dna=investor.investor_dna,
            summary=self._summary(brain.portfolio),
            insights=[],
            focus="portfolio",
            # Cheap enough to belong here: the risk analyst reads the
            # portfolio and market the Brain already holds and makes no
            # request of its own. It is the per-holding evaluation behind
            # the executive brief that is too slow for a page load, not
            # reasoning as such.
            risk=RiskAnalyst().assess(brain),
            # Same reasoning: capacity compares two figures the Brain
            # already holds — the broker's allocation and the investor's
            # policy — and makes no request of its own.
            capacity=CapacityAnalyst().assess(brain),
            # The executive brief is produced by the Artificial CIO and served
            # from /executive/portfolio. Reporting a placeholder here would
            # put words in the CIO's mouth.
            brief=None,
        )

    @staticmethod
    def _summary(
        portfolio: PortfolioSnapshot,
    ) -> str:
        """State what the portfolio is, without interpreting it."""

        positions = (
            "1 position"
            if portfolio.positions == 1
            else f"{portfolio.positions} positions"
        )

        # The cash half of this sentence is dropped entirely rather than
        # printed as $0 — a sentence saying an account holds no cash is a
        # claim, and this one would be made out of an absent reading.
        if portfolio.available_cash_usd is None or portfolio.liquidity_pct is None:
            return (
                f"{positions} worth "
                f"${portfolio.invested_usd:,.0f}. "
                "Available cash could not be read."
            )

        return (
            f"{positions} worth "
            f"${portfolio.invested_usd:,.0f}, "
            f"with ${portfolio.available_cash_usd:,.0f} in cash "
            f"({portfolio.liquidity_pct:.0f}% of the account)."
        )
