from app.application.brain.reasoning.market_analyst import MarketAnalyst


def test_market_analyst_exists() -> None:
    assert MarketAnalyst() is not None
