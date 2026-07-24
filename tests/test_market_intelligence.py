from app.domain.market_intelligence import MarketIntelligence


def test_market_intelligence_is_immutable():
    intelligence = MarketIntelligence(
        market_mood="positive",
        volatility="low",
        fear_greed=70,
        vix=14.2,
        treasury_10y=4.1,
        gold_change=0.3,
        oil_change=-0.2,
        dollar_index=102.1,
        summary="Markets remain constructive.",
    )

    assert intelligence.market_mood == "positive"
    assert intelligence.fear_greed == 70
