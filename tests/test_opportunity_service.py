from app.services.opportunity_service import OpportunityService


def test_returns_three_opportunities() -> None:
    opportunities = OpportunityService().top_opportunities()

    assert len(opportunities) == 3


def test_first_opportunity_is_microsoft() -> None:
    opportunity = OpportunityService().top_opportunities()[0]

    assert opportunity.symbol == "MSFT"
    assert opportunity.action == "BUY"
    assert opportunity.score == 92.0
