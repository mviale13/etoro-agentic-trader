from app.domain.market_facts import (
    MarketFacts,
)
from app.domain.market_opportunity import (
    MarketOpportunity,
)
from app.domain.opportunity_facts import (
    OpportunityFacts,
)


class OpportunityFactsService:
    def build(
        self,
        opportunity: MarketOpportunity,
        market: MarketFacts,
    ) -> OpportunityFacts:
        quote = market.quote(
            opportunity.symbol,
        )

        if quote is None:
            raise ValueError(f"No market facts found for {opportunity.symbol}")

        return OpportunityFacts(
            symbol=opportunity.symbol,
            asset_type=(opportunity.asset_type),
            current_price=quote.price,
            daily_change_percent=(quote.change_percent),
            source=quote.source,
        )
