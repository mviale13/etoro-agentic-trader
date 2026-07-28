from app.domain.opportunity_facts import OpportunityFacts
from app.services.committees.opportunity_committee import (
    OpportunityCommittee,
)


def test_votes_buy_for_strong_crypto() -> None:
    facts = OpportunityFacts(
        symbol="BTC",
        asset_type="crypto",
        current_price=120000,
        daily_change_percent=3.1,
        source="Yahoo",
    )

    vote = OpportunityCommittee().vote(
        facts,
    )

    assert vote.recommendation == "BUY"
    assert vote.confidence >= 70


def test_votes_hold_for_flat_stock() -> None:
    facts = OpportunityFacts(
        symbol="MSFT",
        asset_type="stock",
        current_price=620,
        daily_change_percent=0.4,
        source="Yahoo",
    )

    vote = OpportunityCommittee().vote(
        facts,
    )

    assert vote.recommendation == "HOLD"
