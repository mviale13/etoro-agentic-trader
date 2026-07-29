#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo "MOVRvest — Sprint 50.4: BrainPipeline"
echo "============================================================"

BRAIN_DIR="app/application/brain"
TEST_FILE="tests/test_brain_pipeline_architecture.py"

mkdir -p "$BRAIN_DIR"

cat > "$BRAIN_DIR/perception_stage.py" <<'PY'
"""Perception stage for the MOVRvest investment-brain pipeline."""

from app.domain.brain_context import BrainContext
from app.services.brain_context_builder import BrainContextBuilder


class PerceptionStage:
    """Gather the complete context required for one brain cycle."""

    async def execute(self) -> BrainContext:
        """Build and return the current investment context."""
        return await BrainContextBuilder().build()
PY

cat > "$BRAIN_DIR/reasoning_stage.py" <<'PY'
"""Reasoning stage for the MOVRvest investment-brain pipeline."""

from app.domain.brain_context import BrainContext
from app.domain.insight import Insight
from app.services.executive_reasoning_service import ExecutiveReasoningService


class ReasoningStage:
    """Convert perceived investment context into executive insights."""

    def execute(self, context: BrainContext) -> list[Insight]:
        """Run the current executive reasoning service."""
        return ExecutiveReasoningService().analyze(context)
PY

cat > "$BRAIN_DIR/communication_stage.py" <<'PY'
"""Communication stage for the MOVRvest investment-brain pipeline."""

from collections.abc import Sequence

from app.domain.brain_context import BrainContext
from app.domain.brain_snapshot import BrainSnapshot
from app.domain.insight import Insight
from app.services.executive_summary_service import ExecutiveSummaryService


class CommunicationStage:
    """Convert investment reasoning into a presentation-ready brain snapshot."""

    def execute(
        self,
        context: BrainContext,
        insights: Sequence[Insight],
    ) -> BrainSnapshot:
        """Build the executive communication output for one brain cycle."""
        communication_service = ExecutiveSummaryService()

        insight_list = list(insights)
        brief = communication_service.build(insight_list)
        summary = communication_service.summarize(insight_list)

        has_opportunity = any(
            insight.category.lower() == "opportunity" for insight in insight_list
        )

        has_deployable_cash = False

        if context.investment_policy is not None:
            policy_cash_target = context.investment_policy.target.cash
            current_cash = context.portfolio.allocation.cash
            has_deployable_cash = current_cash > policy_cash_target + 5

        executive_focus = (
            "opportunities" if has_deployable_cash and has_opportunity else "portfolio"
        )

        return BrainSnapshot(
            portfolio=context.portfolio,
            recommendation=context.recommendation,
            observation=context.observation,
            investor_dna=context.investor_dna,
            summary=summary,
            insights=insight_list,
            focus=executive_focus,
            brief=brief,
        )
PY

cat > "$BRAIN_DIR/brain_pipeline.py" <<'PY'
"""Execution pipeline for MOVRvest investment intelligence."""

from app.application.brain.communication_stage import CommunicationStage
from app.application.brain.perception_stage import PerceptionStage
from app.application.brain.reasoning_stage import ReasoningStage
from app.domain.brain_snapshot import BrainSnapshot


class BrainPipeline:
    """Execute perception, reasoning, and communication in sequence."""

    def __init__(
        self,
        perception: PerceptionStage | None = None,
        reasoning: ReasoningStage | None = None,
        communication: CommunicationStage | None = None,
    ) -> None:
        self._perception = perception or PerceptionStage()
        self._reasoning = reasoning or ReasoningStage()
        self._communication = communication or CommunicationStage()

    async def run(self) -> BrainSnapshot:
        """Run one complete MOVRvest investment-intelligence pipeline."""
        context = await self._perception.execute()
        insights = self._reasoning.execute(context)

        return self._communication.execute(
            context=context,
            insights=insights,
        )
PY

cat > "$BRAIN_DIR/investment_brain.py" <<'PY'
"""Central application entry point for MOVRvest investment intelligence."""

from app.application.brain.brain_pipeline import BrainPipeline
from app.domain.brain_snapshot import BrainSnapshot


class InvestmentBrain:
    """Expose the MOVRvest investment brain to presentation-layer callers.

    Execution details belong to ``BrainPipeline``. This class remains the
    stable application entry point consumed by APIs and other presentation
    adapters.
    """

    def __init__(self, pipeline: BrainPipeline | None = None) -> None:
        self._pipeline = pipeline or BrainPipeline()

    async def analyze(self) -> BrainSnapshot:
        """Run one complete MOVRvest investment-intelligence cycle."""
        return await self._pipeline.run()

    async def build(self) -> BrainSnapshot:
        """Compatibility verb for callers that still use ``build``."""
        return await self.analyze()
PY

cat > "$BRAIN_DIR/__init__.py" <<'PY'
"""MOVRvest investment-brain application orchestration."""

from app.application.brain.brain_pipeline import BrainPipeline
from app.application.brain.communication_stage import CommunicationStage
from app.application.brain.investment_brain import InvestmentBrain
from app.application.brain.perception_stage import PerceptionStage
from app.application.brain.reasoning_stage import ReasoningStage

__all__ = [
    "BrainPipeline",
    "CommunicationStage",
    "InvestmentBrain",
    "PerceptionStage",
    "ReasoningStage",
]
PY

cat > "$TEST_FILE" <<'PY'
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
    expected = cast(BrainSnapshot, object())

    class PipelineStub:
        async def run(self) -> BrainSnapshot:
            return expected

    brain = InvestmentBrain(pipeline=cast(BrainPipeline, PipelineStub()))

    assert await brain.analyze() is expected


@pytest.mark.anyio
async def test_pipeline_executes_stages_in_order() -> None:
    calls: list[str] = []

    context = cast(BrainContext, object())
    insights = cast(list[Insight], [])
    snapshot = cast(BrainSnapshot, object())

    class PerceptionStub:
        async def execute(self) -> BrainContext:
            calls.append("perception")
            return context

    class ReasoningStub:
        def execute(self, received_context: BrainContext) -> list[Insight]:
            calls.append("reasoning")
            assert received_context is context
            return insights

    class CommunicationStub:
        def execute(
            self,
            received_context: BrainContext,
            received_insights: list[Insight],
        ) -> BrainSnapshot:
            calls.append("communication")
            assert received_context is context
            assert received_insights is insights
            return snapshot

    pipeline = BrainPipeline(
        perception=cast(PerceptionStage, PerceptionStub()),
        reasoning=cast(ReasoningStage, ReasoningStub()),
        communication=cast(CommunicationStage, CommunicationStub()),
    )

    result = await pipeline.run()

    assert result is snapshot
    assert calls == ["perception", "reasoning", "communication"]
PY

echo
echo "Files created:"
echo "  $BRAIN_DIR/brain_pipeline.py"
echo "  $BRAIN_DIR/perception_stage.py"
echo "  $BRAIN_DIR/reasoning_stage.py"
echo "  $BRAIN_DIR/communication_stage.py"
echo "  $BRAIN_DIR/investment_brain.py"
echo "  $BRAIN_DIR/__init__.py"
echo "  $TEST_FILE"

echo
echo "Running formatting and checks..."

ruff check --fix "$BRAIN_DIR" "$TEST_FILE"
ruff format "$BRAIN_DIR" "$TEST_FILE"
ruff check "$BRAIN_DIR" "$TEST_FILE"
mypy "$BRAIN_DIR" "$TEST_FILE"
pytest

echo
echo "============================================================"
echo "✅ Sprint 50.4 complete"
echo "============================================================"
echo
echo "Architecture:"
echo "InvestmentBrain"
echo "    -> BrainPipeline"
echo "        -> PerceptionStage"
echo "        -> ReasoningStage"
echo "        -> CommunicationStage"
echo "            -> BrainSnapshot"
echo
echo "Suggested commit:"
echo "git add app/application/brain tests/test_brain_pipeline_architecture.py"
echo 'git commit -m "refactor: introduce investment brain pipeline"'
