"""Top-level Artificial CIO orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.application.brain.reasoning import ReasoningService
from app.application.committees.committee_service import (
    CommitteeService,
)
from app.application.executive.decision_evidence_builder import (
    DecisionEvidenceBuilder,
)
from app.application.executive.executive_evaluation import (
    ExecutiveEvaluation,
)
from app.application.thesis.investment_thesis_builder import (
    InvestmentThesisBuilder,
)
from app.brain import Brain
from app.domain.executive_decision import ExecutiveDecision
from app.reasoning.executive_decision_engine import (
    ExecutiveDecisionEngine,
)


@dataclass(slots=True)
class ExecutiveService:
    """Run the complete MOVRvest executive decision pipeline."""

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

    def decide(
        self,
        symbol: str,
        brain: Brain,
    ) -> ExecutiveDecision:
        """
        Produce the final executive decision.

        Kept for backward compatibility with existing callers.
        """

        return self.evaluate(
            symbol=symbol,
            brain=brain,
        ).decision

    def evaluate(
        self,
        symbol: str,
        brain: Brain,
    ) -> ExecutiveEvaluation:
        """
        Produce a complete explainable executive evaluation.

        Pipeline:

        Brain
            -> ReasoningSnapshot
            -> CommitteeOpinion
            -> DecisionEvidence
            -> ExecutiveDecision
            -> InvestmentThesis
            -> ExecutiveEvaluation
        """

        reasoning = self.reasoning.reason(brain)

        committee_opinions = self.committees.review(
            brain,
            reasoning,
        )

        evidence = self.evidence_builder.build(
            symbol,
            brain,
            reasoning,
            committee_opinions,
        )

        decision = self.decision_engine.decide(
            evidence,
        )

        thesis = self.thesis_builder.build(
            symbol=symbol,
            reasoning=reasoning,
            committee_opinions=committee_opinions,
            decision=decision,
        )

        return ExecutiveEvaluation(
            decision=decision,
            thesis=thesis,
            reasoning=reasoning,
            committee_opinions=committee_opinions,
        )
