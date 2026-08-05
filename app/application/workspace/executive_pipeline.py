"""Artificial CIO execution pipeline."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from app.application.brain.reasoning import ReasoningService
from app.application.brain.reasoning.reasoning_snapshot import (
    ReasoningSnapshot,
)
from app.application.brief.executive_brief_builder import (
    ExecutiveBriefBuilder,
)
from app.application.committees.committee_service import CommitteeService
from app.application.executive.decision_evidence_builder import (
    DecisionEvidenceBuilder,
)
from app.application.executive.executive_action_builder import (
    ExecutiveActionBuilder,
)
from app.application.executive.executive_evaluation import (
    ExecutiveEvaluation,
)
from app.application.learning.decision_journal import DecisionJournal
from app.application.thesis.investment_thesis_builder import (
    InvestmentThesisBuilder,
)
from app.brain import Brain
from app.cio.artificial_cio import ExecutiveDecisionEngine
from app.repositories.json_event_repository import JsonEventRepository

from .executive_workspace import ExecutiveWorkspace


@dataclass(slots=True)
class ExecutivePipeline:
    """Execute the complete Artificial CIO pipeline."""

    reasoning: ReasoningService = field(
        default_factory=ReasoningService,
    )

    committees: CommitteeService = field(
        default_factory=CommitteeService,
    )

    evidence_builder: DecisionEvidenceBuilder = field(
        default_factory=DecisionEvidenceBuilder,
    )

    decision_engine: ExecutiveDecisionEngine = field(
        default_factory=ExecutiveDecisionEngine,
    )

    thesis_builder: InvestmentThesisBuilder = field(
        default_factory=InvestmentThesisBuilder,
    )

    action_builder: ExecutiveActionBuilder = field(
        default_factory=ExecutiveActionBuilder,
    )

    brief_builder: ExecutiveBriefBuilder = field(
        default_factory=ExecutiveBriefBuilder,
    )

    #: Where decisions are remembered. None runs the pipeline without
    #: memory, which is what a test or a what-if evaluation wants: nothing
    #: the investor never saw should enter the record.
    journal: DecisionJournal | None = None

    @classmethod
    def with_memory(cls) -> ExecutivePipeline:
        """Build the pipeline that remembers what it decided."""

        return cls(
            journal=DecisionJournal(
                repository=JsonEventRepository(),
            ),
        )

    def execute_all(
        self,
        symbols: Sequence[str],
        brain: Brain,
    ) -> tuple[ExecutiveWorkspace, ...]:
        """
        Evaluate several securities against one Brain.

        Every security is judged against exactly the same view of reality,
        which is what makes their convictions comparable.

        The portfolio, the market and the account's risk do not depend on
        which security is being judged, so that view is reasoned once and
        shared across the cycle. Reasoning it per holding repeated three
        analyst passes for every name, and it let "exactly the same view"
        rest on the assessments coming out identical rather than on their
        being the one object they are here.
        """

        reasoning = self.reasoning.reason(brain)

        return tuple(
            self.execute(
                symbol=symbol,
                brain=brain,
                reasoning=reasoning,
            )
            for symbol in symbols
        )

    def execute(
        self,
        symbol: str,
        brain: Brain,
        reasoning: ReasoningSnapshot | None = None,
    ) -> ExecutiveWorkspace:

        workspace = ExecutiveWorkspace(
            symbol=symbol,
            brain=brain,
        )

        # Shared by `execute_all` across the cycle; computed here for a
        # caller judging a single security on its own.
        workspace.reasoning = (
            reasoning if reasoning is not None else self.reasoning.reason(brain)
        )

        workspace.committee_opinions = self.committees.review(
            brain,
            workspace.reasoning,
            symbol,
        )

        workspace.evidence = self.evidence_builder.build(
            symbol,
            brain,
            workspace.reasoning,
            workspace.committee_opinions,
        )

        workspace.decision = self.decision_engine.decide(
            workspace.evidence,
        )

        # The Brain perceived this history before the cycle began, so the
        # thesis compares today's decision against what came before it.
        workspace.thesis = self.thesis_builder.build(
            symbol=symbol,
            reasoning=workspace.reasoning,
            committee_opinions=workspace.committee_opinions,
            decision=workspace.decision,
            history=brain.decision_history_for(symbol),
            # The scores today's decision was made on, so the thesis can
            # say what moved since the last one — not merely that it did.
            evidence=workspace.evidence,
        )

        # What to consider doing about it. Not the decision restated: a
        # RECOMMEND on something already held asks a different question
        # from a RECOMMEND on something the investor does not own, and
        # only the portfolio knows which this is.
        workspace.action = self.action_builder.build(
            decision=workspace.decision,
            held=any(
                holding.symbol.upper().strip() == symbol.upper().strip()
                for holding in brain.portfolio.holdings
            ),
            catalysts=workspace.thesis.catalysts,
        )

        if self.journal is not None:
            # Recorded with its scores: a later cycle can only explain a
            # conviction move if this one wrote down what it moved from.
            self.journal.record(workspace.decision, workspace.evidence)

        workspace.brief = self.brief_builder.build(
            workspace,
        )

        return workspace

    def evaluate(
        self,
        symbol: str,
        brain: Brain,
    ) -> ExecutiveEvaluation:

        workspace = self.execute(
            symbol=symbol,
            brain=brain,
        )

        assert workspace.reasoning is not None
        assert workspace.decision is not None
        assert workspace.thesis is not None

        reasoning = workspace.reasoning
        decision = workspace.decision
        thesis = workspace.thesis

        return ExecutiveEvaluation(
            decision=decision,
            thesis=thesis,
            reasoning=reasoning,
            committee_opinions=workspace.committee_opinions,
        )
