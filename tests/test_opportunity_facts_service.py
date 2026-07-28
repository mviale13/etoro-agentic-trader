from datetime import UTC, datetime

from app.domain.market_facts import (
    MarketFact,
    MarketFacts,
)
from app.domain.market_opportunity import (
    MarketOpportunity,
)
from app.services.facts.opportunity_facts_service import (
    OpportunityFactsService,
)

NOW = datetime.now(
    UTC,
)


def test_builds_opportunity_facts() -> None:
    market = MarketFacts(
        instruments=(
            MarketFact(
                symbol="BTC",
                name="Bitcoin",
                price=118500.0,
                change_percent=2.35,
                source="Yahoo",
                as_of=NOW,
            ),
        ),
        vix=15,
        source="Yahoo",
        as_of=NOW,
    )

    opportunity = MarketOpportunity(
        symbol="BTC",
        asset_type="crypto",
        source="Scanner",
    )

    facts = OpportunityFactsService().build(
        opportunity,
        market,
    )

    assert facts.symbol == "BTC"
    assert facts.asset_type == "crypto"
    assert facts.current_price == 118500.0
    assert facts.daily_change_percent == 2.35
