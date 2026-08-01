from app.application.brain.reasoning.opportunity_analyst import (
    OpportunityAnalyst,
)


def test_opportunity_analyst_exists() -> None:
    assert OpportunityAnalyst() is not None
