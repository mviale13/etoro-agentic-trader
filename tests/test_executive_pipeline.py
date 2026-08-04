"""One cycle reasons the account once, and every holding shares that view."""

from __future__ import annotations

from app.application.brain.reasoning import ReasoningService
from app.application.brain.reasoning.reasoning_snapshot import ReasoningSnapshot
from app.application.workspace.executive_pipeline import ExecutivePipeline
from app.brain import Brain, BrainBuilder
from tests.test_brain_context import make_market, make_policy, make_portfolio


def make_brain() -> Brain:
    return BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
    ).build()


class CountingReasoning:
    """The real reasoning, counting how often the account is reasoned."""

    def __init__(self) -> None:
        self._inner = ReasoningService()
        self.calls = 0

    def reason(self, brain: Brain) -> ReasoningSnapshot:
        self.calls += 1
        return self._inner.reason(brain)


def test_the_account_is_reasoned_once_for_the_whole_cycle() -> None:
    spy = CountingReasoning()
    pipeline = ExecutivePipeline(reasoning=spy)  # type: ignore[arg-type]

    workspaces = pipeline.execute_all(["AAPL", "MSFT", "NVDA"], make_brain())

    assert len(workspaces) == 3
    # Three holdings, one view of the account — not three.
    assert spy.calls == 1


def test_every_holding_shares_the_one_reasoning_object() -> None:
    """ "Exactly the same view" is the same object, not three that agree."""

    pipeline = ExecutivePipeline()

    workspaces = pipeline.execute_all(["AAPL", "MSFT"], make_brain())

    assert workspaces[0].reasoning is workspaces[1].reasoning


def test_a_single_security_still_reasons_on_its_own() -> None:
    spy = CountingReasoning()
    pipeline = ExecutivePipeline(reasoning=spy)  # type: ignore[arg-type]

    workspace = pipeline.execute(symbol="AAPL", brain=make_brain())

    assert workspace.reasoning is not None
    assert spy.calls == 1
