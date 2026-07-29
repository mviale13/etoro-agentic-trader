from app.application.brain.reasoning.opportunity_reasoner import (
    OpportunityReasoner,
)


def test_opportunity_reasoner_exists() -> None:
    assert OpportunityReasoner() is not None
