"""Market perception component."""

from app.domain.market_context import MarketContext
from app.services.market_context_service import MarketContextService


class MarketPerception:
    """Produces the current market context."""

    def __init__(
        self,
        market_service: MarketContextService | None = None,
    ) -> None:
        self._market_service = market_service or MarketContextService()

    def execute(self) -> MarketContext:
        return self._market_service.build()
