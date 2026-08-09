"""Complete output of the MOVRvest executive pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.brain.reasoning.reasoning_snapshot import (
    ReasoningSnapshot,
)
from app.domain.committee.opinion import (
    CommitteeOpinion,
)
from app.domain.executive_decision import ExecutiveDecision
from app.domain.thesis.investment_thesis import InvestmentThesis


@dataclass(frozen=True, slots=True)
class ExecutiveEvaluation:
    """
    Complete explainable result of an Artificial CIO evaluation.

    This object keeps the final decision together with the reasoning,
    committee opinions and durable investment thesis that produced it.
    """

    decision: ExecutiveDecision

    thesis: InvestmentThesis

    reasoning: ReasoningSnapshot

    committee_opinions: tuple[CommitteeOpinion, ...]
