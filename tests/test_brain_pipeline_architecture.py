"""Architecture tests for the MOVRvest BrainPipeline."""

import inspect
from typing import cast

import pytest

from app.application.brain import (
    BrainPipeline,
    CommunicationStage,
    InvestmentBrain,
    PerceptionStage,
    ReasoningStage,
)
from app.domain.brain_context import BrainContext
from app.domain.brain_snapshot import BrainSnapshot
from app.domain.insight import Insight


def test_brain_pipeline_is_defined_in_application_layer() -> None:
    assert BrainPipeline.__module__ == "app.application.brain.brain_pipeline"


def test_pipeline_stages_are_defined_in_application_layer() -> None:
    assert PerceptionStage.__module__ == "app.application.brain.perception_stage"
    assert ReasoningStage.__module__ == "app.application.brain.reasoning_stage"
    assert CommunicationStage.__module__ == (
        "app.application.brain.communication_stage"
    )


def test_brain_pipeline_run_is_async() -> None:
    assert inspect.iscoroutinefunction(BrainPipeline.run)


def test_investment_brain_analyze_remains_async() -> None:
    assert inspect.iscoroutinefunction(InvestmentBrain.analyze)


@pytest.mark.anyio
async def test_investment_brain_delegates_to_pipeline() -> None:
    expected_snapshot = cast(BrainSnapshot, object())

    class PipelineStub:
        async def run(self) -> BrainSnapshot:
            return expected_snapshot

    brain = InvestmentBrain(
        pipeline=cast(BrainPipeline, PipelineStub()),
    )

    assert await brain.analyze() is expected_snapshot


@pytest.mark.anyio
async def test_pipeline_executes_stages_in_order() -> None:
    calls: list[str] = []

    expected_context = cast(BrainContext, object())
    expected_insights = cast(list[Insight], [])
    expected_snapshot = cast(BrainSnapshot, object())

    class PerceptionStub:
        async def execute(self) -> BrainContext:
            calls.append("perception")
            return expected_context

    class ReasoningStub:
        def execute(self, context: BrainContext) -> list[Insight]:
            calls.append("reasoning")
            assert context is expected_context
            return expected_insights

    class CommunicationStub:
        def execute(
            self,
            context: BrainContext,
            insights: list[Insight],
        ) -> BrainSnapshot:
            calls.append("communication")
            assert context is expected_context
            assert insights is expected_insights
            return expected_snapshot

    pipeline = BrainPipeline(
        perception=cast(PerceptionStage, PerceptionStub()),
        reasoning=cast(ReasoningStage, ReasoningStub()),
        communication=cast(CommunicationStage, CommunicationStub()),
    )

    result = await pipeline.run()

    assert result is expected_snapshot
    assert calls == [
        "perception",
        "reasoning",
        "communication",
    ]
