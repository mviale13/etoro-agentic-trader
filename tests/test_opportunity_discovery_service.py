from app.services.opportunity_discovery_service import (
    OpportunityDiscoveryService,
)


def test_returns_market_universe() -> None:
    opportunities = OpportunityDiscoveryService().discover()

    assert len(opportunities) >= 8

    symbols = {item.symbol for item in opportunities}

    assert "BTC" in symbols
    assert "MSFT" in symbols
    assert "SPY" in symbols
