from dataclasses import dataclass

from app.brain import Brain, BrainBuilder
from app.reasoning.reasoning_pipeline import ReasoningPipeline
from tests.test_brain_context import (
    make_market,
    make_policy,
    make_portfolio,
)


@dataclass(slots=True)
class DummyReasoner:
    called: bool = False

    def reason(
        self,
        brain: Brain,
    ) -> Brain:
        self.called = True
        return brain


def make_brain() -> Brain:
    return BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
    ).build()


def test_pipeline_runs_every_reasoner() -> None:
    first = DummyReasoner()
    second = DummyReasoner()

    pipeline = ReasoningPipeline(
        reasoners=(first, second),
    )

    brain = make_brain()

    result = pipeline.run(brain)

    assert first.called
    assert second.called
    assert result is brain


def test_empty_pipeline_returns_same_brain() -> None:
    pipeline = ReasoningPipeline(reasoners=())

    brain = make_brain()

    assert pipeline.run(brain) is brain
