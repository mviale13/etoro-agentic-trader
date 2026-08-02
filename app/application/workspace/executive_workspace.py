"""Shared workspace for the Artificial CIO execution pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.brain.reasoning.reasoning_snapshot import (
    ReasoningSnapshot,
)
from app.application.committees.models.committee_opinion import (
    CommitteeOpinion,
)
from app.brain.brain import Brain
from app.domain.executive.executive_brief import ExecutiveBrief
from app.domain.executive_decision import DecisionEvidence, ExecutiveDecision
from app.domain.thesis import InvestmentThesis


@dataclass(slots=True)
class ExecutiveWorkspace:
    """
    Shared working context for the Artificial CIO pipeline.

    Each pipeline stage enriches this workspace.
    """

    symbol: str
    brain: Brain
    reasoning: ReasoningSnapshot | None = None
    committee_opinions: tuple[CommitteeOpinion, ...] = ()
    #: The scores the decision was actually made on.
    evidence: DecisionEvidence | None = None
    decision: ExecutiveDecision | None = None
    thesis: InvestmentThesis | None = None
    brief: ExecutiveBrief | None = None
