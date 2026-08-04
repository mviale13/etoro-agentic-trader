from app.application.brain.reasoning import ReasoningService
from app.brain import BrainBuilder
from tests.test_brain_context import (
    make_market,
    make_policy,
    make_portfolio,
)


def make_brain():
    return BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
    ).build()


def test_reasoning_service_runs_all_reasoners():
    service = ReasoningService()

    snapshot = service.reason(make_brain())

    assert snapshot.portfolio is not None
    assert snapshot.market is not None
    assert snapshot.risk is not None
