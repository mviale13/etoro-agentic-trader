"""Shared workspace for the Artificial CIO execution pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.brain.reasoning.reasoning_snapshot import (
    ReasoningSnapshot,
)
from app.brain.brain import Brain
from app.domain.business_quality import BusinessQuality
from app.domain.committee.opinion import CommitteeOpinion
from app.domain.executive.executive_action import ExecutiveAction
from app.domain.executive.executive_brief import ExecutiveBrief
from app.domain.executive_decision import DecisionEvidence, ExecutiveDecision
from app.domain.finding import FindingLedger
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

    #: Every finding read about this security, addressable. Gathered
    #: before the committees so their opinions can reference it.
    findings: FindingLedger = FindingLedger()

    committee_opinions: tuple[CommitteeOpinion, ...] = ()

    #: What the filing establishes about business quality, where the
    #: statements reached quorum. None where they did not.
    quality: BusinessQuality | None = None
    #: The scores the decision was actually made on.
    evidence: DecisionEvidence | None = None
    decision: ExecutiveDecision | None = None
    thesis: InvestmentThesis | None = None

    #: What the Artificial CIO is asking the investor to consider about
    #: this security — which the decision state alone cannot say, because
    #: it does not know whether the security is already held.
    action: ExecutiveAction | None = None

    brief: ExecutiveBrief | None = None
