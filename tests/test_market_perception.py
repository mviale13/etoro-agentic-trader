from app.application.brain.perception.market_perception import (
    MarketPerception,
)


def test_market_perception_is_in_perception_layer() -> None:
    assert MarketPerception.__module__ == (
        "app.application.brain.perception.market_perception"
    )
