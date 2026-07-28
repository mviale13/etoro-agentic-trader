from app.domain.market_opportunity import (
    MarketOpportunity,
)


class OpportunityDiscoveryService:
    def discover(
        self,
    ) -> tuple[
        MarketOpportunity,
        ...,
    ]:
        return (
            MarketOpportunity(
                symbol="BTC",
                asset_type="crypto",
                source="Universe",
            ),
            MarketOpportunity(
                symbol="ETH",
                asset_type="crypto",
                source="Universe",
            ),
            MarketOpportunity(
                symbol="SPY",
                asset_type="etf",
                source="Universe",
            ),
            MarketOpportunity(
                symbol="QQQ",
                asset_type="etf",
                source="Universe",
            ),
            MarketOpportunity(
                symbol="NVDA",
                asset_type="stock",
                source="Universe",
            ),
            MarketOpportunity(
                symbol="MSFT",
                asset_type="stock",
                source="Universe",
            ),
            MarketOpportunity(
                symbol="GOOG",
                asset_type="stock",
                source="Universe",
            ),
            MarketOpportunity(
                symbol="AAPL",
                asset_type="stock",
                source="Universe",
            ),
        )
